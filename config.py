from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
SPOONCULAR_API_KEY = os.getenv("SPOONCULAR_API_KEY")
SPOONCULAR_BASE_URL = "https://api.spoonacular.com"
RECIPE_COUNT = 900
RECIPE_DATASET_PATH = "data/raw/recipes_dataset.csv"

# raw data file paths
RAW_RECIPES_PATH = "data/raw/recipes_master.csv"
RAW_INGREDIENTS_PATH = "data/raw/ingredients_standard.csv"

# backup raw data file paths
BACKUP_RAW_RECIPES_PATH = "data/backup_search/recipes_master.csv"
BACKUP_RAW_INGREDIENTS_PATH = "data/backup_search/ingredients_standard.csv"

# define the endpoints