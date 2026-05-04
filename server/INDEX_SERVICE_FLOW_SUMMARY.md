# Index Service Flow Summary

**File:** `server/services/index_service.py`

---

## Overview

`index_service` is responsible for loading all recipe data from CSV into memory and building the data structures used by `search_service` for search and autocomplete.

---

## Data Structures

### `Recipe` (frozen dataclass)
Normalized record for a single recipe.

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Unique recipe ID |
| `title` | `str` | Recipe title |
| `description` | `str` | Derived description (currently empty) |
| `image` | `str` | Spoonacular image URL |
| `categories` | `list[str]` | Capitalized category names |
| `cook_time_minutes` | `int` | Parsed from ISO 8601 duration |
| `servings` | `int` | Serving count |
| `ingredients` | `list[dict]` | `[{"name": ..., "amount": ...}]` |
| `instructions` | `list[dict]` | `[{"step": N, "description": ...}]` |
| `ingredients_text` | `str` | Flat ingredient names for TF-IDF |

### `IndexData` (dataclass)
Container returned by `load_index()`.

| Field | Type | Purpose |
|---|---|---|
| `recipes` | `dict[int, Recipe]` | Lookup by recipe ID |
| `categories` | `list[str]` | Sorted unique category names |
| `ingredient_strings` | `list[str]` | Parallel list for TF-IDF |
| `recipe_ids` | `list[int]` | Parallel list — index aligns with above |

> **Note:** `ingredient_strings[i]` and `recipe_ids[i]` always refer to the same recipe. This alignment is required by the TF-IDF vectorizer in `search_service`.

---

## `load_index()` Flow

```
load_index()
│
├── 1. READ CSV
│       pd.read_csv(config.DATA_PATH)
│       → raw DataFrame (N rows)
│
├── 2. FOR EACH ROW
│   │
│   ├── Parse raw fields
│   │     _parse_json_list(ingredients)  → list[dict]  (name, qty, unit, ...)
│   │     _parse_json_list(instructions) → list[dict|str]
│   │     _parse_categories(row)         → list[str]   (capitalized)
│   │     _parse_cook_time(row)          → int (minutes)
│   │     _parse_servings(row)           → int
│   │
│   ├── Normalize
│   │     ingredients  → [{"name": ..., "amount": _format_amount(...)}]
│   │                     _format_amount: joins qty + unit + preparation
│   │     instructions → [{"step": N, "description": ...}]
│   │                     handles both plain str items and dict items
│   │
│   ├── Build search text
│   │     _build_ingredients_text()  → "chicken garlic onion ..."
│   │
│   ├── Construct Recipe dataclass
│   │     Recipe(id, title, image, categories, cook_time_minutes,
│   │            servings, ingredients, instructions, ingredients_text)
│   │
│   └── Append to accumulators
│         recipes[recipe_id] = recipe
│         ingredient_strings.append(ingredients_text)   ← used by TF-IDF
│         recipe_ids.append(recipe_id)                  ← parallel index
│
├── 3. COLLECT CATEGORIES
│       flatten all recipe.categories → deduplicate → sort alphabetically
│
└── 4. RETURN IndexData
        ├── recipes            dict[int, Recipe]   ← lookup by ID
        ├── categories         list[str]            ← filter sidebar
        ├── ingredient_strings list[str]            ── parallel lists
        └── recipe_ids         list[int]            ── aligned by position
```

---

## Helper Functions

| Function | Purpose |
|---|---|
| `_parse_categories(row)` | Splits comma-separated category string, capitalizes each |
| `_parse_json_list(raw)` | Safely parses JSON-encoded list from a CSV cell; returns `[]` on failure |
| `_build_ingredients_text(ingredients)` | Joins ingredient `name` fields into a single string |
| `_format_amount(ingredient)` | Builds readable amount string from `quantity + unit + preparation` |
| `_parse_cook_time(row)` | Tries `cook_time`, `prep_time`, `total_time` columns in order |
| `_parse_iso_duration(value)` | Parses `PT25M` / `PT1H30M` ISO 8601 format into total minutes |
| `_parse_servings(row)` | Safely extracts int servings count |

---

## Key Design Points

- **No persistence** — everything lives in memory; `load_index()` is called once at server startup via `search_service._ensure_index()`.
- **Parallel lists** — `ingredient_strings` and `recipe_ids` are positionally aligned, enabling direct TF-IDF matrix indexing.
- **TF-IDF corpus** — title + ingredient names only; instructions are excluded to keep search signal clean and relevant.
- **ISO 8601 duration** — `_parse_iso_duration` handles both `PT25M` and `PT1H30M` formats.
- **Instruction flexibility** — handles both plain string items and `{"step", "description"}` dict items from the CSV.

---

## Autocomplete Suggestion System

**Files:** `n_gram/trainer.py`, `n_gram/suggester.py`

The N-gram index is built from recipe titles and ingredient names after `load_index()` completes. It powers the `/api/v1/search/suggest` endpoint.

### Phrase Normalization (`n_gram/loader.py`)

Before any phrase enters the index it passes through `_normalize_phrase`:
1. Lowercase
2. Strip non-alphanumeric characters (`-`, `(`, `)`, `/`, etc.) — replaced with spaces
3. Collapse whitespace

```
"Stir-Fry Chicken"  →  "stir fry chicken"
"Soup (Spicy)"      →  "soup spicy"
"tomato paste"      →  "tomato paste"   (unchanged)
```

---

### Two Data Structures Built at Training Time

#### 1. `prefix_map: dict[str, list[str]]`
Maps every **character prefix of each full phrase** to phrases that start with it.

```
phrase: "mango salsa"
prefix_map keys added:
  "m" → ["mango salsa", ...]
  "ma" → ["mango salsa", ...]
  ...
  "mango sa" → ["mango salsa", "mango sauce"]
  "mango sal" → ["mango salsa"]
  "mango salsa" → ["mango salsa"]
```

**Strength:** fast, precise — matches phrases that literally start with the query string.
**Weakness:** only matches from the START of the full phrase. `"mango sa"` will never find `"thai green mango salad"` because that phrase starts with `"thai"`, not `"mango"`.

---

#### 2. `word_index: dict[str, list[str]]`
Maps every **individual word (stemmed)** to all phrases that contain it anywhere.

```
phrase: "thai green mango salad"
word_index keys added (each word is stemmed before indexing):
  stem("thai")  = "thai"  → ["thai green mango salad", "thai mango salsa", ...]
  stem("green") = "green" → ["thai green mango salad", ...]
  stem("mango") = "mango" → ["thai green mango salad", "mango salsa", "mango sauce", ...]
  stem("salad") = "salad" → ["thai green mango salad", "pasta salad", ...]
```

Stemmed keys mean `"tomatoes"` and `"tomato"` both resolve to the same key `"tomato"`, so queries with either form find the same phrases.

**Strength:** finds phrases that contain a word anywhere, not just at the start; stemming handles word-form variants.
**Weakness:** less precise on its own — must be combined with a partial-word filter.

---

### Why Two Steps Are Needed — Concrete Example

Suppose the index contains these phrases:
```
"mango salsa"
"mango sauce"
"thai green mango salad"
```

User types: **`"mango sa"`**

#### Step 1 — `prefix_map["mango sa"]`
```
"mango sa" is a character prefix of:
  "mango salsa"  ✅  (starts with "mango sa")
  "mango sauce"  ✅  (starts with "mango sa")

Result: ["mango salsa", "mango sauce"]
```
Step 1 finds the direct continuations — good. But `"thai green mango salad"` is missed entirely because it starts with `"thai"`, not `"mango"`.

#### Step 3 — word-boundary lookup (always runs for multi-word queries, merged with Steps 1+2)
```
Query split:
  complete_words = ["mango"]
  partial        = "sa"

word_index["mango"] = ["mango salsa", "mango sauce", "thai green mango salad"]

Filter: keep only phrases where any word starts with "sa"
  "mango salsa"           → "salsa" starts with "sa" ✅
  "mango sauce"           → "sauce" starts with "sa" ✅
  "thai green mango salad" → "salad" starts with "sa" ✅

Result: ["mango salsa", "mango sauce", "thai green mango salad"]
```

#### Merged output (Step 1 first, Step 3 adds new entries)
```
["mango salsa", "mango sauce", "thai green mango salad"]
```
`"mango salsa"` and `"mango sauce"` rank first (exact prefix match = higher confidence).
`"thai green mango salad"` follows as a word-level match.

---

### Full `suggest_phrases` Lookup Chain

```
Query: "tomatoes sa"
│
├── Step 1 — prefix_map["tomatoes sa"]
│           → exact character prefix match (original query)
│
├── Step 2 — prefix_map[stem_all_but_last("tomatoes sa")]
│           → prefix_map["tomato sa"]   (stems all complete words, keeps partial "sa")
│           Always merged with Step 1 (not a fallback)
│
├── Step 3 — word_index[stem("tomato")] ∩ words-starting-"sa"   (multi-word queries always run this)
│           → adds phrases containing "tomato" anywhere with a word starting "sa"
│           Complete words are stemmed before word_index lookup
│
│   Merge: Steps 1+2 results first, Step 3 appends new entries (deduped)
│
└── Step 4 — trailing-slice fallback   (only if Steps 1–3 all returned empty)
            try progressively shorter trailing slices of the query
            e.g. "garlic tomato p" → try "tomato p" → ["tomato paste", "tomato puree"]
```

**Single-word queries** skip Step 3 (no complete words to intersect). Steps 1 and 2 (original and stemmed prefix) always run.

---

### Additional Example: Multiple Complete Words Narrow Results

User types: **`"green mango sa"`**

```
Step 1: prefix_map["green mango sa"] → []   (no phrase starts with "green mango sa")

Step 3: complete_words = ["green", "mango"],  partial = "sa"
        word_index["green"] = ["thai green mango salad"]
        word_index["mango"] = ["mango salsa", "mango sauce", "thai green mango salad"]
        intersection        = ["thai green mango salad"]
        filter words starting "sa": "salad" ✅
        → ["thai green mango salad"]

Result: ["thai green mango salad"]
```

Each complete word acts as an AND filter, narrowing results to only phrases that contain all specified words.

