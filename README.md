# cgu_Recipe_Generator

NLP-powered recipe search engine using TF-IDF for search ranking and N-gram (prefix-based) for autocomplete suggestions.

## Quick Start

### Data Collection
```bash
# Basic pagination mode (fetch popular recipes)
uv run -m data_collection.fetcher

# Query-based search
uv run -m data_collection.fetcher --query "chicken pasta"

# With cuisine filter
uv run -m data_collection.fetcher --cuisine "italian"

# With dish type
uv run -m data_collection.fetcher --dish-type "dessert"

# Combined search with sorting
uv run -m data_collection.fetcher --query "tomato" --cuisine "italian" --sort "rating"
```

### Data Preprocessing
```bash
# Run full 7-phase pipeline
uv run -m data_preprocessing.full_preprocess

# Run specific phase
uv run -m data_preprocessing.full_preprocess --only 5
```

### Backend & Frontend
```bash
# Backend server
uv run -m server.main

# Frontend dev server
cd frontend && npm run dev
```

### Food Classification (Image-based Ingredient Recognition)
```bash
# Download dataset
uv run python -m food_classified download

# Train model
uv run python -m food_classified train --epochs 5

# Predict on image
uv run python -m food_classified predict --image path/to/image.jpg
```

## Documentation
- [TF-IDF Module](tf_idf/TF_TDF_SUMMARY.md) - Search engine implementation
- [N-Gram Module](n_gram/N_GRAM_SUMMARY.md) - Autocomplete implementation
- [Food Classified Module](food_classified/README.md) - Image-based ingredient classification
- [Feature Report](REPORT_SUMMARY.md) - Complete feature overview