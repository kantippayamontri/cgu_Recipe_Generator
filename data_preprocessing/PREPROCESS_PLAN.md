# Recipe Data Preprocessing Plan

## Overview
This document outlines the preprocessing pipeline for extracting structured recipe data from HTML-extracted JSON files.

**Source Data:** `data/backup_search/instructions_extracted/` (941 JSON files)
**Target Output:** `data/process/recipes_processed.csv`

---

## Phase 1: Data Assessment & Exploration

### Objectives
- Load and analyze sample JSON files
- Understand data structure and patterns
- Assess data quality and completeness

### Tasks
1. **Load sample data** (10-20 JSON files)
2. **Check data quality metrics:**
   - Total files: 941
   - Files with valid recipe content: TBD
   - Files with ingredients: TBD
   - Files with instructions: TBD
   - Files with both ingredients AND instructions: TBD
3. **Identify website patterns:**
   - Different recipe sites use different schema structures
   - Common types: BlogPosting, Recipe, Article, WPHeader

### Expected Output
- Data quality report showing extraction success rates
- List of schema types found in the data

---

## Phase 2: Text Extraction & Cleaning

### Objectives
Extract only recipe-relevant content from noisy HTML-extracted data.

### Data Structure
Each JSON file contains three main sections:
- `microdata`: Schema.org microdata markup
- `json-ld`: JSON-LD structured data
- `opengraph`: OpenGraph metadata

### Cleaning Steps

#### Step 2.1: Filter Relevant Schema Types
Keep only these schema types:
- `https://schema.org/Recipe` (or `http://schema.org/Recipe`)
- Content with recipe-related properties

**Remove:**
- `WPHeader` (navigation menus)
- `Blog` (blog metadata)
- `Person` (author info)
- `CreativeWork` (unless it contains recipe data)
- Navigation content, sidebars, footers

#### Step 2.2: Extract Recipe Fields
From valid recipe entries, extract:
- **Title**: `name` or `headline` property
- **Ingredients**: `recipeIngredient` (array of strings)
- **Instructions**: `recipeInstructions` (structured steps or text)
- **Cooking Time**: `cookTime`, `prepTime`, `totalTime`
- **Servings**: `recipeYield`
- **Category**: `recipeCategory`, `recipeCuisine`

#### Step 2.3: Clean Text Content
- Remove HTML tags if present
- Normalize whitespace
- Strip navigation text ("Skip to content", "Toggle Menu", etc.)
- Remove repetitive site content

### Expected Output
- Clean JSON files or in-memory data structure with extracted fields
- Log of files that couldn't be processed

---

## Phase 3: Ingredient Parsing

### Objectives
Parse ingredient strings into structured components.

### Input Format
Raw ingredients are strings like:
- "2 cups flour"
- "1/2 teaspoon salt"
- "3 large eggs, beaten"
- "1 pound ground beef, 80% lean"

### Parsing Tasks

#### Step 3.1: Extract Components
For each ingredient string, extract:
1. **Quantity** (numeric): 2, 1/2, 3
2. **Unit** (standardized): cups, teaspoon, pound
3. **Name** (cleaned): flour, salt, eggs, ground beef
4. **Preparation** (optional): beaten, diced, chopped

#### Step 3.2: Unit Normalization
Standardize common units:
- Volume: tsp → teaspoon, tbsp → tablespoon, cup → cup
- Weight: oz → ounce, lb → pound, g → gram
- Count: whole, large, small, medium

#### Step 3.3: Ingredient Name Cleaning
- Remove preparation notes from name: "eggs, beaten" → "eggs"
- Remove parenthetical content: "beef (80% lean)" → "beef"
- Standardize singular/plural forms
- Lowercase all names

### Expected Output
List of dictionaries per recipe:
```json
[
  {
    "name": "flour",
    "amount": 2.0,
    "unit": "cup",
    "preparation": ""
  },
  {
    "name": "eggs",
    "amount": 3.0,
    "unit": "large",
    "preparation": "beaten"
  }
]
```

---

## Phase 4: Instruction Processing

### Objectives
Extract and clean cooking instructions.

### Input Formats
Instructions can be in various formats:
- **Text block**: "Step 1: Preheat oven... Step 2: Mix ingredients..."
- **List of strings**: ["Preheat oven to 350°F", "Mix dry ingredients"]
- **Structured objects**: `[{"@type": "HowToStep", "text": "..."}]`

### Processing Steps

#### Step 4.1: Extract Instruction Text
- Parse structured HowToStep objects
- Split text blocks into individual steps
- Number steps sequentially

#### Step 4.2: Clean Instructions
- Remove step numbers if already present: "Step 1: ..." → "..."
- Remove excessive whitespace
- Remove navigation/UI text
- Keep only cooking actions

#### Step 4.3: Extract Metadata from Instructions
- Cooking temperatures: "350°F", "180°C"
- Time references: "for 30 minutes", "until golden brown"
- Equipment mentions: "baking sheet", "mixing bowl"

### Expected Output
List of instruction steps:
```json
[
  "Preheat oven to 350°F",
  "Mix flour, sugar, and salt in a large bowl",
  "Add eggs and butter, stir until combined"
]
```

---

## Phase 5: Structured Output Generation

### Objectives
Create final processed dataset.

### Output Format: CSV

**Columns:**
- `recipe_id` (int): Original recipe ID from filename
- `title` (str): Recipe title
- `ingredients` (JSON str): List of parsed ingredient objects
- `instructions` (JSON str): List of instruction steps
- `prep_time` (str): Preparation time (ISO 8601 duration or text)
- `cook_time` (str): Cooking time (ISO 8601 duration or text)
- `total_time` (str): Total time
- `servings` (str): Number of servings
- `cuisine` (str): Recipe cuisine/category
- `extraction_status` (str): Success/partial/failed

### Alternative Output Formats
Consider also saving as:
- **SQLite database**: For faster querying
- **Individual JSON files**: One per recipe in `data/process/recipes/`

---

## Phase 6: Validation & Quality Control

### Objectives
Ensure data quality and completeness.

### Validation Steps

#### Step 6.1: Data Quality Checks
- Verify recipe_id uniqueness
- Check for empty titles
- Check for empty ingredients list
- Check for empty instructions list
- Validate ingredient amounts are numeric
- Verify instruction steps are non-empty

#### Step 6.2: Generate Statistics
- Total recipes processed: 941
- Successfully extracted: TBD
- Partial data (missing ingredients or instructions): TBD
- Failed extractions: TBD
- Average ingredients per recipe: TBD
- Average instruction steps per recipe: TBD

#### Step 6.3: Sample Review
- Manually review 10-20 random recipes
- Verify ingredient parsing accuracy
- Verify instruction completeness
- Note edge cases for refinement

### Expected Output
- Data quality report
- Error log for failed extractions
- Sample data review document

---

## Phase 7: TF-IDF Preprocessing

### Objectives
Prepare text data for TF-IDF vectorization by applying comprehensive NLP preprocessing to both ingredients and instructions.

### Why TF-IDF Preprocessing?
- **Ingredient normalization**: "carrots" and "carrot" should be the same term
- **Text cleaning**: Remove noise (punctuation, stopwords, numbers)
- **Vocabulary reduction**: Reduce unique terms from ~4,500 to ~3,200 (estimated -29%)
- **Better vectors**: Clean text produces more meaningful TF-IDF features

### Input
- `data/process/recipes_final_validated.csv` (from Phase 6)
- 1,575 validated recipes with structured ingredients and instructions

### Processing Steps

#### Step 7.1: Ingredient Preprocessing
For each ingredient name:
1. **Lowercase**: "Carrots" → "carrots"
2. **Lemmatize**: "carrots" → "carrot" (singular form)
3. **Tokenize**: Split multi-word ingredients
4. **Remove stopwords**: Remove "and", "or", "of" from compound ingredients
5. **Remove short tokens**: Remove tokens < 3 characters

**Example:**
```
Input:  "green onions"
Output: "green onion"

Input:  "garlic cloves"
Output: "garlic clove"
```

#### Step 7.2: Instruction Preprocessing
For each instruction step:
1. **Lowercase**: Convert to lowercase
2. **Remove punctuation**: Strip ".,;:!?" etc.
3. **Remove numbers**: "25 minutes" → "minutes" (optional)
4. **Tokenize**: Split into words
5. **Remove stopwords**: Remove common English words
6. **Lemmatize**: Convert to base form ("cooking" → "cook")
7. **Remove short tokens**: Keep only tokens >= 3 characters
8. **Rejoin**: Combine back into clean text

**Example:**
```
Input:  "Preheat the oven to 425 degrees."
Output: "preheat oven degree"

Input:  "Cook for 25 minutes or until golden brown."
Output: "cook minute until golden brown"
```

#### Step 7.3: Create Combined Corpus
- Merge preprocessed ingredients and instructions
- Create single text field per recipe for TF-IDF
- Calculate vocabulary statistics

### Expected Output

#### Files
1. **`data/process/recipes_tfidf_ready.csv`**
   - Same as Phase 6 output plus TF-IDF columns
   
2. **`data/process/tfidf_ingredients.json`**
   - Preprocessed ingredient names per recipe
   
3. **`data/process/tfidf_instructions.json`**
   - Preprocessed instruction steps per recipe

4. **`data/process/phase7_report.md`**
   - Vocabulary reduction statistics
   - Sample before/after comparisons
   - TF-IDF validation results

#### New CSV Columns
| Column | Description |
|--------|-------------|
| `ingredients_tfidf` | JSON array of preprocessed ingredient names |
| `instructions_tfidf` | JSON array of preprocessed instruction steps |
| `tfidf_text` | Combined ingredients + instructions (for TF-IDF) |
| `ingredient_vocab_size` | Number of unique ingredient terms |
| `instruction_vocab_size` | Number of unique instruction terms |
| `total_vocab_size` | Combined vocabulary size |

### Dependencies
- `nltk` (already in pyproject.toml)
  - `wordnet` for lemmatization
  - `stopwords` for stopword removal
  - `punkt` for tokenization

---

## Implementation Priority

### High Priority (Phase 1-2)
- [x] Load and analyze sample data
- [x] Implement schema type filtering
- [x] Extract recipe title, ingredients, instructions
- [x] Clean navigation/UI text

### Medium Priority (Phase 3-4)
- [x] Implement ingredient parsing
- [x] Normalize units
- [x] Clean ingredient names
- [x] Extract and clean instructions

### Lower Priority (Phase 5-7)
- [x] Generate final CSV output
- [x] Implement validation checks
- [x] Generate quality reports
- [x] Review sample data
- [x] Implement TF-IDF preprocessing (Phase 7)

---

## Files Created

1. `data_preprocessing/phase1_data_assessment.py` - Phase 1: Data assessment script
2. `data_preprocessing/phase2_text_extraction.py` - Phase 2: Text extraction & cleaning script
3. `data_preprocessing/phase3_ingredient_parsing.py` - Phase 3: Ingredient parsing script
4. `data_preprocessing/phase4_instruction_processing.py` - Phase 4: Instruction processing script
5. `data_preprocessing/phase5_structure_output.py` - Phase 5: Structured output generation
6. `data_preprocessing/phase6_validation.py` - Phase 6: Validation & quality control
7. `data_preprocessing/phase7_tfidf_preprocessing.py` - Phase 7: TF-IDF preprocessing
8. `data_preprocessing/process_extracted.py` - Main preprocessing script (future)

---

## Output Locations

- **Phase 1 Report:** `data/process/phase1_report.txt`
- **Phase 2 Report:** `data/process/phase2_report.txt`
- **Extracted Recipes:** `data/process/extracted_recipes/{recipe_id}.json`
- **Parsed Ingredients:** `data/process/parsed_ingredients/{recipe_id}.json`
- **Processed Recipes:** `data/process/processed_recipes/{recipe_id}.json`
- **Phase 5 CSV:** `data/process/recipes_processed.csv`
- **Phase 6 Validated CSV:** `data/process/recipes_final_validated.csv`
- **Phase 6 Reports:** `data/process/phase6_summary_report.md`, `data/process/phase6_anomalies.log`, `data/process/phase6_sample_review.md`
- **Phase 7 TF-IDF CSV:** `data/process/recipes_tfidf_ready.csv`
- **Phase 7 Reports:** `data/process/phase7_report.md`
- **TF-IDF JSON Files:** `data/process/tfidf_ingredients.json`, `data/process/tfidf_instructions.json`
- **Quality Report:** `data/process/preprocessing_report.txt`
- **Failed Extractions:** `data/process/failed_extractions.log`

---

## Success Criteria

1. ✅ Successfully process >90% of 941 recipes
2. ✅ Extract ingredients for >85% of recipes
3. ✅ Extract instructions for >85% of recipes
4. ✅ Parse ingredient amounts for >80% of ingredients
5. ✅ Generate actionable quality report

---

## Next Steps

1. Review and approve this plan
2. Start with Phase 1 (data assessment)
3. Implement Phase 2 (text extraction)
4. Iterate and refine based on results

---

*Last Updated: 2025-04-13*
*Status: Phase 1-6 Complete, Phase 7 In Progress*
