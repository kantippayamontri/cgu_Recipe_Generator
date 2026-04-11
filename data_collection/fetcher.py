import json
import os

import pandas as pd
import requests

from config import (
    RAW_RECIPES_PATH,
    RECIPE_COUNT,
    SPOONCULAR_API_KEY,
    SPOONCULAR_BASE_URL,
)

import time


def get_cached_data(CACHE_FILE) -> list:
    if os.path.exists(CACHE_FILE):
        print(f"Loading cached data from '{CACHE_FILE}'...")
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    else:
        return []


def get_nrows_in_csv(file_path):
    if not os.path.exists(file_path):
        return 0

    df = pd.read_csv(file_path)
    return len(df)  # row count, header not included


def get_unique_recipe_count(file_path):
    """Get count of unique recipe_ids in the CSV.

    This is used for API offset calculation to avoid fetching duplicates.
    """
    if not os.path.exists(file_path):
        return 0

    df = pd.read_csv(file_path)
    if "recipe_id" not in df.columns:
        return 0
    return df["recipe_id"].nunique()


def process_recipes_master(recipes: list):
    # NOTE: for recipes_master file
    # Minimal response from complexSearch: id, title, image, imageType, sourceUrl
    # Keep all old columns for compatibility, fill only available data
    recipes_list = []
    for r in recipes:
        source_url = r.get("sourceUrl") or "No instructions provided"
        recipes_list.append(
            {
                "recipe_id": r.get("id"),
                "title": r.get("title"),
                "image": r.get("image"),
                "preparationMinutes": "",  # Not available in minimal response
                "cookingMinutes": "",  # Not available in minimal response
                "healthScore": "",  # Not available in minimal response
                "calories": "",  # Not available in minimal response
                "protein": "",  # Not available in minimal response
                "fat": "",  # Not available in minimal response
                "carbs": "",  # Not available in minimal response
                "dietary_tags": "",  # Not available in minimal response
                "instructions": source_url,  # URL from API response
            }
        )

    df_recipes = pd.DataFrame(recipes_list)
    df_recipes.to_csv(
        RAW_RECIPES_PATH,
        index=False,
        mode="a",
        header=not os.path.exists(RAW_RECIPES_PATH),
    )
    print(f"Saved {len(df_recipes)} recipes to '{RAW_RECIPES_PATH}'.")


# Ingredients are no longer fetched from API
# They will be extracted from recipe HTML using source_url


def get_existing_recipe_ids(file_path):
    """Get set of existing recipe IDs to avoid duplicates."""
    if not os.path.exists(file_path):
        return set()

    df = pd.read_csv(file_path, usecols=["recipe_id"])
    return set(df["recipe_id"].astype(int))


def fetch_recipes_dataset():
    n_recipes_rows = get_nrows_in_csv(RAW_RECIPES_PATH)
    n_recipes_unique = get_unique_recipe_count(RAW_RECIPES_PATH)
    existing_ids = get_existing_recipe_ids(RAW_RECIPES_PATH)
    print(f"Current dataset: {n_recipes_rows} rows, {n_recipes_unique} unique recipes.")
    print(f"Tracking {len(existing_ids)} existing recipe IDs to avoid duplicates.")
    print("Starting fetch for new recipes...\n")

    while True:
        params = {
            "apiKey": SPOONCULAR_API_KEY,
            "number": RECIPE_COUNT,
            "random": True,  # Fetch random recipes
            # Minimal request: only get basic info including sourceUrl
            # Full recipe data will be fetched from sourceUrl later
        }

        print(f"Connecting to Spoonacular... requesting {RECIPE_COUNT} recipes.")
        response = requests.get(
            SPOONCULAR_BASE_URL + "/recipes/complexSearch", params=params
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return

        quota_request = response.headers.get("X-API-Quota-Request")
        quota_used = response.headers.get("X-API-Quota-Used")
        quota_left = response.headers.get("X-API-Quota-Left")

        print(f"Points used by this request : {quota_request} {type(quota_request)}")
        print(f"Points used today           : {quota_used} {type(quota_used)}")
        print(f"Points remaining today      : {quota_left} {type(quota_left)}")

        data = response.json()
        recipes = data.get("results", [])

        # Filter out recipes that already exist
        new_recipes_list = [r for r in recipes if r.get("id") not in existing_ids]
        skipped_count = len(recipes) - len(new_recipes_list)

        if skipped_count > 0:
            print(f"Skipped {skipped_count} duplicate recipes.")

        if new_recipes_list:
            process_recipes_master(new_recipes_list)
            # Update existing_ids with newly added recipes
            existing_ids.update(r.get("id") for r in new_recipes_list)
        else:
            print("No new recipes in this batch.")

        if quota_left is not None and int(float(quota_left)) <= 0:
            print("API quota exhausted. Stopping fetch.")
            break

        time.sleep(3)  # Sleep to avoid hitting rate limits

    final_unique = get_unique_recipe_count(RAW_RECIPES_PATH)
    new_recipes = final_unique - n_recipes_unique
    print(f"\nFetch complete. Added {new_recipes} unique recipes.")


if __name__ == "__main__":
    fetch_recipes_dataset()
