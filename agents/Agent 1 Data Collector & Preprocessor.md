Role: Data Acquisition & Cleaning Specialist
Responsibilities:
  • Fetch recipes from APIs (Spoonacular/Edamam)
  • Web scrape recipes from cooking sites (backup)
  • Clean and standardize recipe data
  • Create structured dataset for downstream tasks

Capabilities:
  • API integration handling (rate limiting, error handling)
  • HTML parsing with BeautifulSoup
  • Data validation and quality checks
  • Save to CSV/JSON with consistent schema

Output:
  • cleaned_recipes.csv with columns:
    - recipe_id, title, ingredients[], instructions[]
    - prep_time, cook_time, servings
    - cuisine_type, difficulty, tags[]