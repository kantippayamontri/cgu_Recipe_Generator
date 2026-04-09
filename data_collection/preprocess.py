from pathlib import Path
import pandas as pd
from pandas import DataFrame

from config import (
    BACKUP_RAW_INGREDIENTS_PATH,
    BACKUP_RAW_RECIPES_PATH,
    RAW_INGREDIENTS_PATH,
    RAW_RECIPES_PATH,
)

from .preprocess_recipe import preprocess_recipes
from .preprocess_ingredient import preprocess_ingredients


def load_recipes_csv() -> pd.DataFrame | None:
    """Load recipes from master CSV if it exists."""
    if not Path(RAW_RECIPES_PATH).exists():
        print(f"Warning: {RAW_RECIPES_PATH} not found")
        return None
    return pd.read_csv(RAW_RECIPES_PATH)


def load_ingredients_csv() -> pd.DataFrame | None:
    """Load ingredients from standard CSV if it exists."""
    if not Path(RAW_INGREDIENTS_PATH).exists():
        print(f"Warning: {RAW_INGREDIENTS_PATH} not found")
        return None
    return pd.read_csv(RAW_INGREDIENTS_PATH)


def load_backup_recipes() -> pd.DataFrame | None:
    """Load recipes from backup CSV if it exists."""
    if not Path(BACKUP_RAW_RECIPES_PATH).exists():
        print(f"Warning: {BACKUP_RAW_RECIPES_PATH} not found")
        return None
    return pd.read_csv(BACKUP_RAW_RECIPES_PATH)


def summarize_data() -> tuple[dict, DataFrame | None, DataFrame | None]:
    """Print summary statistics for loaded datasets."""
    summary = {}

    # Recipes summary
    df_recipes = load_recipes_csv()
    if df_recipes is not None:
        summary["recipes"] = {
            "rows": len(df_recipes),
            "columns": list(df_recipes.columns),
            "missing_values": df_recipes.isnull().sum().to_dict(),
            "dtypes": df_recipes.dtypes.astype(str).to_dict(),
        }

    # Ingredients summary
    df_ingredients = load_ingredients_csv()
    if df_ingredients is not None:
        summary["ingredients"] = {
            "rows": len(df_ingredients),
            "columns": list(df_ingredients.columns),
            "missing_values": df_ingredients.isnull().sum().to_dict(),
            "unique_recipe_ids": df_ingredients["recipe_id"].nunique(),
        }

    return summary, df_recipes, df_ingredients


if __name__ == "__main__":
    print("Data Preprocessing Module")
    print("=" * 50)

    summary, df_recipes, df_ingredients = summarize_data()

    if not summary:
        print("No data files found. Make sure you've run the fetcher first.")
        print("\nRun: uv run -m data_collection.fetcher")
        exit(1)

    for dataset, stats in summary.items():
        print(f"\n{dataset.upper()}:")
        print(f"  Rows: {stats.get('rows', 'N/A')}")
        print(f"  Columns: {stats.get('columns', [])}")
        if "missing_values" in stats:
            nulls = stats["missing_values"]
            missing_cols = {k: v for k, v in nulls.items() if v > 0}
            if missing_cols:
                print(f"  Missing values in: {missing_cols}")

    # TEST: use for testing
    df_recipes = df_recipes.head(5) if df_recipes is not None else None
    df_ingredients = df_ingredients.head(5) if df_ingredients is not None else None

    # preprocess recipes
    preprocess_recipes()
    
    # preprocess ingredients
    preprocess_ingredients(ingredients_df=df_ingredients)

    print("\n" + "=" * 50)
    print("Data preprocessing check complete.")