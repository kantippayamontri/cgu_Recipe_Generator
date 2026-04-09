# AGENTS.md

## Build/Lint/Test Commands

### Test Execution
- Run all tests:
  ```bash
  pytest tests/
  ```
- Run single test file:
  ```bash
  pytest tests/test_recipes.py
  ```
- Run specific test function:
  ```bash
  pytest tests/test_recipes.py::test_generate_recipe
  ```
- Run with verbose output:
  ```bash
  pytest -v tests/
  ```

### Linting & Formatting
- Check code style:
  ```bash
  ruff check .
  ```
- Auto-format code:
  ```bash
  ruff format .
  ```
- Type checking:
  ```bash
  mypy .
  ```

### Security Checks
- Scan for secrets:
  ```bash
  detect-secrets scan --all-files
  ```

## Code Style Guidelines

### Imports
1. Standard library imports first
2. Third-party packages (alphabetical):
   ```python
   import dotenv
   import pandas as pd
   import requests
   ```
3. Local application imports
4. Use explicit relative imports for local modules
5. Group imports with blank lines between sections

### Formatting
- 4-space indentation (no tabs)
- Max line length: 88 characters
- Use double quotes for strings
- Trailing commas in collections
- Blank line before class/function definitions
- No space inside parentheses:
  ```python
  df = pd.DataFrame(data)
  ```

### Type Annotations
- Python 3.12+ style type hints required
- Use `Any` sparingly with justification in comments
- Type aliases for complex types:
  ```python
  RecipeData = dict[str, str | list[str]]
  ```
- Function signatures must be fully typed

### Naming Conventions
- `snake_case` for variables/functions
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Private members prefixed with `_`
- Test files: `test_*.py`
- Test functions: `test_*()`

### Error Handling
1. Always catch specific exceptions:
   ```python
   try:
       response = requests.get(url)
       response.raise_for_status()
   except requests.exceptions.HTTPError as e:
       logger.error(f"API error: {e}")
       raise
   ```
2. Never use bare `except:`
3. Log errors with context before re-raising
4. Validate API responses before processing
5. Handle pandas `KeyError` for missing columns

### Security Practices
- NEVER commit `.env` files
- Validate all API inputs
- Use environment variables for secrets
- Sanitize user inputs for recipe queries
- Rate limit API calls to Spoonacular

### Testing Standards
1. 80%+ test coverage required
2. Test edge cases for:
   - Empty API responses
   - Invalid ingredient lists
   - Rate limit errors
3. Use pytest fixtures for test data
4. Mock external API calls:
   ```python
   @pytest.fixture
   def mock_spoonacular_response():
       return {"results": [{"title": "Test Recipe"}]}
   ```

### Documentation
- Module docstrings required
- Function docstrings for public methods:
  ```python
  def get_recipes(ingredients: list[str]) -> list[RecipeData]:
      """Fetch recipes matching ingredients.

      Args:
          ingredients: List of available ingredients

      Returns:
          List of recipe dictionaries with title/instructions
      """
  ```
- Type annotations replace "Returns" section when obvious

## Operational Notes
- Always run `pytest` and `ruff check` before committing
- Verify `.env` is in `.gitignore`
- Use `dotenv.load_dotenv()` for config
- Handle pandas `SettingWithCopyWarning` properly
- Prefer vectorized operations over `.iterrows()`
- API keys must NEVER appear in code