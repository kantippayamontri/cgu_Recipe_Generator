"""Phase 2: Text Extraction & Cleaning for Recipe Data Preprocessing.

This script extracts recipe-relevant content from JSON files,
filtering for Recipe schema types and cleaning the text content.
"""

import html
import json
import re
from pathlib import Path
from typing import Any


# Configuration
DATA_DIR = Path("data/backup_search/instructions_extracted")
OUTPUT_DIR = Path("data/process/extracted_recipes")
REPORT_PATH = Path("data/process/phase2_report.txt")

# Navigation/UI text patterns to remove
NAVIGATION_PATTERNS = [
    r"Skip to content",
    r"Toggle Menu",
    r"Follow me on \w+!",
    r"Jump to Recipe",
    r"Print Recipe",
    r"Home\s*[»\|>]\s*",
    r"Expand\s*$",
    r"^Search\s*$",
    r"^About\s*$",
    r"^Contact\s*$",
    r"^Privacy Policy\s*$",
]


def load_json_file(filepath: Path) -> dict[str, Any] | None:
    """Load a single JSON file and return its contents."""
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading {filepath}: {e}")
        return None


def clean_text(text: str) -> str:
    """Clean text by removing HTML, normalizing whitespace, and stripping navigation."""
    if not isinstance(text, str):
        text = str(text)

    # Decode HTML entities
    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove navigation/UI patterns
    for pattern in NAVIGATION_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def split_instruction_text(text: str) -> list[str]:
    """Split a single instruction string into individual steps.

    Handles formats like:
    - "Step 1: Do this. Step 2: Do that."
    - "1. Do this. 2. Do that."
    - "1) Do this. 2) Do that."
    - Plain long text (returned as single step)
    """
    # Try splitting on numbered step patterns: "Step 1:", "1.", "1)"
    step_patterns = [
        r"(?i)(?<!\w)step\s*\d+\s*[:\-]\s*",  # "Step 1:", "Step 1 -"
        r"(?<!\d)\d+\.\s+",  # "1. ", "2. "
        r"(?<!\d)\d+\)\s+",  # "1) ", "2) "
    ]

    for pattern in step_patterns:
        parts = re.split(pattern, text)
        # Filter out empty strings from split
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) > 1:
            return parts

    # No numbered steps found — return as single step
    return [text]


def extract_instructions_from_jsonld(instructions: list[Any]) -> list[str]:
    """Extract instruction text from JSON-LD HowToStep objects or strings."""
    steps = []
    for step in instructions:
        if isinstance(step, dict):
            # HowToStep object
            text = step.get("text", "")
            if text:
                cleaned = clean_text(text)
                # A single HowToStep dict should not need splitting
                steps.append(cleaned)
        elif isinstance(step, str):
            cleaned = clean_text(step)
            if cleaned:
                # A single string might contain multiple steps concatenated
                steps.extend(split_instruction_text(cleaned))
    return steps


def extract_recipe_from_microdata(data: dict[str, Any]) -> dict[str, Any] | None:
    """Extract recipe from microdata section."""
    for item in data.get("microdata", []):
        item_type = item.get("type", "")
        if "Recipe" in str(item_type) and "properties" in item:
            props = item["properties"]

            # Extract ingredients
            ingredients = props.get("ingredients", [])
            if isinstance(ingredients, str):
                ingredients = [ingredients]
            cleaned_ingredients = [clean_text(i) for i in ingredients if i]

            # Extract instructions
            instructions = props.get("recipeInstructions", [])
            if isinstance(instructions, str):
                # Single string block — split into steps
                instructions = split_instruction_text(clean_text(instructions))
                cleaned_instructions = [s for s in instructions if s]
            else:
                cleaned_instructions = [clean_text(i) for i in instructions if i]

            return {
                "title": clean_text(props.get("name", "")),
                "ingredients": cleaned_ingredients,
                "instructions": cleaned_instructions,
                "prep_time": props.get("prepTime", ""),
                "cook_time": props.get("cookTime", ""),
                "total_time": props.get("totalTime", ""),
                "servings": clean_text(
                    props.get("recipeYield", "")
                    if isinstance(props.get("recipeYield"), str)
                    else ", ".join(props.get("recipeYield", []))
                ),
                "cuisine": clean_text(
                    props.get("recipeCuisine", "")
                    if isinstance(props.get("recipeCuisine"), str)
                    else ", ".join(props.get("recipeCuisine", []))
                ),
                "category": clean_text(
                    props.get("recipeCategory", "")
                    if isinstance(props.get("recipeCategory"), str)
                    else ", ".join(props.get("recipeCategory", []))
                ),
                "source": "microdata",
            }
    return None


def extract_recipe_from_jsonld(data: dict[str, Any]) -> dict[str, Any] | None:
    """Extract recipe from json-ld @graph section."""
    for item in data.get("json-ld", []):
        if "@graph" in item:
            for graph_item in item["@graph"]:
                t = graph_item.get("@type")
                is_recipe = False
                if isinstance(t, list) and "Recipe" in t:
                    is_recipe = True
                elif t == "Recipe":
                    is_recipe = True

                if is_recipe:
                    # Extract ingredients
                    ingredients = graph_item.get("recipeIngredient", [])
                    if isinstance(ingredients, str):
                        ingredients = [ingredients]
                    cleaned_ingredients = [clean_text(i) for i in ingredients if i]

                    # Extract instructions (may be HowToStep objects or a string block)
                    instructions = graph_item.get("recipeInstructions", [])
                    if isinstance(instructions, str):
                        # Single string block — split into steps
                        instructions = split_instruction_text(clean_text(instructions))
                        cleaned_instructions = [s for s in instructions if s]
                    else:
                        cleaned_instructions = extract_instructions_from_jsonld(
                            instructions
                        )

                    # Handle yield as list or string
                    servings = graph_item.get("recipeYield", "")
                    if isinstance(servings, list):
                        servings = ", ".join(servings)

                    # Handle cuisine as list or string
                    cuisine = graph_item.get("recipeCuisine", "")
                    if isinstance(cuisine, list):
                        cuisine = ", ".join(cuisine)

                    # Handle category as list or string
                    category = graph_item.get("recipeCategory", "")
                    if isinstance(category, list):
                        category = ", ".join(category)

                    return {
                        "title": clean_text(graph_item.get("name", "")),
                        "ingredients": cleaned_ingredients,
                        "instructions": cleaned_instructions,
                        "prep_time": graph_item.get("prepTime", ""),
                        "cook_time": graph_item.get("cookTime", ""),
                        "total_time": graph_item.get("totalTime", ""),
                        "servings": clean_text(servings),
                        "cuisine": clean_text(cuisine),
                        "category": clean_text(category),
                        "source": "json-ld",
                    }
    return None


def extract_recipe(filepath: Path) -> dict[str, Any] | None:
    """Extract recipe data from a JSON file."""
    data = load_json_file(filepath)
    if data is None:
        return None

    # Try microdata first (most common)
    recipe = extract_recipe_from_microdata(data)
    if recipe:
        recipe["recipe_id"] = filepath.stem
        return recipe

    # Fall back to json-ld
    recipe = extract_recipe_from_jsonld(data)
    if recipe:
        recipe["recipe_id"] = filepath.stem
        return recipe

    return None


def process_all_recipes() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Process all JSON files and extract recipes."""
    all_files = sorted(DATA_DIR.glob("*.json"))

    results = {
        "total_files": len(all_files),
        "processed": 0,
        "failed": 0,
        "from_microdata": 0,
        "from_jsonld": 0,
        "with_ingredients": 0,
        "with_instructions": 0,
        "with_both": 0,
        "failed_files": [],
    }

    extracted_recipes = []

    for filepath in all_files:
        recipe = extract_recipe(filepath)

        if recipe is None:
            results["failed"] += 1
            results["failed_files"].append(filepath.name)
            continue

        results["processed"] += 1

        if recipe["source"] == "microdata":
            results["from_microdata"] += 1
        else:
            results["from_jsonld"] += 1

        if recipe["ingredients"]:
            results["with_ingredients"] += 1
        if recipe["instructions"]:
            results["with_instructions"] += 1
        if recipe["ingredients"] and recipe["instructions"]:
            results["with_both"] += 1

        extracted_recipes.append(recipe)

    return extracted_recipes, results


def save_recipes(recipes: list[dict[str, Any]]) -> None:
    """Save extracted recipes to individual JSON files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for recipe in recipes:
        output_path = OUTPUT_DIR / f"{recipe['recipe_id']}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(recipe, f, indent=2, ensure_ascii=False)


def generate_report(results: dict[str, Any]) -> str:
    """Generate a formatted report from processing results."""
    lines = []
    lines.append("=" * 60)
    lines.append("PHASE 2: TEXT EXTRACTION & CLEANING REPORT")
    lines.append("=" * 60)
    lines.append("")

    lines.append("PROCESSING STATISTICS")
    lines.append("-" * 40)
    lines.append(f"Total files: {results['total_files']}")
    lines.append(f"Successfully processed: {results['processed']}")
    lines.append(f"Failed: {results['failed']}")
    lines.append("")

    lines.append("SOURCE BREAKDOWN")
    lines.append("-" * 40)
    lines.append(f"From microdata: {results['from_microdata']}")
    lines.append(f"From json-ld: {results['from_jsonld']}")
    lines.append("")

    lines.append("CONTENT QUALITY")
    lines.append("-" * 40)
    lines.append(f"With ingredients: {results['with_ingredients']}")
    lines.append(f"With instructions: {results['with_instructions']}")
    lines.append(f"With both: {results['with_both']}")
    lines.append("")

    if results["total_files"] > 0:
        lines.append("SUCCESS RATES")
        lines.append("-" * 40)
        lines.append(
            f"Processing rate: {results['processed'] / results['total_files'] * 100:.1f}%"
        )
        lines.append(
            f"Ingredients rate: {results['with_ingredients'] / results['total_files'] * 100:.1f}%"
        )
        lines.append(
            f"Instructions rate: {results['with_instructions'] / results['total_files'] * 100:.1f}%"
        )
        lines.append(
            f"Complete data rate: {results['with_both'] / results['total_files'] * 100:.1f}%"
        )
        lines.append("")

    if results["failed_files"]:
        lines.append("FAILED FILES")
        lines.append("-" * 40)
        for fname in results["failed_files"][:10]:  # Show first 10
            lines.append(f"  {fname}")
        if len(results["failed_files"]) > 10:
            lines.append(f"  ... and {len(results['failed_files']) - 10} more")
        lines.append("")

    lines.append("OUTPUT LOCATION")
    lines.append("-" * 40)
    lines.append(f"Extracted recipes: {OUTPUT_DIR}")
    lines.append("")

    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)


def main() -> None:
    """Run Phase 2 text extraction and cleaning."""
    print("Phase 2: Text Extraction & Cleaning")
    print("=" * 40)

    # Process all recipes
    print("Processing files...")
    recipes, results = process_all_recipes()

    # Save extracted recipes
    print(f"Saving {len(recipes)} extracted recipes...")
    save_recipes(recipes)

    # Generate report
    report = generate_report(results)

    # Save report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_PATH}")
    print(f"Extracted recipes saved to: {OUTPUT_DIR}")
    print("\n" + report)


if __name__ == "__main__":
    main()
