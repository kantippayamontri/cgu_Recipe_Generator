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