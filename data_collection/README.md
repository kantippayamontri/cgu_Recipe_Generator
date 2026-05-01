# Data Collection Module Documentation

**Module:** `data_collection/`  
**Purpose:** Fetch recipes from Spoonacular API with pagination and query-based search  
**Output:** Raw recipe data in CSV format for preprocessing pipeline

---

## Overview

The data collection module fetches recipes from the Spoonacular API using two strategies:

1. **Pagination Mode** - Systematically fetch recipes by offset (default)
2. **Query Mode** - Search recipes by ingredients, cuisines, and dish types

The module handles:
- Duplicate detection and skipping
- Rate limiting (1s between requests)
- API quota monitoring
- Incremental dataset building

---

## Installation & Setup

**Prerequisites:**
- Python 3.12+
- `uv` package manager
- Spoonacular API key

**Environment Variables:**
Create a `.env` file in the project root:
```bash
SPOONCULAR_API_KEY=your_api_key_here
```

**Dependencies:**
```bash
uv sync
```

---

## Usage

### Basic Pagination Mode

Fetch popular recipes using offset-based pagination:

```bash
uv run -m data_collection.fetcher
```

**Behavior:**
- Fetches recipes sorted by popularity
- Automatically skips duplicates
- Stops at offset 900 (API limit)
- Stops after 3 consecutive empty batches

### Random Mode

Randomly select a query, cuisine, dish type, and sort order from predefined lists:

```bash
uv run -m data_collection.fetcher --random
```

**Example output:**
```
Random mode: query='salmon', cuisine='japanese', dish_type='main course', sort='rating'
Starting fetch with query="salmon", cuisine="japanese", dish_type="main course"...
```

Useful for diversifying the dataset without manually specifying parameters each time.

### Query-Based Search

Search recipes by specific criteria:

```bash
# Search by ingredient or dish name
uv run -m data_collection.fetcher --query "chicken pasta"

# Filter by cuisine
uv run -m data_collection.fetcher --cuisine "italian"

# Filter by dish type
uv run -m data_collection.fetcher --dish-type "dessert"

# Combined search
uv run -m data_collection.fetcher --query "tomato" --cuisine "italian" --dish-type "main course"

# Sort by rating instead of popularity
uv run -m data_collection.fetcher --query "pasta" --sort "rating"
```

**Query Examples:**
```bash
# Italian main courses
uv run -m data_collection.fetcher --cuisine "italian" --dish-type "main course"

# Chicken dishes sorted by rating
uv run -m data_collection.fetcher --query "chicken" --sort "rating"

# Desserts with chocolate
uv run -m data_collection.fetcher --query "chocolate" --dish-type "dessert"
```

### Command-Line Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--query` | string | `None` | Search query (e.g., "chicken pasta", "tomato salad") |
| `--cuisine` | string | `None` | Cuisine filter (e.g., "italian", "mexican", "indian") |
| `--dish-type` | string | `None` | Dish type (e.g., "main course", "dessert", "appetizer") |
| `--sort` | choice | `"popularity"` | Sort order: `"popularity"`, `"rating"`, `"relevance"` |
| `--random` | flag | `False` | Randomly pick query, cuisine, dish-type, and sort from predefined lists |

---

## API Parameters

### Query Parameter
Searches recipe titles and ingredients.

**Examples:**
- `"chicken"` - recipes containing chicken
- `"pasta salad"` - recipes with pasta and salad
- `"tomato basil"` - recipes with tomato and basil

### Cuisine Parameter
Filters by cuisine type.

**Supported Values:**
- `"italian"` - Italian cuisine
- `"mexican"` - Mexican cuisine
- `"indian"` - Indian cuisine
- `"chinese"` - Chinese cuisine
- `"american"` - American cuisine
- `"french"` - French cuisine
- `"asian"` - Asian cuisine
- `"mediterranean"` - Mediterranean cuisine
- (and many more - see Spoonacular docs)

### Dish Type Parameter
Filters by meal type or course.

**Common Values:**
- `"main course"` - Main dishes
- `"dessert"` - Sweet dishes
- `"appetizer"` - Starters
- `"side dish"` - Side dishes
- `"salad"` - Salads
- `"soup"` - Soups
- `"breakfast"` - Breakfast items
- `"beverage"` - Drinks

### Sort Parameter
Controls the order of results.

**Options:**
- `"popularity"` - Most popular first (default)
- `"rating"` - Highest rated first
- `"relevance"` - Most relevant to query first

---

## Output Format

**File:** `data/raw_recipes.csv`

**Columns:**
| Column | Description |
|--------|-------------|
| `recipe_id` | Unique recipe identifier from Spoonacular |
| `title` | Recipe title |
| `image` | Recipe image URL |
| `preparationMinutes` | Prep time (minutes) |
| `cookingMinutes` | Cook time (minutes) |
| `healthScore` | Health score (0-100) |
| `calories` | Calorie count |
| `protein` | Protein content (g) |
| `fat` | Fat content (g) |
| `carbs` | Carbohydrate content (g) |
| `dietary_tags` | Dietary restrictions/labels |
| `instructions` | Cooking instructions or source URL |

**Example Output:**
```csv
recipe_id,title,image,preparationMinutes,cookingMinutes,healthScore,calories,protein,fat,carbs,dietary_tags,instructions
1001,Chicken Pasta,http://...,20,30,75,450,25,15,45,"vegetarian-friendly",http://...
```

---

## Features

### Duplicate Detection
The fetcher automatically detects and skips duplicate recipes:
- Tracks recipe IDs from existing CSV
- Skips already-fetched recipes
- Reports count of skipped duplicates

**Example Output:**
```
Current dataset: 500 rows, 450 unique recipes.
Tracking 450 existing recipe IDs to avoid duplicates.
Starting fetch with query="chicken"...

[Offset: 0] Requesting 100 recipes with query...
Skipped 15 duplicates
✓ Added 85 new unique recipes
```

### Rate Limiting
Automatic rate limiting to respect API quotas:
- 1 second delay between requests
- Monitors API quota headers
- Stops when quota is exhausted

### Incremental Building
The fetcher builds datasets incrementally:
- Appends to existing CSV file
- Preserves previous fetches
- Only adds new unique recipes

---

## Implementation Details

### Pagination Strategy
```
Offset 0 → Fetch 100 recipes → Append to CSV
Offset 100 → Fetch 100 recipes → Append to CSV
Offset 200 → Fetch 100 recipes → Append to CSV
...
Offset 900 → Stop (API limit reached)
```

### Query Strategy
```
Query "chicken" + Offset 0 → Fetch 100 recipes → Append
Query "chicken" + Offset 100 → Fetch 100 recipes → Append
...
Empty batch → Increment counter
3 consecutive empty batches → Stop
```

### Duplicate Handling Flow
```
1. Load existing recipe IDs from CSV
2. Fetch batch from API
3. Filter out existing IDs
4. Append only new recipes
5. Update ID set
6. Repeat
```

---

## Error Handling

### API Errors
- **Status Code != 200:** Prints error message and stops
- **Quota Exhausted:** Detects zero quota and stops gracefully
- **Network Error:** Will raise exception (retry logic not implemented)

### Data Errors
- **Missing Recipe ID:** Skipped (recipe requires valid ID)
- **Empty Results:** Increments empty batch counter
- **Invalid Parameters:** API returns error, fetcher stops

---

## Performance

**Typical Performance:**
- Batch size: 100 recipes per request
- Request time: ~1-2 seconds per batch
- Rate limit: 1 second between requests
- Total time for 900 recipes: ~2-3 minutes

**Memory Usage:**
- Minimal memory footprint
- Processes one batch at a time
- CSV appended incrementally

---

## Integration with Preprocessing

After fetching, the raw data is processed by the preprocessing pipeline:

```bash
# 1. Fetch raw data
uv run -m data_collection.fetcher --cuisine "italian"

# 2. Run preprocessing pipeline
uv run -m data_preprocessing.full_preprocess
```

**Preprocessing Phases:**
1. Data Assessment & Exploration
2. Text Extraction & Cleaning
3. Ingredient Parsing
4. Instruction Processing
5. Structured Output Generation
6. Validation & Quality Control
7. TF-IDF Preprocessing

---

## Examples by Use Case

### Example 1: Build Italian Recipe Dataset
```bash
# Fetch Italian cuisine recipes
uv run -m data_collection.fetcher --cuisine "italian"

# Output: ~200-300 Italian recipes
```

### Example 2: Build Dessert Dataset
```bash
# Fetch dessert recipes
uv run -m data_collection.fetcher --dish-type "dessert"

# Output: ~150-200 dessert recipes
```

### Example 3: Search by Ingredient
```bash
# Fetch recipes with chicken
uv run -m data_collection.fetcher --query "chicken"

# Output: ~300-400 chicken recipes
```

### Example 4: Combined Search
```bash
# Fetch Italian main courses with tomato
uv run -m data_collection.fetcher --query "tomato" --cuisine "italian" --dish-type "main course"

# Output: ~50-100 specific recipes
```

### Example 5: High-Rated Recipes
```bash
# Fetch top-rated pasta recipes
uv run -m data_collection.fetcher --query "pasta" --sort "rating"

# Output: ~200-300 highly-rated pasta recipes
```

### Example 6: Random Mode (Dataset Diversification)
```bash
# Let the fetcher pick random parameters
uv run -m data_collection.fetcher --random

# Output: varies each run, e.g. ~100-300 recipes for a random cuisine + ingredient combo
```

---

## Troubleshooting

### Issue: "No recipes returned"
**Cause:** Query too specific or API limit reached  
**Solution:** Try broader search terms or different cuisine/dish type

### Issue: "API quota exhausted"
**Cause:** Daily API limit reached  
**Solution:** Wait for quota reset (next day) or use smaller batch sizes

### Issue: "Duplicate recipes added"
**Cause:** CSV file corrupted or missing recipe_id column  
**Solution:** Manually check CSV for duplicates, ensure `recipe_id` column exists

### Issue: "Empty batches"
**Cause:** Offset beyond available results  
**Solution:** Normal behavior - fetcher stops after 3 consecutive empty batches

---

## API Quota Information

**Spoonacular Free Tier:**
- 150 requests/day
- 10,000 points/month
- Complex search: ~1-5 points per recipe

**Monitoring:**
The fetcher displays quota usage after each request:
```
Points used: 100 | Total: 1500 | Remaining: 8500
```

**Optimization Tips:**
- Use larger batch sizes (fewer requests)
- Avoid duplicate queries
- Cache results locally

---

## Git History

**Recent Changes:**
- Added query-based search functionality
- Added cuisine and dish type filters
- Added sorting options (popularity, rating, relevance)
- Improved duplicate detection
- Added rate limiting and quota monitoring

---

## See Also

- [Spoonacular API Documentation](https://spoonacular.com/food-api)
- [Preprocessing Pipeline](../data_preprocessing/PREPROCESS_SUMMARY.md)
- [TF-IDF Module](../tf_idf/TF_TDF_SUMMARY.md)
- [N-Gram Module](../n_gram/N_GRAM_SUMMARY.md)

---

_Generated on 2026-04-22_
