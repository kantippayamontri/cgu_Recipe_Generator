import json
import os

import pandas as pd
import requests

from config import (
    RAW_INGREDIENTS_PATH,
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

def process_recipes_master(recipes: list):
    # NOTE: for recipes_master file
    recipes_list = []
    for r in recipes:
        nutrition = {
            n["name"]: n["amount"] for n in r.get("nutrition", {}).get("nutrients", [])
        }

        recipes_list.append(
            {
                "recipe_id": r.get("id"),
                "title": r.get("title"),
                "image": r.get("image"),
                "preparationMinutes": r.get("preparationMinutes"),
                "cookingMinutes": r.get("cookingMinutes"),
                "healthScore": r.get("healthScore"),
                "calories": nutrition.get("Calories"),
                "protein": nutrition.get("Protein"),
                "fat": nutrition.get("Fat"),
                "carbs": nutrition.get("Carbohydrates"),
                "dietary_tags": ", ".join(r.get("diets", [])),
                "instructions": r.get("sourceUrl") or "No instructions provided",
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


def process_ingredients_standard(recipes: list):
    ingredients_mapping = []
    for r in recipes:
        for ing in r.get("extendedIngredients", []):
            ingredients_mapping.append(
                {
                    "recipe_id": r.get("id"),
                    "raw_text": ing.get("original"),
                    "clean_name": ing.get("name"),
                    "amount": ing.get("amount"),
                    "unit": ing.get("unit"),
                }
            )

    df_ing = pd.DataFrame(ingredients_mapping)
    df_ing.to_csv(
        RAW_INGREDIENTS_PATH,
        index=False,
        mode="a",
        header=not os.path.exists(RAW_INGREDIENTS_PATH),
    )
    print(f"Saved {len(df_ing)} ingredient rows to '{RAW_INGREDIENTS_PATH}'.")


def fetch_recipes_dataset():
    n_recipes = get_nrows_in_csv(RAW_RECIPES_PATH)
    n_ingredients = get_nrows_in_csv(RAW_INGREDIENTS_PATH)
    print(f"Current dataset: {n_recipes} recipes, {n_ingredients} ingredient rows.")
    print("Starting fetch for new recipes...\n")

    while True:

        params = {
            "apiKey": SPOONCULAR_API_KEY,
            "offset": get_nrows_in_csv(file_path=RAW_RECIPES_PATH),  # skip already fetched recipes
            "number": RECIPE_COUNT,
            "addRecipeInformation": True,  # Gets instructions, source, and more
            "fillIngredients": True,  # Gets full ingredient lists
            "addRecipeNutrition": True,  # Gets calorie and macro breakdowns
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

        process_recipes_master(recipes)
        process_ingredients_standard(recipes)

        if quota_left is not None and int(float(quota_left)) <= 0:
            print("API quota exhausted. Stopping fetch.")
            break

        time.sleep(3)  # Sleep to avoid hitting rate limits

    new_recipes = get_nrows_in_csv(RAW_RECIPES_PATH) - n_recipes
    new_ingredients = get_nrows_in_csv(RAW_INGREDIENTS_PATH) - n_ingredients
    print(f"\nFetch complete. Added today: {new_recipes} recipes, {new_ingredients} ingredient rows.")


if __name__ == "__main__":
    fetch_recipes_dataset()
