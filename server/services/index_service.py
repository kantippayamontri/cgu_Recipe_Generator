"""Load and index recipe data from CSV into memory."""

import json
import logging
from dataclasses import dataclass, field

import pandas as pd

import config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Recipe:
    """Normalized recipe record."""

    id: int
    title: str
    description: str
    image: str
    categories: list[str]
    cook_time_minutes: int
    servings: int
    ingredients: list[dict[str, str]]
    instructions: list[dict[str, str | int]]
    ingredients_text: str


@dataclass
class IndexData:
    """Container for all loaded and indexed recipes."""

    recipes: dict[int, Recipe] = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)
    # For TF-IDF search
    ingredient_strings: list[str] = field(default_factory=list)
    instruction_strings: list[str] = field(default_factory=list)
    recipe_ids: list[int] = field(default_factory=list)


def _parse_categories(row: pd.Series) -> list[str]:
    """Normalize category field into a list of clean category strings."""
    raw = str(row.get("category", ""))
    if not raw or raw == "nan":
        return []
    return [c.strip().capitalize() for c in raw.split(",") if c.strip()]


def _parse_json_list(raw: str | None) -> list[dict[str, str | int]] | list[str]:
    """Safely parse a JSON-encoded list from a CSV cell."""
    if not raw or raw == "nan":
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


def _build_ingredients_text(ingredients: list[dict[str, str]]) -> str:
    """Extract ingredient names for TF-IDF search text."""
    return " ".join(
        ing.get("name", "")
        for ing in ingredients
        if isinstance(ing, dict) and ing.get("name")
    )


def _build_instruction_text(instructions: list[dict[str, str | int]]) -> str:
    """Extract instruction descriptions for TF-IDF search text."""
    return " ".join(
        str(inst.get("description", ""))
        for inst in instructions
        if isinstance(inst, dict) and inst.get("description")
    )


def load_index() -> IndexData:
    """Load all recipes from CSV and build search indices.

    Returns:
        IndexData containing recipes and TF-IDF text data.
    """
    logger.info("Loading recipe index from %s", config.DATA_PATH)

    df = pd.read_csv(config.DATA_PATH)
    logger.info("Loaded %d rows from CSV", len(df))

    recipes: dict[int, Recipe] = {}
    ingredient_strings: list[str] = []
    instruction_strings: list[str] = []
    recipe_ids: list[int] = []

    for _, row in df.iterrows():
        recipe_id = int(row["recipe_id"])
        ingredients = _parse_json_list(str(row.get("ingredients", "")))
        instructions = _parse_json_list(str(row.get("instructions", "")))

        # Normalize ingredients: each item should be {"name": ..., "amount": ...}
        normalized_ingredients: list[dict[str, str]] = []
        for ing in ingredients:
            if isinstance(ing, dict):
                normalized_ingredients.append(
                    {
                        "name": str(ing.get("name", "")),
                        "amount": _format_amount(ing),
                    }
                )

        normalized_instructions: list[dict[str, str | int]] = []
        for idx, inst in enumerate(instructions, start=1):
            if isinstance(inst, str):
                normalized_instructions.append({"step": idx, "description": inst})
            elif isinstance(inst, dict):
                normalized_instructions.append(
                    {
                        "step": inst.get("step", idx),
                        "description": str(inst.get("description", "")),
                    }
                )

        ingredients_text = _build_ingredients_text(normalized_ingredients)
        instructions_text = _build_instruction_text(normalized_instructions)

        recipe = Recipe(
            id=recipe_id,
            title=str(row.get("title", "")),
            description="",  # CSV has no description; will be derived
            image=f"https://img.spoonacular.com/recipes/{recipe_id}-312x231.jpg",
            categories=_parse_categories(row),
            cook_time_minutes=_parse_cook_time(row),
            servings=_parse_servings(row),
            ingredients=normalized_ingredients,
            instructions=normalized_instructions,
            ingredients_text=ingredients_text,
        )
        recipes[recipe_id] = recipe
        ingredient_strings.append(ingredients_text)
        instruction_strings.append(instructions_text)
        recipe_ids.append(recipe_id)

    # Collect unique categories
    all_categories: set[str] = set()
    for recipe in recipes.values():
        all_categories.update(recipe.categories)

    data = IndexData(
        recipes=recipes,
        categories=sorted(all_categories),
        ingredient_strings=ingredient_strings,
        instruction_strings=instruction_strings,
        recipe_ids=recipe_ids,
    )

    logger.info("Indexed %d recipes, %d categories", len(recipes), len(all_categories))
    return data


def _format_amount(ingredient: dict) -> str:
    """Build a human-readable amount string from parsed ingredient data."""
    parts: list[str] = []
    qty = ingredient.get("quantity")
    unit = ingredient.get("unit", "")
    prep = ingredient.get("preparation", "")

    if qty is not None and qty != "":
        # Format nice numbers
        if isinstance(qty, float) and qty == int(qty):
            parts.append(str(int(qty)))
        else:
            parts.append(str(qty))

    if unit:
        parts.append(unit)

    if prep:
        parts.append(prep)

    return " ".join(parts).strip()


def _parse_cook_time(row: pd.Series) -> int:
    """Extract cook time in minutes from ISO 8601 duration or fallback."""
    for col in ("cook_time", "prep_time", "total_time"):
        val = str(row.get(col, ""))
        minutes = _parse_iso_duration(val)
        if minutes > 0:
            return minutes
    return 0


def _parse_iso_duration(value: str) -> int:
    """Parse PT25M or PT1H30M format into total minutes."""
    if not value or value == "nan":
        return 0
    value = value.strip()
    if not value.startswith("PT"):
        return 0

    minutes = 0
    value = value[2:]  # strip PT

    if "H" in value:
        h_part = value.split("H")[0]
        minutes += int(h_part) * 60
        value = value.split("H")[1]

    if "M" in value:
        m_part = value.split("M")[0]
        minutes += int(m_part)

    return minutes


def _parse_servings(row: pd.Series) -> int:
    """Extract servings count from the servings column."""
    val = str(row.get("servings", ""))
    if not val or val == "nan":
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0
