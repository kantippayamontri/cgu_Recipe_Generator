# Search Service Flow Summary

**File:** `server/services/search_service.py`

---

## Overview

`search_service` is the main search engine layer. It wraps `index_service`, builds a TF-IDF matrix and an N-gram autocomplete index on first use, then exposes five async functions consumed by FastAPI route handlers.

---

## Module-Level Cache (Globals)

Populated once on the first request via `_ensure_index()`. Reused for the lifetime of the server process.

| Variable | Type | Purpose |
|---|---|---|
| `_cached_index` | `IndexData \| None` | Loaded recipe index from `index_service` |
| `_tfidf_vectorizer` | `TfidfVectorizer \| None` | Fitted sklearn vectorizer |
| `_tfidf_matrix` | `np.ndarray \| None` | Shape `(N_recipes × 10_000)` |
| `_ngram_index` | `NGramIndex \| None` | Prefix → phrases map for autocomplete |

---

## Initialization Flow (`_ensure_index`)

```
_ensure_index()  — called on every request, skips if already cached
│
├── load_index()  (from index_service)
│       → IndexData { recipes, ingredient_strings, recipe_ids }
│
├── Build TF-IDF matrix
│       corpus[i] = (title[i] × 3) + " " + ingredient_strings[i]
│       TfidfVectorizer(
│           tokenizer=_stem_tokenize,   ← SnowballStemmer("english")
│           token_pattern=None,
│           stop_words="english",
│           ngram_range=(1,2), max_features=10_000
│       ).fit_transform(corpus)
│       → _tfidf_matrix  shape: (N_recipes × 10_000)
│
└── Build N-gram index (for autocomplete)
        load_suggestion_documents(data)
            → recipe titles, normalized lowercase
        build_n_gram_index(docs)
            → _ngram_index  (prefix → phrases map, duplicates deduplicated by stem)
```

---

## Per-Request Flows

### `search_recipes(SearchRequest) → SearchResponse`

```
SearchRequest
├── query: str
├── filters: list[str]  (category names, optional)
└── limit: int          (optional)
     │
     ▼
Has query text?
│
├── YES → TF-IDF Search
│         stemmed_query = " ".join(_stem_tokenize(query))
│         query_vector  = vectorizer.transform([stemmed_query])
│         similarities  = cosine_similarity(query_vector, _tfidf_matrix)
│                         → array of shape (N_recipes,)
│         ranked_indices = argsort(similarities) descending
│         │
│         └── For each idx in ranked order:
│               if similarities[idx] <= 0.0 → break  (no match)
│               recipe = recipes[recipe_ids[idx]]
│               if filters set → skip if recipe has no matching category
│               → _recipe_to_response(recipe)
│               stop when limit reached
│
└── NO  → Browse mode (no TF-IDF)
          iterate recipes dict in insertion order
          apply same category filter + limit logic
     │
     ▼
SearchResponse { query, total, recipes: list[RecipeResponse] }
```

---

### `get_recipe(recipe_id) → RecipeResponse | None`

```
recipe_id → data.recipes.get(id)
found?     → _recipe_to_response(recipe)  → RecipeResponse
not found? → None  (route returns 404)
```

---

### `get_similar_recipes(recipe_id, limit) → list[RecipeResponse]`

```
find idx = recipe_ids.index(recipe_id)
source_vector = _tfidf_matrix[idx]          ← row for this recipe
similarities = cosine_similarity(source_vector, _tfidf_matrix)
ranked_indices = argsort descending
skip self (rid == recipe_id)
collect up to `limit` recipes → list[RecipeResponse]
```

---

### `get_categories() → list[str]`

```
data.categories  → sorted list[str]  (pre-built in index_service)
```

---

### `get_suggestions(query) → list[str]`

```
suggest_phrases(_ngram_index, query)

Step 1 — direct prefix match (original phrase prefixes)
          prefix_map["tom"] → ["tomato", "tomato pasta", ...]

Step 2 — stemmed-query fallback (if Step 1 empty)
          stem all-but-last token: "tomatoes" → "tomato"
          prefix_map["tomato"] → ["tomato", "tomato pasta", ...]

Step 3 — word-boundary lookup (multi-word queries, always merged)
          "mango sa" → complete=["mango"], partial="sa"
          word_index["mango"] ∩ phrases-with-word-starting-"sa"
          → ["thai green mango salad", "thai mango salsa"]

Step 4 — trailing-slice fallback (last resort)
          "garlic tomato p" → try "tomato p" → ["tomato paste", ...]

Ranked: Step 1/2 results first, then Step 3, all by frequency desc.
→ list[str]
```

---

## How the Pieces Connect

```
                     ┌─────────────────────┐
                     │   index_service      │
                     │   load_index()       │
                     │   → IndexData        │
                     └────────┬────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                   ▼
 TfidfVectorizer        n-gram index          recipes dict
 fit on corpus          build_n_gram_index    dict[int, Recipe]
 → _tfidf_matrix        → _ngram_index
      │                       │
      │                       └──── get_suggestions()
      │
 ┌────┴──────────────────────────────┐
 │  cosine_similarity()              │
 ├── search_recipes()   (query→docs) │
 └── get_similar_recipes() (doc→doc) ┘
```

---

## `_recipe_to_response` Conversion

Converts the internal `Recipe` dataclass to the Pydantic `RecipeResponse` schema for API output.

| Internal field | Response field | Notes |
|---|---|---|
| `recipe.id` | `id` | |
| `recipe.title` | `title`, `description` | `description` reuses title (CSV lacks descriptions) |
| `recipe.image` | `image` | |
| `recipe.categories` | `categories` | |
| `recipe.cook_time_minutes` | `cookTimeMinutes` | |
| `recipe.servings` | `servings` | |
| `recipe.ingredients` | `ingredients` | Each → `IngredientResponse(name, amount)` |
| `recipe.instructions` | `instructions` | Each → `InstructionResponse(step, description)` |

---

## Key Design Points

- **Lazy init** — index and matrices are built only on the first request; all subsequent calls reuse module-level globals.
- **Stemmed TF-IDF** — both corpus and queries are tokenized through `_stem_tokenize` (SnowballStemmer), so `"tomato paste"` and `"tomatoes paste"` produce identical query vectors.
- **Title boosting** — each recipe title is repeated 3× in the corpus string, giving title terms 3× the TF weight of ingredient terms.
- **Zero-similarity guard** — results loop breaks immediately when `similarities[idx] <= 0.0`; no unrelated recipes are returned for queries with no vocabulary match.
- **Two search modes** — TF-IDF cosine similarity when a query is present; insertion-order iteration when query is empty.
- **Category filtering** — applied post-ranking for TF-IDF search and during iteration for browse mode.
- **Similarity search** — uses the same TF-IDF matrix but compares a single recipe row against all others (doc-to-doc instead of query-to-doc).
- **Autocomplete** — fully separate N-gram index; does not touch the TF-IDF matrix. Inflected duplicates (e.g. `"tomatoes"`) are collapsed to the most-frequent canonical form at index-build time.
