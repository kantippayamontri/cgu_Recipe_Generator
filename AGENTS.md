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
├── tf_idf/                      # TF-IDF search engine
│   ├── __init__.py
│   ├── indexer.py
│   ├── searcher.py
│   ├── similarity.py
│   └── loader.py
│
├── n_gram/                      # N-gram autocomplete
│   ├── __init__.py
│   ├── model.py
│   ├── trainer.py
│   └── suggester.py
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

### 8. Security Rules
- NEVER commit `.env` or API keys
- ALWAYS read secrets from environment via `config.py`
- Rate limit Spoonacular API calls (1s between requests)
- Validate all user inputs
- CORS configured for frontend origin only

### 9. Testing Rules
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
