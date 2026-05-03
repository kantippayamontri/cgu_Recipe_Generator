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
