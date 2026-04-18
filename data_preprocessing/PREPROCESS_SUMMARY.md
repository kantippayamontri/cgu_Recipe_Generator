# Recipe Data Preprocessing — Full Summary

This document describes every step of the preprocessing pipeline in detail, from raw HTML-extracted JSON files to a TF-IDF-ready dataset.

---

## Pipeline at a Glance

```
data/backup_search/instructions_extracted/   (941 raw JSON files)
          │
          ▼
    Phase 1 — Data Assessment & Exploration
          │
          ▼
    Phase 2 — Text Extraction & Cleaning
          │  data/process/extracted_recipes/
          ▼
    Phase 3 — Ingredient Parsing
          │  data/process/parsed_ingredients/
          ▼
    Phase 4 — Instruction Processing
          │  data/process/processed_recipes/
          ▼
    Phase 5 — Structured Output Generation
          │  data/process/recipes_processed.csv
          ▼
    Phase 6 — Validation & Quality Control
          │  data/process/recipes_final_validated.csv
          ▼
    Phase 7 — TF-IDF Preprocessing
          │  data/process/recipes_tfidf_ready.csv
          ▼
          (Ready for TF-IDF vectorization)
```

To run the full pipeline (Phases 1–6):
```bash
uv run python -m data_preprocessing.full_preprocess
```

To run a specific phase or range:
```bash
uv run python -m data_preprocessing.full_preprocess --from 3 --to 5
uv run python -m data_preprocessing.full_preprocess --only 7
```

---

## Phase 1 — Data Assessment & Exploration

**Script:** `phase1_data_assessment.py`  
**Input:** `data/backup_search/instructions_extracted/` (941 JSON files)  
**Output:** `data/process/phase1_report.txt`

### Purpose
Understand the raw data before writing any extraction logic. This phase scans all JSON files to answer: how many have recipe data, what schema types exist, and how complete each record is.

### What each JSON file contains
Each file was produced by scraping a recipe webpage and extracting structured metadata. Every file has up to three sections:

| Section | Description |
|---------|-------------|
| `microdata` | Schema.org microdata markup embedded in the HTML |
| `json-ld` | JSON-LD blocks from `<script type="application/ld+json">` tags |
| `opengraph` | OpenGraph meta tags (title, image, description) |

### Step-by-step

**Step 1.1 — Load all JSON files**  
Reads every `.json` file from the source directory using `json.load()`. Files that fail to parse are logged as failures.

**Step 1.2 — Extract schema types**  
For each file, the script scans both the `microdata` array (`item["type"]`) and the `json-ld` array (`item["@type"]`), including nested `@graph` objects. It collects a list of all schema type strings found (e.g. `https://schema.org/Recipe`, `BlogPosting`, `Person`, `WPHeader`).

**Step 1.3 — Detect recipe content**  
A file is marked as containing recipe data if any of its schema types contains the string `"Recipe"`.

**Step 1.4 — Extract recipe-level fields for assessment**  
For files that contain a Recipe schema, the script reads these fields to check presence:

- `name` / `headline` → title
- `ingredients` / `recipeIngredient` → ingredient list
- `recipeInstructions` → instruction list
- `prepTime`, `cookTime`, `totalTime`
- `recipeYield` → servings
- `recipeCuisine`, `recipeCategory`

It checks both `microdata.properties` and `json-ld.@graph` to cover all schema formats.

**Step 1.5 — Generate statistics report**  
The report contains:
- Total files / loaded / failed
- Count of files with Recipe schema, with ingredients, with instructions, with both
- Success rates as percentages
- Ranked list of all schema types found
- Per-field coverage (e.g. what % of recipes have a cook time)
- Average ingredient and instruction counts

---

## Phase 2 — Text Extraction & Cleaning

**Script:** `phase2_text_extraction.py`  
**Input:** `data/backup_search/instructions_extracted/` (941 JSON files)  
**Output:** `data/process/extracted_recipes/` (one JSON per recipe)

### Purpose
Extract only the relevant recipe fields from noisy web-scraped data and clean the text — removing HTML tags, navigation text, and whitespace noise.

### Step-by-step

**Step 2.1 — Clean raw text strings**  
Every text value passes through `clean_text()`:
1. Decode HTML entities (`&amp;` → `&`, `&deg;` → `°`)
2. Strip HTML tags with `re.sub(r"<[^>]+>", "", text)`
3. Remove UI/navigation noise using regex patterns:
   - `"Skip to content"`, `"Toggle Menu"`, `"Jump to Recipe"`, `"Print Recipe"`
   - Breadcrumb separators (`Home »`)
   - Generic page links (`About`, `Contact`, `Privacy Policy`)
4. Normalize all whitespace to single spaces and strip

**Step 2.2 — Split instruction text blocks into steps**  
Some sites store instructions as a single long string rather than a structured list. `split_instruction_text()` tries to split it by detecting:
- Labeled steps: `"Step 1:"`, `"Step 1 -"`
- Numbered lists: `"1. "`, `"2) "`

If no numbered steps are found, the whole string is kept as one step.

**Step 2.3 — Extract from microdata (primary path)**  
Iterates over `data["microdata"]` looking for items whose `type` contains `"Recipe"`. If found, extracts from `item["properties"]`:

| Source field | Output field |
|---|---|
| `name` | `title` |
| `ingredients` | `ingredients` (list of strings) |
| `recipeInstructions` | `instructions` (list of strings) |
| `prepTime` | `prep_time` |
| `cookTime` | `cook_time` |
| `totalTime` | `total_time` |
| `recipeYield` | `servings` |
| `recipeCuisine` | `cuisine` |
| `recipeCategory` | `category` |

Multi-value fields (cuisine, category, yield given as lists) are joined with `", "`.

**Step 2.4 — Fall back to json-ld @graph (secondary path)**  
If no microdata Recipe is found, the script searches `data["json-ld"]` for objects containing `"@graph"`, then scans each graph item for `"@type": "Recipe"` (also handles `@type` as a list). The same fields are extracted using JSON-LD property names (`recipeIngredient` instead of `ingredients`).

Instruction steps are parsed through `extract_instructions_from_jsonld()` which handles both:
- `{"@type": "HowToStep", "text": "..."}` dict objects
- Plain strings (passed through the step-splitter)

**Step 2.5 — Save individual recipe JSON files**  
Each successfully extracted recipe is saved to `data/process/extracted_recipes/{recipe_id}.json` where `recipe_id` is the source filename stem (a number).

---

## Phase 3 — Ingredient Parsing

**Script:** `phase3_ingredient_parsing.py`  
**Input:** `data/process/extracted_recipes/` (JSON files from Phase 2)  
**Output:** `data/process/parsed_ingredients/` (JSON files)

### Purpose
Convert raw ingredient strings like `"1 1/2 cups all-purpose flour, sifted"` into structured components: quantity, unit, name, preparation.

### Step-by-step

**Step 3.1 — Skip invalid entries**  
Lines that are empty, end with `:` (section headers like `"For the sauce:"`), or match `(A)` style labels are skipped and marked `is_valid: False`.

**Step 3.2 — Parse quantity**  
`parse_quantity()` scans the beginning of the string for a number in any of these formats (tried in order):

| Format | Example | Result |
|--------|---------|--------|
| Unicode fraction | `½` | `0.5` |
| Mixed number | `1 1/2` | `1.5` |
| Simple fraction | `3/4` | `0.75` |
| Range | `2-3` or `2 to 3` | average: `2.5` |
| Decimal/integer | `2.5`, `3` | `2.5`, `3.0` |

Returns the numeric value and the remaining string after the quantity.

**Step 3.3 — Parse and normalize unit**  
`parse_unit()` checks the first one or two words of the remaining string against `UNIT_MAPPINGS` (60+ entries). It handles:
- Volume: `tsp` → `teaspoon`, `tbsp` → `tablespoon`, `c` → `cup`, `ml` → `milliliter`, etc.
- Weight: `oz` → `ounce`, `lb` / `lbs` → `pound`, `g` → `gram`, `kg` → `kilogram`
- Containers: `can`, `jar`, `bottle`, `pkg` → `package`
- Descriptors: `large`, `medium`, `small`, `whole` → `""` (empty — these are size descriptors, not units)
- Specialty: `clove`, `sprig`, `bunch`, `handful`, `pinch`, `dash`, etc.

Both singular and plural forms are checked (e.g. both `"cup"` and `"cups"`).

**Step 3.4 — Extract preparation notes**  
`extract_preparation()` looks for two patterns:
1. **Comma-separated**: `"eggs, beaten"` → name=`"eggs"`, prep=`"beaten"`
2. **Parenthetical**: `"beef (80% lean)"` → name=`"beef"`, prep=`"80% lean"`

**Step 3.5 — Clean ingredient name**  
`clean_name()` performs several operations on the remaining name string:
1. Remove leading `"of"` (`"1 cup of flour"` → `"flour"`)
2. Remove articles: `"a"`, `"an"`, `"the"`
3. Move `"to taste"` from name to preparation field
4. Scan name for 70+ preparation keywords (`"chopped"`, `"diced"`, `"minced"`, `"fresh"`, `"frozen"`, `"roasted"`, `"boneless"`, etc.) and move them to the preparation field
5. Clean extra whitespace and commas
6. Lowercase the final name

**Step 3.6 — Assemble structured ingredient**  
Each ingredient becomes:
```json
{
  "original": "1 1/2 cups all-purpose flour, sifted",
  "quantity": 1.5,
  "unit": "cup",
  "name": "all-purpose flour",
  "preparation": "sifted",
  "is_valid": true
}
```

Only `is_valid: true` entries are kept in `parsed_ingredients`.

---

## Phase 4 — Instruction Processing

**Script:** `phase4_instruction_processing.py`  
**Input:** `data/process/parsed_ingredients/` (JSON files from Phase 3)  
**Output:** `data/process/processed_recipes/` (JSON files)

### Purpose
Clean and structure cooking instructions, and extract embedded metadata (temperatures, times, equipment mentions).

### Step-by-step

**Step 4.1 — Clean each instruction step**  
`clean_instruction()` applies:
1. Remove step number prefixes: `"Step 1:"`, `"1."`, `"1)"`, `"(1)"` at the start
2. Normalize whitespace to single spaces
3. Strip leading/trailing punctuation: spaces, dashes, colons, semicolons

**Step 4.2 — Split long text blocks into individual steps**  
If a cleaned instruction is longer than 200 characters and contains `". "` or `"; "`, `split_text_into_steps()` splits it by:
1. First tries: labeled step patterns (`"Step 1:"`) or numbered lists (`"1."`)
2. Falls back to: period followed by a capital letter (`". A"`, `". P"`)

Each resulting fragment shorter than 10 characters is discarded.

**Step 4.3 — Extract metadata from each step**  
`extract_metadata()` scans each step with three regex patterns:

- **Temperatures** — matches:
  - `"350°F"`, `"180°C"`
  - `"350 degrees Fahrenheit"`, `"400 deg F"`
  - Heat level words: `"low heat"`, `"medium-high"`, `"high heat"`

- **Times** — matches:
  - `"25 minutes"`, `"2 hours"`, `"30 secs"`
  - Phrases: `"a few minutes"`, `"several minutes"`, `"overnight"`
  - Relative: `"until golden"`, `"for about 10"`

- **Equipment** — matches 30+ kitchen items including:
  - Appliances: `oven`, `stove`, `blender`, `food processor`, `slow cooker`, `air fryer`
  - Cookware: `pan`, `skillet`, `pot`, `wok`, `saucepan`, `baking sheet`, `casserole dish`
  - Utensils: `whisk`, `spatula`, `tongs`, `rolling pin`, `grater`, `colander`

Duplicates within a recipe are removed while preserving order.

**Step 4.4 — Assemble processed instructions**  
Each recipe gets a `processed_instructions` object:
```json
{
  "steps": [
    {
      "text": "Preheat oven to 350°F.",
      "metadata": {
        "temperatures": ["350°F"],
        "times": [],
        "equipment": ["oven"]
      }
    }
  ],
  "step_count": 8,
  "metadata": {
    "temperatures": ["350°F"],
    "times": ["30 minutes", "25 minutes"],
    "equipment": ["oven", "mixing bowl", "baking sheet"]
  }
}
```

---

## Phase 5 — Structured Output Generation

**Script:** `phase5_structure_output.py`  
**Input:** `data/process/processed_recipes/` (JSON files from Phase 4)  
**Output:** `data/process/recipes_processed.csv`

### Purpose
Consolidate all per-recipe JSON files into a single flat CSV, with structured JSON columns for ingredients and instructions, plus quality flags for the next phase.

### Step-by-step

**Step 5.1 — Validate and sanitize each recipe's structure**  
Before extracting data, `sanitize_recipe_structure()` checks and fixes:
- `title` must be a string (reset to `""` if not)
- `parsed_ingredients` must be a list of dicts (reset to `[]` if malformed)
- `processed_instructions` must be a dict with a `steps` list and a `metadata` dict (repaired if missing or wrong type)

Validation errors are logged but do not stop processing.

**Step 5.2 — Deduplicate by recipe_id**  
`recipe_id` is parsed from the filename stem as an integer. If the same ID appears more than once, all duplicates after the first are skipped and counted.

**Step 5.3 — Determine extraction status**  
Each recipe is assigned one of three statuses:

| Status | Condition |
|--------|-----------|
| `success` | Title present AND has ingredients AND has instruction steps |
| `partial` | Has some data but missing title, ingredients, or steps |
| `failed` | No usable data at all (no ingredients AND no steps) |

**Step 5.4 — Serialize ingredients to JSON string**  
`serialize_ingredients()` converts `parsed_ingredients` to a compact JSON string, retaining only four fields per ingredient (dropping internal tracking fields like `is_valid` and `original`):
```json
[{"name":"flour","quantity":1.5,"unit":"cup","preparation":"sifted"}]
```

**Step 5.5 — Serialize instructions to JSON string**  
`serialize_instructions()` extracts just the `text` field from each step object, discarding per-step metadata, producing a flat list:
```json
["Preheat oven to 350°F","Mix dry ingredients in a large bowl"]
```

**Step 5.6 — Extract instruction metadata columns**  
The aggregated temperatures, times, and equipment lists from `processed_instructions["metadata"]` are each serialized as separate JSON string columns.

**Step 5.7 — Write final CSV**  
All records are collected into a pandas DataFrame and saved. The CSV has these columns:

| Column | Type | Description |
|--------|------|-------------|
| `recipe_id` | int | Unique identifier from filename |
| `title` | str | Recipe name |
| `ingredients` | JSON str | Array of `{name, quantity, unit, preparation}` objects |
| `instructions` | JSON str | Array of instruction step strings |
| `prep_time` | str | ISO 8601 duration or text |
| `cook_time` | str | ISO 8601 duration or text |
| `total_time` | str | ISO 8601 duration or text |
| `servings` | str | Number of servings |
| `cuisine` | str | Recipe cuisine |
| `category` | str | Recipe category |
| `extraction_status` | str | `success` / `partial` / `failed` |
| `ingredient_count` | int | Number of parsed ingredients |
| `step_count` | int | Number of instruction steps |
| `instruction_temperatures` | JSON str | Temperatures extracted from steps |
| `instruction_times` | JSON str | Time references extracted from steps |
| `instruction_equipment` | JSON str | Equipment mentioned in steps |
| `has_empty_title` | bool | Quality flag |
| `has_zero_ingredients` | bool | Quality flag |
| `has_zero_steps` | bool | Quality flag |
| `has_validation_errors` | bool | Upstream structure needed sanitizing |

---

## Phase 6 — Validation & Quality Control

**Script:** `phase6_validation.py`  
**Input:** `data/process/recipes_processed.csv`  
**Output:**  
- `data/process/recipes_final_validated.csv` — clean "golden" dataset  
- `data/process/phase6_summary_report.md` — full quality report  
- `data/process/phase6_anomalies.log` — log of every dropped recipe  
- `data/process/phase6_sample_review.md` — 15 random recipes for manual review

### Purpose
Audit the full CSV, remove any records that fail quality checks, and produce a clean dataset that is safe to use for modelling.

### Step-by-step

**Step 6.1 — Detect duplicate recipe_ids**  
Scans all `recipe_id` values; any ID that appears more than once is flagged. All duplicates (second occurrence onward) are marked as anomalous.

**Step 6.2 — Validate each row**  
Three checks are run on every row:

1. **Title check**: `title` must be a non-empty, non-whitespace string.

2. **Ingredients JSON validation** (`validate_ingredients_json()`):
   - Must be valid JSON
   - Must be a JSON array
   - Every element must be a dict
   - `quantity` must be a number or `null` (not a string)
   - `name` must be a non-empty string

3. **Instructions JSON validation** (`validate_instructions_json()`):
   - Must be valid JSON
   - Must be a JSON array
   - Every element must be a non-empty string

**Step 6.3 — Build the clean dataset**  
Only rows with zero validation errors AND no duplicate ID are kept. The rest are removed and their `recipe_id` and error reasons are saved to the anomaly log.

**Step 6.4 — Compute content statistics on clean data**  
On the validated dataset:
- Total and average ingredient counts
- Total and average instruction step counts
- Recipes with zero ingredients or zero steps (still in the clean set — missing data is allowed, just flagged)

**Step 6.5 — Compute metadata coverage**  
Reports what percentage of clean recipes have values for:
- `instruction_temperatures`, `instruction_times`, `instruction_equipment`
- `cuisine`, `category`, `prep_time`, `cook_time`, `servings`

**Step 6.6 — Save sample review**  
15 randomly selected recipes (with `random_state=42` for reproducibility) are formatted as a Markdown document showing their full ingredient table and numbered instruction steps — for human sanity-checking.

---

## Phase 7 — TF-IDF Preprocessing

**Script:** `phase7_tfidf_preprocessing.py`  
**Input:** `data/process/recipes_final_validated.csv` (from Phase 6)  
**Output:**  
- `data/process/recipes_tfidf_ready.csv` — dataset with TF-IDF columns added  
- `data/process/tfidf_ingredients.json` — preprocessed ingredients per recipe  
- `data/process/tfidf_instructions.json` — preprocessed instructions per recipe  
- `data/process/phase7_report.md` — vocabulary reduction statistics

### Purpose
Apply NLP preprocessing (tokenization, stopword removal, lemmatization) to prepare the text for TF-IDF vectorization. Raw ingredient names and instruction text contain noise, plurals, and filler words that reduce the quality of TF-IDF features.

### NLTK dependencies
The following NLTK data packages are auto-downloaded on first run:
- `wordnet` — for lemmatization (WordNetLemmatizer)
- `stopwords` — English stopword list
- `punkt` + `punkt_tab` — for tokenization (both downloaded to support NLTK <3.9 and ≥3.9)

### Ingredient preprocessing (`preprocess_ingredient()`)

Applied to each ingredient `name` string from the parsed ingredients list:

| Step | Operation | Example |
|------|-----------|---------|
| 1 | Lowercase | `"Carrots"` → `"carrots"` |
| 2 | Tokenize with `word_tokenize` | `"green onions"` → `["green", "onions"]` |
| 3 | Strip non-alphabetic characters from each token | `"egg,"` → `"egg"` |
| 4 | Remove tokens shorter than 3 characters | `"of"`, `"a"` dropped |
| 5 | Remove NLTK English stopwords + recipe units | `"cup"`, `"tablespoon"`, `"oz"`, `"gram"`, etc. dropped |
| 6 | Lemmatize as noun | `"carrots"` → `"carrot"`, `"onions"` → `"onion"` |
| 7 | Rejoin tokens | `["green", "onion"]` → `"green onion"` |

**Recipe-specific stopwords** removed (in addition to NLTK English stopwords):  
`cup`, `cups`, `tablespoon`, `tablespoons`, `teaspoon`, `teaspoons`, `tbsp`, `tsp`, `lb`, `lbs`, `oz`, `ounce`, `ounces`, `gram`, `grams`, `ml`, `liter`, `liters`, `pound`, `pounds`, `inch`, `inches`

### Instruction preprocessing (`preprocess_instruction()`)

Applied to each instruction step string:

| Step | Operation | Example |
|------|-----------|---------|
| 1 | Lowercase | `"Preheat the oven..."` → `"preheat the oven..."` |
| 2 | Remove punctuation (replace with space) | `"bake, stirring."` → `"bake  stirring "` |
| 3 | Remove numbers | `"25 minutes"` → `"  minutes"` |
| 4 | Tokenize with `word_tokenize` | splits into word list |
| 5 | Skip empty tokens and pure digit tokens | extra safety after regex |
| 6 | Remove tokens shorter than 3 characters | `"it"`, `"to"` dropped |
| 7 | Remove NLTK English stopwords | `"the"`, `"until"`, `"for"` removed |
| 8 | Lemmatize as verb first, then noun if unchanged | `"cooking"` → `"cook"`, `"degrees"` → `"degree"` |
| 9 | Rejoin tokens | produces clean step string |

**Examples:**

| Before | After |
|--------|-------|
| `"Preheat the oven to 425 degrees."` | `"preheat oven degree"` |
| `"Cook for 25 minutes or until golden brown."` | `"cook minute golden brown"` |
| `"Stir occasionally and serve hot."` | `"stir occasionally serve hot"` |

### Combined TF-IDF text field

`tfidf_text` is built by joining all preprocessed ingredient terms and all preprocessed instruction terms into a single string per recipe:

```
tfidf_text = (all ingredient names joined) + " " + (all instruction steps joined)
```

This combined field is what is passed to `TfidfVectorizer`.

### Vocabulary statistics

Per-recipe columns added to the CSV:

| Column | Description |
|--------|-------------|
| `ingredients_tfidf` | JSON array of preprocessed ingredient name strings |
| `instructions_tfidf` | JSON array of preprocessed instruction step strings |
| `tfidf_text` | Combined single string for TF-IDF input |
| `ingredient_vocab_size` | Unique tokens across this recipe's ingredients |
| `instruction_vocab_size` | Unique tokens across this recipe's instructions |
| `total_vocab_size` | Sum of above two |

The report measures vocabulary reduction by comparing the token-level unique word counts before and after preprocessing across the entire dataset.

### Downstream usage
```python
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

df = pd.read_csv("data/process/recipes_tfidf_ready.csv")

vectorizer = TfidfVectorizer(
    max_features=5000,   # Top 5000 terms
    ngram_range=(1, 2),  # Unigrams and bigrams
    min_df=2,            # Ignore terms appearing in < 2 recipes
    max_df=0.8,          # Ignore terms appearing in > 80% of recipes
)

tfidf_matrix = vectorizer.fit_transform(df["tfidf_text"])
# Shape: (n_recipes × n_features)
```

---

## Data Flow Summary

```
941 raw JSON files
    │
    │  Phase 1: Count, assess, log schema types
    │
    │  Phase 2: Extract title, ingredients (strings), instructions (strings)
    │           Clean HTML, nav text, whitespace
    │           → 941 extracted_recipes JSON files
    │
    │  Phase 3: Parse each ingredient string into
    │           {quantity, unit, name, preparation}
    │           Normalize units, extract prep keywords
    │           → 941 parsed_ingredients JSON files
    │
    │  Phase 4: Clean instruction steps, remove step numbers
    │           Split long blocks into individual steps
    │           Extract temperatures, times, equipment metadata
    │           → 941 processed_recipes JSON files
    │
    │  Phase 5: Consolidate all JSONs into one CSV
    │           Serialize ingredients and instructions as JSON strings
    │           Assign extraction_status, add quality flags
    │           → recipes_processed.csv (~894 rows)
    │
    │  Phase 6: Validate JSON columns, check titles, detect duplicates
    │           Drop anomalous rows
    │           → recipes_final_validated.csv (~1,575 rows*)
    │
    │  Phase 7: Tokenize, remove stopwords, lemmatize
    │           Build tfidf_text = ingredients + instructions
    │           → recipes_tfidf_ready.csv (ready for ML)
    ▼
TF-IDF matrix  (n_recipes × n_features)
```

> \* The validated row count may be higher than the processed count if the Phase 5 CSV is run on a merged or expanded dataset.

---

## Output File Reference

| File | Phase | Description |
|------|-------|-------------|
| `data/process/phase1_report.txt` | 1 | Schema types and field coverage stats |
| `data/process/phase2_report.txt` | 2 | Extraction success rates |
| `data/process/extracted_recipes/*.json` | 2 | Per-recipe JSON with raw text fields |
| `data/process/parsed_ingredients/*.json` | 3 | Per-recipe JSON with structured ingredients |
| `data/process/processed_recipes/*.json` | 4 | Per-recipe JSON with cleaned instructions + metadata |
| `data/process/recipes_processed.csv` | 5 | Consolidated CSV with all recipes |
| `data/process/recipes_final_validated.csv` | 6 | Clean "golden" dataset (anomalies removed) |
| `data/process/phase6_summary_report.md` | 6 | Full quality report in Markdown |
| `data/process/phase6_anomalies.log` | 6 | Every dropped recipe_id with reason |
| `data/process/phase6_sample_review.md` | 6 | 15 random recipes for manual review |
| `data/process/recipes_tfidf_ready.csv` | 7 | Dataset with TF-IDF columns added |
| `data/process/tfidf_ingredients.json` | 7 | Preprocessed ingredients per recipe (dict by ID) |
| `data/process/tfidf_instructions.json` | 7 | Preprocessed instructions per recipe (dict by ID) |
| `data/process/phase7_report.md` | 7 | Vocabulary reduction statistics |

---

*Last updated: 2026-04-13*  
*Pipeline status: Phases 1–7 complete*
