"""Fetch recipes from Spoonacular API using pagination.

This script fetches recipes using the complexSearch endpoint with proper
pagination to systematically get unique recipes.
"""

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
    return len(df)


def get_unique_recipe_count(file_path):
    """Get count of unique recipe_ids in the CSV."""
    if not os.path.exists(file_path):
        return 0

    df = pd.read_csv(file_path)
    if "recipe_id" not in df.columns:
        return 0
    return df["recipe_id"].nunique()


def process_recipes_master(recipes: list):
    """Process and save recipes to CSV."""
    recipes_list = []
    for r in recipes:
        source_url = r.get("sourceUrl") or "No instructions provided"
        recipes_list.append(
            {
                "recipe_id": r.get("id"),
                "title": r.get("title"),
                "image": r.get("image"),
                "preparationMinutes": "",
                "cookingMinutes": "",
                "healthScore": "",
                "calories": "",
                "protein": "",
                "fat": "",
                "carbs": "",
                "dietary_tags": "",
                "instructions": source_url,
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


def get_existing_recipe_ids(file_path):
    """Get set of existing recipe IDs to avoid duplicates."""
    if not os.path.exists(file_path):
        return set()

    df = pd.read_csv(file_path, usecols=["recipe_id"])
    return set(df["recipe_id"].astype(int))


def fetch_recipes_dataset():
    """Fetch recipes using pagination strategy.

    Uses offset parameter to systematically fetch different recipes.
    Maximum offset is 900, so we'll rotate through cuisines if needed.
    """
    n_recipes_rows = get_nrows_in_csv(RAW_RECIPES_PATH)
    n_recipes_unique = get_unique_recipe_count(RAW_RECIPES_PATH)
    existing_ids = get_existing_recipe_ids(RAW_RECIPES_PATH)
    print(f"Current dataset: {n_recipes_rows} rows, {n_recipes_unique} unique recipes.")
    print(f"Tracking {len(existing_ids)} existing recipe IDs to avoid duplicates.")
    print("Starting fetch with pagination...\n")

    offset = 0
    total_fetched = 0
    total_new = 0
    empty_batches = 0
    max_empty_batches = 3  # Stop after 3 consecutive empty batches
    max_offset = 900  # API limit

    while True:
        # Calculate batch size - API max is 100, but we'll use RECIPE_COUNT
        batch_size = min(RECIPE_COUNT, 100)

        params = {
            "apiKey": SPOONCULAR_API_KEY,
            "number": batch_size,
            "offset": offset,
            "sort": "popularity",  # Sort by popularity for consistent ordering
            "sortDirection": "desc",
            "instructionsRequired": True,  # Only get recipes with instructions
        }

        print(f"[Offset: {offset}] Requesting {batch_size} recipes...")
        response = requests.get(
            SPOONCULAR_BASE_URL + "/recipes/complexSearch", params=params
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return

        quota_request = response.headers.get("X-API-Quota-Request")
        quota_used = response.headers.get("X-API-Quota-Used")
        quota_left = response.headers.get("X-API-Quota-Left")

        print(
            f"  Points used: {quota_request} | Total: {quota_used} | Remaining: {quota_left}"
        )

        data = response.json()
        recipes = data.get("results", [])
        total_results = data.get("totalResults", 0)

        print(f"  API reports {total_results} total matching recipes")
        print(f"  Received {len(recipes)} recipes in this batch")

        if not recipes:
            print("  No recipes returned. Moving to next offset...")
            empty_batches += 1
            if empty_batches >= max_empty_batches:
                print(f"\nStopped: {max_empty_batches} consecutive empty batches")
                break
        else:
            empty_batches = 0  # Reset counter on successful batch

            # Filter out recipes that already exist
            new_recipes_list = [r for r in recipes if r.get("id") not in existing_ids]
            skipped_count = len(recipes) - len(new_recipes_list)

            if skipped_count > 0:
                print(f"  Skipped {skipped_count} duplicates")

            if new_recipes_list:
                process_recipes_master(new_recipes_list)
                # Update existing_ids with newly added recipes
                existing_ids.update(r.get("id") for r in new_recipes_list)
                total_new += len(new_recipes_list)
                print(f"  ✓ Added {len(new_recipes_list)} new unique recipes")
            else:
                print("  No new unique recipes in this batch")

        total_fetched += len(recipes)

        # Check quota
        if quota_left is not None:
            try:
                quota_left_int = int(float(quota_left))
                if quota_left_int <= 0:
                    print("\nAPI quota exhausted. Stopping fetch.")
                    break
            except (ValueError, TypeError):
                pass

        # Move to next offset
        offset += batch_size

        # Check if we've reached max offset
        if offset >= max_offset:
            print(f"\nReached maximum offset ({max_offset}). Stopping.")
            print(
                "Note: To get more recipes, consider using cuisine filters or random mode"
            )
            break

        time.sleep(1)  # Rate limiting

    final_unique = get_unique_recipe_count(RAW_RECIPES_PATH)
    new_recipes = final_unique - n_recipes_unique

    print(f"\n{'='*60}")
    print(f"FETCH COMPLETE")
    print(f"{'='*60}")
    print(f"Total recipes fetched: {total_fetched}")
    print(f"New unique recipes added: {new_recipes}")
    print(f"Dataset now has: {final_unique} unique recipes")
    print(f"Final offset reached: {offset}")


if __name__ == "__main__":
    fetch_recipes_dataset()
