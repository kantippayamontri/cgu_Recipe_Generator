# Frontend — CGU Recipe Generator

## Overview

The `frontend/` folder contains the Streamlit-based web interface for the CGU Recipe Generator. It reads pre-collected recipe and ingredient data from CSV files and presents an interactive, filterable UI with nutrition visualisations.

## Folder Structure

```
frontend/
├── __init__.py               # Package marker
├── app.py                    # Main Streamlit entry point
├── pages_guild/              # UI wireframe spec files
└── components/
    ├── __init__.py           # Components package marker
    ├── ingredient_input.py   # Page 1: Ingredient Input Hub (NLP)
    ├── filters.py            # Sidebar filter widgets
    ├── recipe_card.py        # Expandable recipe display card
    └── charts.py             # Plotly visualisation components
```

## How to Run

```bash
uv run streamlit run frontend/app.py
```

The app will open at `http://localhost:8501` in your browser.

## Components

### `app.py`

- Entry point for the Streamlit application.
- Loads `data/raw/recipes_master.csv` and `data/raw/ingredients_standard.csv` (cached with `@st.cache_data`).
- Builds a `known_ingredients` vocabulary set from the ingredients CSV for NLP quality scoring.
- Renders the **Ingredient Input Hub**, summary metric row, and two tabs: **Recipes** and **Charts**.
- `_apply_filters()` merges ingredient-based recipe matching, NLP-detected dietary tags, and sidebar filter values before passing results to child components.

### `components/ingredient_input.py` _(Page 1: Ingredient Input Hub)_

Implements the main ingredient entry UI and lightweight NLP pipeline:

- **Text area** — accepts natural language input (e.g. _"I have chicken, 2 tomatoes, gluten-free options?"_)
- **Action buttons** — `Parse Ingredients`, `Detect Dietary Constraints`, `🗑️ Clear`
- **NLP Feedback Panel** (shown after analysis):
  - Detected ingredient badges matched against the dataset vocabulary
  - Dietary flag grid: ✅ explicitly requested / ❌ conflicting ingredient detected / ⚠️ ambiguous
  - Text quality score (%) + cleaned text string
- **Image Upload placeholder** — disabled expander; CV feature not yet implemented

Key functions:
| Function | Purpose |
|---|---|
| `parse_ingredient_text()` | Strips quantities/units, matches bigrams + tokens against known ingredients, scores quality |
| `render_ingredient_input_hub()` | Renders the full Page 1 UI and returns a `ParsedInput` dict via session state |

### `components/filters.py`

Renders the **sidebar** with:

- **Dietary Tags** multiselect (vegetarian, vegan, gluten free, dairy free, etc.)
- **Max Calories** slider (0–2000 kcal)
- **Min Health Score** slider (0–100)
- **Max Prep Time** slider (0–180 min)
- **Max Cook Time** slider (0–180 min)

Returns a dictionary of filter values consumed by `app.py`.

### `components/recipe_card.py`

Renders each recipe as a collapsible **expander card** containing:

- Recipe image (if available)
- Health score, calories, prep/cook time
- Dietary tag badges
- Link to full instructions
- Ingredient list (joined from the ingredients CSV)

### `components/charts.py`

Four Plotly visualisations:

| Chart                                 | Description                                                        |
| ------------------------------------- | ------------------------------------------------------------------ |
| **Macronutrient Bar Chart**           | Stacked bar of protein / fat / carbs per recipe (top 20)           |
| **Health Score Histogram**            | Distribution of health scores across filtered results              |
| **Calories vs. Health Score Scatter** | Colour-coded scatter plot with recipe name on hover                |
| **Avg Health Score Gauge**            | Single-value gauge showing average health score of current results |

## Data Sources

| File                                | Rows  | Key Columns                                                                                                                                                 |
| ----------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data/raw/recipes_master.csv`       | 358   | `recipe_id`, `title`, `image`, `calories`, `protein`, `fat`, `carbs`, `healthScore`, `preparationMinutes`, `cookingMinutes`, `dietary_tags`, `instructions` |
| `data/raw/ingredients_standard.csv` | 3,920 | `recipe_id`, `clean_name`, `raw_text`, `amount`, `unit`                                                                                                     |

## Dependencies Added

| Package             | Purpose                                                |
| ------------------- | ------------------------------------------------------ |
| `streamlit>=1.40.0` | Web UI framework                                       |
| `plotly>=5.0.0`     | Interactive charts                                     |
| `pandas>=2.0.0,<3`  | Data manipulation (pinned for streamlit compatibility) |

Dev tools (`ruff`, `pytest`, `pytest-cov`, `mypy`) are in the `[dependency-groups] dev` section of `pyproject.toml`.

## Lint & Format

```bash
uv run ruff check frontend/
uv run ruff format frontend/
```
