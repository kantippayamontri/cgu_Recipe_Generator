# AGENTS.md

## IDENTITY
Recipe Search Engine using NLP techniques (TF-IDF, N-grams).
Monorepo with 6 sub-projects: data_collection, data_preprocessing, server, frontend, tf_idf, n_gram.

---

## BEHAVIORAL GUIDELINES

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## STRICT CODING RULES

### 1. Project Structure (DO NOT deviate)
```
cgu_Recipe_Generator/
├── config.py                    # Central configuration
├── main.py                      # Python entry point
├── pyproject.toml               # Python dependencies (monorepo)
├── package.json                 # Node.js workspace root
│
├── data_collection/             # Spoonacular API fetching
│   ├── __init__.py
│   ├── fetcher.py
│   ├── preprocess_recipe.py
│   ├── preprocess_ingredient.py
│   └── extract_recipes.py
│
├── data_preprocessing/          # 7-phase pipeline
│   ├── __init__.py
│   ├── full_preprocess.py
│   ├── phase1_data_assessment.py
│   ├── phase2_text_extraction.py
│   ├── phase3_ingredient_parsing.py
│   ├── phase4_instruction_processing.py
│   ├── phase5_structure_output.py
│   ├── phase6_validation.py
│   └── phase7_tfidf_preprocessing.py
│
├── server/                      # FastAPI backend
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── search.py            # Search endpoints
│   │   ├── recipes.py           # Recipe CRUD
│   │   └── suggestions.py       # Autocomplete
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search_service.py
│   │   └── index_service.py
│   └── schemas/
│       ├── __init__.py
│       ├── search.py
│       └── recipe.py
│
├── frontend/                    # React + Vite + Shadcn
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ui/              # Shadcn components
│   │   │   ├── SearchBar.tsx
│   │   │   ├── RecipeCard.tsx
│   │   │   └── FilterSidebar.tsx
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   └── RecipeDetail.tsx
│   │   ├── hooks/
│   │   │   ├── useSearch.ts
│   │   │   └── useSuggestions.ts
│   │   ├── lib/
│   │   │   └── api.ts           # API client
│   │   └── types/
│   │       └── recipe.ts
│   └── index.html
│
   ├── tf_idf/ # TF-IDF search engine (educational/demo module)
   │ ├── __init__.py          # Package API exports
   │ ├── __main__.py          # Runnable demo script
   │ ├── indexer.py           # TfidfIndex, build_tfidf_index, top_terms_for_document
   │ ├── loader.py            # TfidfDocument, load_tfidf_documents from Phase 7 CSV
   │ ├── searcher.py          # search_documents, SearchResult
   │ └── similarity.py        # find_similar_documents, SimilarRecipe
│
   ├── n_gram/ # N-gram autocomplete module
   │ ├── __init__.py          # Package API exports
   │ ├── model.py             # NGramDocument, NGramIndex dataclasses
   │ ├── loader.py            # load_suggestion_documents from recipe index
   │ ├── trainer.py           # build_n_gram_index with prefix lookup
   │ └── suggester.py         # suggest_phrases for autocomplete
│
├── tests/                       # All tests
│
└── data/                        # Data files (gitignored)
```

### 2. Python Rules
- Python version: 3.12+
- Type hints MANDATORY on every function
- No `Any` type unless justified with comment
- Use `logging` module, never `print()` in production code
- Docstrings for public functions (Args/Returns format)

### 3. FastAPI Rules (server/)
- ALL routes MUST have: `response_model`, `status_code`, `summary`
- NEVER put business logic in route handlers → use `services/`
- ALWAYS use Pydantic schemas for request/response
- Version ALL endpoints under `/api/v1/`
- Use async handlers for all routes

### 4. Pydantic Rules
- NEVER use raw `dict` as input/output → use Pydantic schema
- Separate schemas: `*Request`, `*Response`, `*Base`
- NEVER expose internal fields (file paths, indices)

### 5. React/TypeScript Rules (frontend/)
- TypeScript strict mode enabled
- Use functional components with hooks
- Use `@tanstack/react-query` for API state
- Components in `components/`, pages in `pages/`
- Use Shadcn/ui components from `components/ui/`

### 6. Pandas/Data Processing Rules
- Prefer vectorized operations over `.iterrows()`
- Handle `SettingWithCopyWarning` properly
- Validate column existence before operations
- All data paths defined in `config.py`

### 7. Pipeline Rules
- Phase execution order: 1→2→3→4→5→6→7
- Each phase reads from previous phase output
- Run via: `uv run python -m data_preprocessing.full_preprocess`
- Phase options: `--from N`, `--to N`, `--only N`

### 8. TF-IDF Module Rules (tf_idf/)
- Educational/demo module independent from `server/`
- Uses Phase 7 output: `data/process/recipes_tfidf_ready.csv`
- Hybrid approach: sklearn TfidfVectorizer for matrix, custom logic for workflows
- All functions must have type hints and docstrings
- All modules must have corresponding tests in `tests/`
- Demo script: `uv run python -m tf_idf --query "tomato pasta"`
- Similarity: `uv run python -m tf_idf --similar-to <recipe_id>`

### 9. N-Gram Module Rules (n_gram/)
- Autocomplete suggestion module integrated with `server/`
- Trained on recipe titles + ingredient names from `index_service.load_index()`
- Prefix-based matching: "tom" → "tomato", "tomato pasta"
- Integrated into `/api/v1/search/suggest` endpoint
- All functions must have type hints and docstrings
- All modules must have corresponding tests in `tests/`
- Training data: recipe titles and ingredient names (normalized, lowercase)
- Ranking: by match quality (prefix) then by frequency
- Blank query returns top phrases by frequency

### 10. Security Rules
- NEVER commit `.env` or API keys
- ALWAYS read secrets from environment via `config.py`
- Rate limit Spoonacular API calls (1s between requests)
- Validate all user inputs
- CORS configured for frontend origin only

### 11. Testing Rules
- Every new endpoint/function MUST have tests
- Use `pytest` with fixtures
- Mock external API calls
- Test file mirrors source file path

---

## FORBIDDEN ACTIONS
- Do NOT modify `config.py` without asking
- Do NOT skip pipeline phases
- Do NOT use `print()` — use `logging` module
- Do NOT hardcode file paths — use `config.py`
- Do NOT install new packages without listing them first
- Do NOT bypass TypeScript checks with `any`
- Do NOT commit `.env` files

---

## Dependencies

### Python (pyproject.toml)
```toml
dependencies = [
    # existing...
    "fastapi>=0.115.0",
    "uvicorn>=0.32.0",
    "scikit-learn>=1.5.0",
]
```

### Frontend (frontend/package.json)
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "typescript": "^5.6.0",
    "vite": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## Build/Lint/Test Commands

### Package Management (Python - uv)
- Sync dependencies: `uv sync`
- Add dependency: `uv add <package>`
- Add dev dependency: `uv add --dev <package>`

### Package Management (Node.js)
- Install dependencies: `cd frontend && npm install`
- Add dependency: `cd frontend && npm add <package>`
- Add dev dependency: `cd frontend && npm add -D <package>`

### Running Services
- Data fetcher: `uv run -m data_collection.fetcher`
- Full pipeline: `uv run -m data_preprocessing.full_preprocess`
- Single phase: `uv run -m data_preprocessing.full_preprocess --only 5`
- Backend server: `uv run -m server.main`
- Frontend dev: `cd frontend && npm run dev`
- TF-IDF demo: `uv run python -m tf_idf --query "tomato pasta"`
- TF-IDF similarity: `uv run python -m tf_idf --similar-to 100`
- N-gram autocomplete: Built into `/api/v1/search/suggest` endpoint

### Testing
- Run all tests: `pytest tests/`
- Run specific test: `pytest tests/test_search.py::test_search_by_ingredient`
- Run with coverage: `pytest --cov=. tests/`

### Linting & Formatting (Python)
- Check style: `ruff check .`
- Auto-format: `ruff format .`
- Type check: `mypy .`

### Linting & Formatting (Frontend)
- Check: `cd frontend && npm run lint`
- Format: `cd frontend && npm run format`
- Type check: `cd frontend && npm run typecheck`

### Security
- Scan for secrets: `detect-secrets scan --all-files`

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/search` | POST | Search recipes by ingredients/text |
| `/api/v1/search/similar/{id}` | GET | Find similar recipes |
| `/api/v1/recipes/{id}` | GET | Get recipe details |
| `/api/v1/suggestions` | GET | Autocomplete suggestions |
| `/api/v1/ingredients/popular` | GET | Popular ingredients for filters |

---

## Development Workflow

### Terminal 1: Backend
```bash
uv run -m server.main
# Runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Terminal 2: Frontend
```bash
cd frontend && npm run dev
# Runs on http://localhost:5173
```

### Before Committing
```bash
# Python
ruff check . && ruff format . && mypy . && pytest tests/

# Frontend
cd frontend && npm run lint && npm run typecheck
```

---

## BEFORE YOU WRITE ANY CODE — CHECKLIST
- [ ] Does this follow the folder structure?
- [ ] Are all types annotated?
- [ ] Is business logic in service layer?
- [ ] Are secrets safe (env vars)?
- [ ] Is there error handling?
- [ ] Is there a test for this?
- [ ] Does the API endpoint have proper docs?

---

## RESPONSE FORMAT
When providing code, structure as:
1. **What** you are doing
2. **Why** you made that decision
3. **Code block**
4. **Test example** (if applicable)

## Codebase Search (SocratiCode)

This project is indexed with SocratiCode. Always use its MCP tools to explore the codebase
before reading any files directly.

### Workflow

1. **Start most explorations with `codebase_search`.**
   Hybrid semantic + keyword search (vector + BM25, RRF-fused) runs in a single call.
   - Use broad, conceptual queries for orientation: "how is authentication handled",
     "database connection setup", "error handling patterns".
   - Use precise queries for symbol lookups: exact function names, constants, type names.
   - Prefer search results to infer which files to read — do not speculatively open files.
   - **When to use grep instead**: If you already know the exact identifier, error string,
     or regex pattern, grep/ripgrep is faster and more precise — no semantic gap to bridge.
     Use `codebase_search` when you're exploring, asking conceptual questions, or don't
     know which files to look in.

2. **Follow the graph before following imports.**
   Use `codebase_graph_query` to see what a file imports and what depends on it before
   diving into its contents. This prevents unnecessary reading of transitive dependencies.
   - **Before modifying or deleting a file**, check its dependents with `codebase_graph_query`
     to understand the blast radius.
   - **When planning a refactor**, use the graph to identify all affected files before
     making changes.

3. **Use Impact Analysis BEFORE refactoring, renaming, or deleting code.**
   The symbol-level call graph (`codebase_impact`, `codebase_flow`, `codebase_symbol`,
   `codebase_symbols`) goes one step deeper than the file graph: it knows which
   functions and methods call which.
   - `codebase_impact` answers "what breaks if I change X?" (blast radius — every file
     that transitively calls into the target).
   - `codebase_flow` answers "what does this code do?" by tracing forward from an entry
     point. Call with no `entrypoint` to discover candidate entry points (auto-detected
     via orphans, conventional names like `main()`, framework routes, tests).
   - `codebase_symbol` gives a 360° view of one function: definition, callers, callees.
   - `codebase_symbols` lists symbols in a file or searches by name.
   - Always prefer these over reading multiple files when the question is about
     dependencies between functions, not concepts.

4. **Read files only after narrowing down via search.**
   Once search results clearly point to 1–3 files, read only the relevant sections.
   Never read a file just to find out if it's relevant — search first.

5. **Use `codebase_graph_circular` when debugging unexpected behaviour.**
   Circular dependencies cause subtle runtime issues; check for them proactively.
   Also run `codebase_graph_circular` when you notice import-related errors or unexpected
   initialisation order.

6. **Check `codebase_status` if search returns no results.**
   The project may not be indexed yet. Run `codebase_index` if needed, then wait for
   `codebase_status` to confirm completion before searching.

7. **Leverage context artifacts for non-code knowledge.**
   Projects can define a `.socraticodecontextartifacts.json` config to expose database
   schemas, API specs, infrastructure configs, architecture docs, and other project
   knowledge that lives outside source code. These artifacts are auto-indexed alongside
   code during `codebase_index` and `codebase_update`.
   - Run `codebase_context` early to see what artifacts are available.
   - Use `codebase_context_search` to find specific schemas, endpoints, or configs
     before asking about database structure or API contracts.
   - If `codebase_status` shows artifacts are stale, run `codebase_context_index` to
     refresh them.

### When to use each tool

| Goal | Tool |
|------|------|
| Understand what a codebase does / where a feature lives | `codebase_search` (broad query) |
| Find a specific function, constant, or type | `codebase_search` (exact name) or grep if you know already the exact string |
| Find exact error messages, log strings, or regex patterns | grep / ripgrep |
| See what a file imports or what depends on it | `codebase_graph_query` |
| Check blast radius before modifying or deleting a file | `codebase_impact` (symbol-level) or `codebase_graph_query` (file-level) |
| **What breaks if I change function X?** | `codebase_impact target=X` |
| **What does this entry point actually do?** | `codebase_flow entrypoint=X` |
| **List entry points in this codebase** | `codebase_flow` (no args) |
| **Who calls this function and what does it call?** | `codebase_symbol name=X` |
| **What functions/classes exist in this file?** | `codebase_symbols file=path` |
| **Search for symbols by name across the project** | `codebase_symbols query=X` |
| Spot architectural problems | `codebase_graph_circular`, `codebase_graph_stats` |
| Visualise module structure | `codebase_graph_visualize` |
| Verify index is up to date | `codebase_status` |
| Discover what project knowledge (schemas, specs, configs) is available | `codebase_context` |
| Find database tables, API endpoints, infra configs | `codebase_context_search` |

## Tools

<!-- sigmap-tools -->

```json
[
  {
    "name": "sigmap_ask",
    "description": "Rank source files by relevance to a natural-language query. Run before exploring the codebase.",
    "command": "sigmap ask \"$QUERY\""
  },
  {
    "name": "sigmap_validate",
    "description": "Validate SigMap config and measure context coverage. Run after changing config or source dirs.",
    "command": "sigmap validate"
  },
  {
    "name": "sigmap_judge",
    "description": "Score an LLM response for groundedness against source context. Use to verify answer quality.",
    "command": "sigmap judge --response \"$RESPONSE\" --context \"$CONTEXT\""
  },
  {
    "name": "sigmap_query",
    "description": "Rank all files by relevance using TF-IDF and write a focused mini-context.",
    "command": "sigmap --query \"$QUERY\" --context"
  },
  {
    "name": "sigmap_weights",
    "description": "Show learned file-ranking multipliers accumulated from past sessions.",
    "command": "sigmap weights"
  }
]
```

## Auto-generated signatures
<!-- Updated by gen-context.js -->
# Code signatures

## SigMap commands

| When | Command |
|------|---------|
| Before answering a question | `sigmap ask "<your question>"` |
| After code changes | `sigmap validate` |
| To query by topic | `sigmap --query "<topic>"` |

Always run `sigmap ask` or `sigmap --query` before searching for files relevant to a task.
## deps
```
data_preprocessing/phase6_validation.py ← pandas
data_preprocessing/full_preprocess.py ← data_preprocessing
data_preprocessing/phase7_tfidf_preprocessing.py ← nltk, pandas
frontend/src/App.tsx ← components/Footer, components/Navbar, pages/Home, pages/RecipeDetail, pages/SearchResults
frontend/src/components/SearchBar.tsx ← hooks/useSuggestions
frontend/src/hooks/useSearch.ts ← lib/api, types/recipe
frontend/src/hooks/useSuggestions.ts ← lib/api
frontend/src/lib/api.ts ← types/recipe
frontend/src/pages/RecipeDetail.tsx ← components/RecipeCard, lib/api
frontend/src/components/Navbar.tsx ← assets/logo
frontend/src/components/RecipeCard.tsx ← types/recipe
frontend/src/components/FilterSidebar.tsx ← types/recipe
frontend/src/pages/SearchResults.tsx ← components/FilterSidebar, components/RecipeCard, components/SearchBar, hooks/useSearch, lib/api
frontend/src/pages/Home.tsx ← assets/kan_mascot, components/FilterSidebar, components/RecipeCard, components/SearchBar, hooks/useSearch
data_collection/fetcher.py ← config, pandas, requests
tf_idf/__main__.py ← __future__, tf_idf, pandas
tf_idf/indexer.py ← __future__, scipy, sklearn, tf_idf
tf_idf/loader.py ← pandas
tf_idf/searcher.py ← __future__, sklearn, tf_idf
tf_idf/similarity.py ← __future__, sklearn, tf_idf
server/main.py ← fastapi, server
server/routes/search.py ← fastapi, server
server/routes/recipes.py ← fastapi, server
server/services/index_service.py ← pandas, config
server/schemas/recipe.py ← pydantic
server/schemas/search.py ← pydantic, server
server/services/search_service.py ← nltk, sklearn, n_gram, server, numpy
n_gram/__main__.py ← __future__, n_gram, server
n_gram/loader.py ← __future__, n_gram, server
n_gram/model.py ← __future__
n_gram/suggester.py ← __future__, nltk, n_gram
n_gram/trainer.py ← __future__, nltk, n_gram
```

## changes (last 10 commits — 5 days ago)
```
frontend/src/components/RecipeCard.tsx        ~RecipeCard
frontend/src/components/FilterSidebar.tsx     ~FilterSidebar
frontend/src/pages/SearchResults.tsx          ~SearchResults
data_collection/fetcher.py                    +import  +RandomQueryParams  +random_query  +random_ingredient_query
tf_idf/__main__.py                            +demo_search  +demo_similarity  +main
tf_idf/TF_TDF_SUMMARY.md                      +and  +TfidfDocument  +load_tfidf_documents  +TfidfIndex
tf_idf/indexer.py                             ~build_tfidf_index
tf_idf/loader.py                              ~load_tfidf_documents
tf_idf/searcher.py                            ~search_documents
tf_idf/similarity.py                          ~find_similar_documents
server/SEARCH_SERVICE_FLOW_SUMMARY.md         +to
server/main.py                                +health
server/routes/search.py                       +search  +suggestions  +categories
server/routes/recipes.py                      +get_recipe  +get_similar
server/services/index_service.py              +Recipe  +IndexData  +_parse_categories  +_parse_json_list
server/schemas/recipe.py                      +IngredientResponse  +InstructionResponse  +RecipeResponse
server/schemas/search.py                      +CategoryInfo  +SearchRequest  +SearchResponse
server/services/search_service.py             +_stem_tokenize  +_ensure_index  +_recipe_to_response  +to
n_gram/__main__.py                            +run_query  +run_interactive
n_gram/loader.py                              +_normalize_phrase  +load_suggestion_documents
n_gram/N_GRAM_SUMMARY.md                      +for  +holding  +NGramDocument  +NGramIndex
n_gram/model.py                               +NGramDocument  +NGramIndex  +document_count
n_gram/suggester.py                           +_normalize_query  +_stem_all_but_last  +_word_boundary_lookup  +suggest_phrases
n_gram/trainer.py                             +_stem_phrase  +_prefixes  +build_n_gram_index
```

## data_collection

### data_collection/README.md
```
h1 Data Collection Module Documentation
h2 Overview
h2 Installation & Setup
h2 Usage
h3 Basic Pagination Mode
h3 Random Mode
h3 Query-Based Search
h1 Search by ingredient or dish name
h1 Filter by cuisine
h1 Filter by dish type
h1 Combined search
h1 Sort by rating instead of popularity
h1 Italian main courses
h1 Chicken dishes sorted by rating
h1 Desserts with chocolate
h3 Command-Line Options
h2 API Parameters
h3 Query Parameter
h3 Cuisine Parameter
h3 Dish Type Parameter
h3 Sort Parameter
h2 Output Format
h2 Features
h3 Duplicate Detection
h3 Rate Limiting
```

### data_collection/fetcher.py
```
@dataclass RandomQueryParams(query, sort)
def random_query() → RandomQueryParams  # Randomly select a query term and sort order
def random_ingredient_query() → RandomQueryParams  # Randomly select a single ingredient as the search query
def get_cached_data(CACHE_FILE) → list
def get_nrows_in_csv(file_path)
def get_unique_recipe_count(file_path)  # Get count of unique recipe_ids in the CSV
def process_recipes_master(recipes: list)  # Process and save recipes to CSV
def get_existing_recipe_ids(file_path)  # Get set of existing recipe IDs to avoid duplicates
def fetch_recipes_dataset(query: str | None, cuisine: str | None, dish_type: str | None, sort: str) → None  # Fetch recipes using pagination or query-based search
```

## data_preprocessing

### data_preprocessing/phase6_validation.py
```
@dataclass Anomaly(recipe_id, title, errors)
@dataclass ValidationStats(total_records, valid_records, anomaly_records, duplicate_ids, empty_titles, invalid_ingredients_json, invalid_instructions_json, non_numeric_quantities, empty_instruction_steps, zero_ingredients, zero_steps, total_ingredients, total_steps, with_temperatures, with_times, with_equipment, with_cuisine, with_category, with_prep_time, with_cook_time, with_servings)
def load_data() → pd.DataFrame  # Load the processed CSV from Phase 5
def validate_ingredients_json(row: pd.Series) → list[str]  # Validate the ingredients JSON column
def validate_instructions_json(row: pd.Series) → list[str]  # Validate the instructions JSON column
def validate_row(row: pd.Series) → list[str]  # Run all validations on a single row
def audit_dataset(df: pd.DataFrame) → tuple[pd.DataFrame, list[An...  # Run full audit on the dataset
def save_clean_csv(clean_df: pd.DataFrame) → None  # Save the validated clean dataset
def save_anomaly_log(anomalies: list[Anomaly]) → None  # Save anomaly log file
def save_summary_report(stats: ValidationStats, anomalies: list[Anomaly]) → None  # Save comprehensive Markdown quality report
def save_sample_review(clean_df: pd.DataFrame) → None  # Save sample review with 15 random recipes in Markdown
def main() → None  # Run Phase 6 validation & quality control
```

### data_preprocessing/full_preprocess.py
```
def parse_args() → argparse.Namespace  # Parse command-line arguments
def run_pipeline(start: int, end: int) → None  # Execute preprocessing phases sequentially
def main() → None  # Entry point for the full preprocessing pipeline
```

### data_preprocessing/PREPROCESS_PLAN.md
```
h1 Recipe Data Preprocessing Plan
h2 Overview
h2 Phase 1: Data Assessment & Exploration
h3 Objectives
h3 Tasks
h3 Expected Output
h2 Phase 2: Text Extraction & Cleaning
h3 Data Structure
h3 Cleaning Steps
h4 Step 2.1: Filter Relevant Schema Types
h4 Step 2.2: Extract Recipe Fields
h4 Step 2.3: Clean Text Content
h2 Phase 3: Ingredient Parsing
h3 Input Format
h3 Parsing Tasks
h4 Step 3.1: Extract Components
h4 Step 3.2: Unit Normalization
h4 Step 3.3: Ingredient Name Cleaning
h2 Phase 4: Instruction Processing
h3 Input Formats
h3 Processing Steps
h4 Step 4.1: Extract Instruction Text
h4 Step 4.2: Clean Instructions
h4 Step 4.3: Extract Metadata from Instructions
h2 Phase 5: Structured Output Generation
```

### data_preprocessing/phase7_tfidf_preprocessing.py
```
class TextPreprocessor
  def __init__() → None
  def preprocess_ingredient(name: str) → str
  def preprocess_instruction(text: str, remove_numbers: bool) → str
def ensure_nltk_data() → None  # Ensure required NLTK data is downloaded
def load_data() → pd.DataFrame  # Load the validated CSV from Phase 6
def process_recipe_ingredients(row: pd.Series, preprocessor: TextPreprocessor) → dict[str, Any]  # Process ingredients for a single recipe
def process_recipe_instructions(row: pd.Series, preprocessor: TextPreprocessor) → dict[str, Any]  # Process instructions for a single recipe
def process_all_recipes(df: pd.DataFrame) → tuple[pd.DataFrame, dict[st...  # Process all recipes for TF-IDF
def save_tfidf_csv(df: pd.DataFrame) → None  # Save TF-IDF ready dataset to CSV
def save_json_files(df: pd.DataFrame) → None  # Save preprocessed ingredients and instructions as JSON files
def get_sample_comparisons(df: pd.DataFrame) → tuple[list[tuple], list[tup...  # Get actual before/after samples from the data
def generate_report(df: pd.DataFrame, stats: dict[str, Any]) → str  # Generate Markdown report
def save_report(report: str) → None  # Save Markdown report
def main() → None  # Run Phase 7 TF-IDF preprocessing
```

### data_preprocessing/PREPROCESS_SUMMARY.md
```
h1 Recipe Data Preprocessing — Full Summary
h2 Pipeline at a Glance
h2 Phase 1 — Data Assessment & Exploration
h3 Purpose
h3 What each JSON file contains
h3 Step-by-step
h2 Phase 2 — Text Extraction & Cleaning
h2 Phase 3 — Ingredient Parsing
h2 Phase 4 — Instruction Processing
h2 Phase 5 — Structured Output Generation
h2 Phase 6 — Validation & Quality Control
h2 Phase 7 — TF-IDF Preprocessing
h3 NLTK dependencies
h3 Ingredient preprocessing (`preprocess_ingredient()`)
h3 Instruction preprocessing (`preprocess_instruction()`)
h3 Combined TF-IDF text field
h3 Vocabulary statistics
h3 Downstream usage
h1 Shape: (n_recipes × n_features)
h2 Data Flow Summary
h2 Output File Reference
code-fence plain
code-fence bash
code-fence ---
code-fence json
```

## frontend

### frontend/README.md
```
h1 React + TypeScript + Vite
h2 React Compiler
h2 Expanding the ESLint configuration
code-fence js
code-fence plain
```

### frontend/src/App.tsx
```
component App
export App
```

### frontend/src/components/SearchBar.tsx
```
component SearchBar
props SearchBarProps
hook useState
hook useSuggestions
export SearchBar
handler onSubmit
handler onChange
handler onMouseDown
```

### frontend/src/hooks/useSearch.ts
```
export function useSearch(request)
```

### frontend/src/hooks/useSuggestions.ts
```
export function useSuggestions(query)
```

### frontend/src/lib/api.ts
```
export async function searchRecipes(request,) → Promise<SearchResponse>
export async function fetchSuggestions(query) → Promise<string[]>
export async function fetchCategories() → Promise<CategoryInfo[]>
export async function fetchRecipeById(id) → Promise<Recipe | undefined>
export async function fetchSimilarRecipes(id) → Promise<Recipe[]>
```

### frontend/src/pages/RecipeDetail.tsx
```
component RecipeDetail
hook useParams
hook useState
hook useEffect
hook useQuery
export RecipeDetail
```

### frontend/src/components/Navbar.tsx
```
component Navbar
export Navbar
```

### frontend/index.html
```
title: Bite-Sized Magic
div#root
```

### frontend/src/components/Footer.tsx
```
component Footer
export Footer
```

### frontend/src/components/RecipeCard.tsx
```
component RecipeCard
props RecipeCardProps
hook useState
hook useEffect
export RecipeCard
```

### frontend/src/components/FilterSidebar.tsx
```
component FilterSidebar
props FilterSidebarProps
export FilterSidebar
```

### frontend/src/pages/SearchResults.tsx
```
component LoadingCard
component SearchResults
hook useSearchParams
hook useNavigate
hook useSearch
hook useQuery
export SearchResults
handler onSearch
handler onChange
```

### frontend/src/pages/Home.tsx
```
component Home
props HomeProps
hook useNavigate
hook useSearch
hook useQuery
export Home
handler onSearch
handler onChange
```

### frontend/src/types/recipe.ts
```
export interface Ingredient
export interface Instruction
export interface Recipe
export interface CategoryInfo
export interface SearchRequest
export interface SearchResponse
```

## n_gram

### n_gram/__main__.py
```
def run_query(query: str, limit: int) → None  # Load the index and print suggestions for a single query
def run_interactive(limit: int) → None  # Load the index once, then run a REPL for interactive queries
```

### n_gram/loader.py
```
def load_suggestion_documents(data: IndexData) → list[NGramDocument]  # Extract title and ingredient phrases for autocomplete traini
```

### n_gram/N_GRAM_SUMMARY.md
```
h1 N-Gram Autocomplete Implementation Summary
h2 Overview
h2 Implementation Steps
h3 Step 1: Create the N-Gram Data Model (`model.py`)
h3 Step 2: Build the Training Phrase Loader (`loader.py`)
h3 Step 3: Train the Prefix Index (`trainer.py`)
h3 Step 4: Implement Suggestion Ranking (`suggester.py`)
h3 Step 5: Backend Integration (`search_service.py`)
h1 Module-level cache
h2 File Structure
h2 API Reference
h3 `model.py`
h3 `loader.py`
h3 `trainer.py`
h3 `suggester.py`
h2 Data Flow
h2 Training Data
h2 Behavior
h2 Integration Points
h2 Performance Characteristics
h2 Testing Strategy
h2 Git Commits
h2 Future Enhancements
h2 Lessons Learned
h2 Running the Feature
```

### n_gram/model.py
```
@dataclass NGramDocument(text, source)
@dataclass NGramIndex(documents, phrase_counts, prefix_map, word_index)
```

### n_gram/suggester.py
```
def suggest_phrases(index: NGramIndex, query: str, limit: int) → list[str]
```

### n_gram/trainer.py
```
def build_n_gram_index(documents: list[NGramDocument]) → NGramIndex  # Build prefix lookup data for autocomplete
```

## server

### server/INDEX_SERVICE_FLOW_SUMMARY.md
```
h1 Index Service Flow Summary
h2 Overview
h2 Data Structures
h3 `Recipe` (frozen dataclass)
h3 `IndexData` (dataclass)
h2 `load_index()` Flow
h2 Helper Functions
h2 Key Design Points
h2 Autocomplete Suggestion System
h3 Phrase Normalization (`n_gram/loader.py`)
h3 Two Data Structures Built at Training Time
h4 1. `prefix_map: dict[str, list[str]]`
h4 2. `word_index: dict[str, list[str]]`
h3 Why Two Steps Are Needed — Concrete Example
h4 Step 1 — `prefix_map["mango sa"]`
h4 Step 3 — word-boundary lookup (always runs for multi-word queries, merged with Steps 1+2)
h4 Merged output (Step 1 first, Step 3 adds new entries)
h3 Full `suggest_phrases` Lookup Chain
h3 Additional Example: Multiple Complete Words Narrow Results
code-fence plain
code-fence ---
```

### server/SEARCH_SERVICE_FLOW_SUMMARY.md
```
h1 Search Service Flow Summary
h2 Overview
h2 Module-Level Cache (Globals)
h2 Initialization Flow (`_ensure_index`)
h2 Per-Request Flows
h3 `search_recipes(SearchRequest) → SearchResponse`
h3 `get_recipe(recipe_id) → RecipeResponse | None`
h3 `get_similar_recipes(recipe_id, limit) → list[RecipeResponse]`
h3 `get_categories() → list[str]`
h3 `get_suggestions(query) → list[str]`
h2 How the Pieces Connect
h2 `_recipe_to_response` Conversion
h2 Key Design Points
code-fence plain
code-fence ---
code-fence searchrequest
```

### server/main.py
```
async def health() → dict[str, str]  # Health check endpoint
GET /api/v1/health  →  health()
```

### server/routes/search.py
```
async def search(request: SearchRequest) → SearchResponse  # Search recipes using TF-IDF similarity
async def categories() → list[CategoryInfo]  # Return unique recipe categories sorted by popularity (recipe
```

### server/routes/recipes.py
```
async def get_recipe(recipe_id: int) → RecipeResponse  # Fetch recipe details
async def get_similar(recipe_id: int) → list[RecipeResponse]  # Return recipes similar to the given recipe using TF-IDF
```

### server/services/index_service.py
```
@dataclass Recipe(id, title, description, image, categories, cook_time_minutes, servings, ingredients, instructions, ingredients_text)
@dataclass IndexData(recipes, categories, ingredient_strings, recipe_ids, category_counts)
def load_index() → IndexData  # Load all recipes from CSV and build search indices
```

### server/schemas/recipe.py
```
class IngredientResponse(BaseModel) {name*, amount*}
class InstructionResponse(BaseModel) {step*, description*}
class RecipeResponse(BaseModel) {id*, title*, description*, image*, categories*, cookTimeMinutes*}
```

### server/schemas/search.py
```
class CategoryInfo(BaseModel) {name*, count*}
class SearchRequest(BaseModel) {query?, filters?, limit?}
class SearchResponse(BaseModel) {query*, total*, recipes*}
```

### server/services/search_service.py
```
async def search_recipes(request: SearchRequest) → SearchResponse  # Search recipes using TF-IDF and filter by categories
async def get_recipe(recipe_id: int) → RecipeResponse | None  # Fetch a single recipe by ID
async def get_similar_recipes(recipe_id: int, limit: int) → list[RecipeResponse]  # Find recipes similar to the given recipe using TF-IDF cosine
async def get_categories() → list[tuple[str, int]]  # Return all unique recipe categories sorted by popularity (re
async def get_suggestions(query: str) → list[str]  # Return autocomplete suggestions using n-gram prefix matching
```

## tf_idf

### tf_idf/__main__.py
```
def demo_search(csv_path: Path, query: str, limit: int) → None  # Run a search query and display results with comparison
def demo_similarity(csv_path: Path, recipe_id: int, limit: int) → None  # Find similar recipes to a given recipe
def main() → None  # Run TF-IDF demo based on command-line arguments
```

### tf_idf/TF_TDF_SUMMARY.md
```
h1 TF-IDF Module Implementation Summary
h2 Overview
h2 Implementation Steps
h3 Step 1: Define Loader Contract (`loader.py`)
h3 Step 2: Build Hybrid Indexing Layer (`indexer.py`)
h3 Step 3: Add Query Search Workflow (`searcher.py`)
h3 Step 4: Add Recipe Similarity Workflow (`similarity.py`)
h3 Step 5: Expose Package API (`__init__.py`)
h3 Step 6: Add Demo Comparison Flow (`__main__.py`)
h1 Search for recipes
h1 Find similar recipes
h1 Custom CSV path
h2 File Structure
h2 API Reference
h3 `loader.py`
h3 `indexer.py`
h3 `searcher.py`
h3 `similarity.py`
h2 Testing
h2 Quality Checks
h2 Dependencies
h2 Data Flow
h2 Input Vector Difference (Search vs Similarity)
h2 Comparison with Backend
h2 Future Enhancements (Not Implemented)
```

### tf_idf/indexer.py
```
@dataclass TfidfIndex(recipe_ids, documents, vectorizer, matrix, feature_names)
def build_tfidf_index(documents: list[TfidfDocument]) → TfidfIndex  # Build a TF-IDF index from recipe documents
```

### tf_idf/loader.py
```
@dataclass TfidfDocument(recipe_id, text)
def load_tfidf_documents(csv_path: Path) → list[TfidfDocument]  # Load TF-IDF-ready recipe documents from a CSV file
```

### tf_idf/searcher.py
```
@dataclass SearchResult(recipe_id, score)
def search_documents(index: TfidfIndex, query: str, limit: int) → list[SearchResult]  # Search indexed recipe documents by TF-IDF cosine similarity
```

### tf_idf/similarity.py
```
@dataclass SimilarRecipe(recipe_id, score)
def find_similar_documents(index: TfidfIndex, recipe_id: int, limit: int) → list[SimilarRecipe]  # Find recipes similar to a source recipe
```
