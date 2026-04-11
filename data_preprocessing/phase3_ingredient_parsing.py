"""Phase 3: Ingredient Parsing for Recipe Data Preprocessing.

This script parses ingredient strings into structured components:
- quantity (numeric amount)
- unit (standardized measurement)
- name (cleaned ingredient name)
- preparation (optional preparation notes)
"""

import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any


# Configuration
INPUT_DIR = Path("data/process/extracted_recipes")
OUTPUT_DIR = Path("data/process/parsed_recipes")
REPORT_PATH = Path("data/process/phase3_report.txt")

# Unit normalization mapping
UNIT_MAPPINGS = {
    # Volume
    "tsp": "teaspoon",
    "tsp.": "teaspoon",
    "teaspoons": "teaspoon",
    "tbsp": "tablespoon",
    "tbsp.": "tablespoon",
    "tbs": "tablespoon",
    "tbs.": "tablespoon",
    "tablespoons": "tablespoon",
    "c": "cup",
    "c.": "cup",
    "cup": "cup",
    "cups": "cup",
    "fl oz": "fluid_ounce",
    "fl. oz": "fluid_ounce",
    "fluid ounces": "fluid_ounce",
    "pt": "pint",
    "pt.": "pint",
    "pints": "pint",
    "qt": "quart",
    "qt.": "quart",
    "quarts": "quart",
    "gal": "gallon",
    "gal.": "gallon",
    "gallons": "gallon",
    "ml": "milliliter",
    "ml.": "milliliter",
    "milliliters": "milliliter",
    "millilitres": "milliliter",
    "l": "liter",
    "l.": "liter",
    "liters": "liter",
    "litres": "liter",
    # Weight
    "oz": "ounce",
    "oz.": "ounce",
    "ounces": "ounce",
    "lb": "pound",
    "lb.": "pound",
    "lbs": "pound",
    "lbs.": "pound",
    "pounds": "pound",
    "g": "gram",
    "g.": "gram",
    "grams": "gram",
    "gm": "gram",
    "gm.": "gram",
    "kg": "kilogram",
    "kg.": "kilogram",
    "kilograms": "kilogram",
    "kilogrammes": "kilogram",
    # Count/Size (these become empty as they're descriptors, not units)
    "whole": "",
    "wholes": "",
    "large": "",
    "medium": "",
    "small": "",
    # Miscellaneous
    "pkg": "package",
    "pkg.": "package",
    "pkgs": "package",
    "packages": "package",
    "can": "can",
    "cans": "can",
    "jar": "jar",
    "jars": "jar",
    "bottle": "bottle",
    "bottles": "bottle",
    "slice": "slice",
    "slices": "slice",
    "piece": "piece",
    "pieces": "piece",
    "pinch": "pinch",
    "pinches": "pinch",
    "dash": "dash",
    "dashes": "dash",
    "handful": "handful",
    "handfuls": "handful",
    "bunch": "bunch",
    "bunches": "bunch",
    "clove": "clove",
    "cloves": "clove",
    "stalk": "stalk",
    "stalks": "stalk",
    "sprig": "sprig",
    "sprigs": "sprig",
    "strip": "strip",
    "strips": "strip",
    "stick": "stick",
    "sticks": "stick",
    "cube": "cube",
    "cubes": "cube",
    "envelope": "envelope",
    "envelopes": "envelope",
    "sheet": "sheet",
    "sheets": "sheet",
}

# Common preparation keywords
PREPARATION_KEYWORDS = [
    "beaten",
    "chopped",
    "diced",
    "minced",
    "sliced",
    "grated",
    "shredded",
    "crushed",
    "mashed",
    "peeled",
    "seeded",
    "cored",
    "halved",
    "quartered",
    "julienned",
    "cubed",
    "dried",
    "fresh",
    "frozen",
    "canned",
    "roasted",
    "toasted",
    "fried",
    "sauteed",
    "steamed",
    "boiled",
    "baked",
    "grilled",
    "smoked",
    "cooked",
    "uncooked",
    "raw",
    "ripe",
    "unripe",
    "softened",
    "melted",
    "soft",
    "firm",
    "finely",
    "coarsely",
    "roughly",
    "thinly",
    "thickly",
    "diagonally",
    "crosswise",
    "lengthwise",
    "drained",
    "rinsed",
    "washed",
    "cleaned",
    "trimmed",
    "boneless",
    "skinless",
    "bone-in",
    "skin-on",
    "pitted",
    "zested",
    "juiced",
    "quartered",
    "sectioned",
    "separated",
    "divided",
    "room temperature",
    "cold",
    "warm",
    "hot",
    "optional",
    "or",
]

# Regex patterns
QUANTITY_PATTERN = re.compile(
    r"^\s*(\d+(?:\.\d+)?\s*(?:-\s*\d+(?:\.\d+)?)?|"
    r"\d+\s*/\s*\d+|"
    r"\d+\s+\d+\s*/\s*\d+|"
    r"½|⅓|⅔|¼|¾|⅛|⅜|⅝|⅞)\s*",
    re.UNICODE,
)

FRACTION_UNICODE = {
    "½": 0.5,
    "⅓": 1 / 3,
    "⅔": 2 / 3,
    "¼": 0.25,
    "¾": 0.75,
    "⅛": 0.125,
    "⅜": 0.375,
    "⅝": 0.625,
    "⅞": 0.875,
}


def parse_quantity(text: str) -> tuple[float | None, str]:
    """Extract quantity from the beginning of ingredient text."""
    text = text.strip()

    # Check for unicode fractions first
    for frac, value in FRACTION_UNICODE.items():
        if text.startswith(frac):
            return value, text[len(frac) :].strip()

    # Try mixed number (e.g., "1 1/2")
    mixed_match = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)\s*", text)
    if mixed_match:
        whole = int(mixed_match.group(1))
        num = int(mixed_match.group(2))
        denom = int(mixed_match.group(3))
        quantity = whole + (num / denom)
        return quantity, text[mixed_match.end() :].strip()

    # Try simple fraction (e.g., "1/2", "10/12")
    frac_match = re.match(r"^(\d+)\s*/\s*(\d+)\s*", text)
    if frac_match:
        num = int(frac_match.group(1))
        denom = int(frac_match.group(2))
        return num / denom, text[frac_match.end() :].strip()

    # Try range (e.g., "2-3" or "2 to 3")
    range_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*", text)
    if range_match:
        # Use the average of the range
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return (low + high) / 2, text[range_match.end() :].strip()

    # Try decimal or integer
    num_match = re.match(r"^(\d+(?:\.\d+)?)\s*", text)
    if num_match:
        return float(num_match.group(1)), text[num_match.end() :].strip()

    return None, text


def parse_unit(text: str) -> tuple[str, str]:
    """Extract and normalize unit from ingredient text."""
    text = text.strip()
    words = text.split()

    if not words:
        return "", text

    # Check first word for unit
    first_word = words[0].lower().rstrip("s")  # Remove trailing s for matching
    first_word_with_s = words[0].lower()

    # Try with and without trailing 's'
    for word in [first_word_with_s, first_word]:
        if word in UNIT_MAPPINGS:
            normalized = UNIT_MAPPINGS[word]
            remaining = " ".join(words[1:])
            return normalized, remaining

    # Check for multi-word units (e.g., "fluid ounce")
    if len(words) >= 2:
        two_words = " ".join(words[:2]).lower()
        if two_words in UNIT_MAPPINGS:
            normalized = UNIT_MAPPINGS[two_words]
            remaining = " ".join(words[2:])
            return normalized, remaining

    return "", text


def extract_preparation(text: str) -> tuple[str, str]:
    """Extract preparation notes from ingredient text."""
    preparation = ""

    # Look for comma-separated preparation
    if "," in text:
        parts = text.split(",", 1)
        text = parts[0].strip()
        preparation = parts[1].strip()

    # Look for parenthetical preparation
    paren_match = re.search(r"\(([^)]+)\)", text)
    if paren_match:
        paren_content = paren_match.group(1)
        # Add space when concatenating to avoid merging words
        before = text[: paren_match.start()].strip()
        after = text[paren_match.end() :].strip()
        if before and after:
            text = before + " " + after
        else:
            text = before + after
        if preparation:
            preparation += f", {paren_content}"
        else:
            preparation = paren_content

    return preparation, text


def clean_name(name: str, existing_preparation: str = "") -> tuple[str, str]:
    """Clean ingredient name by removing extra words and normalizing.

    Also extracts preparation keywords from the name.
    Returns (cleaned_name, preparation).
    """
    preparation = existing_preparation

    # Remove leading "of" (e.g., "1 cup of flour" -> "flour")
    name = re.sub(r"^of\s+", "", name, flags=re.IGNORECASE)

    # Remove articles
    name = re.sub(r"^(a|an|the)\s+", "", name, flags=re.IGNORECASE)

    # Remove "to taste" from name (should be in preparation)
    if re.search(r"to taste", name, flags=re.IGNORECASE):
        name = re.sub(r",?\s*to taste\s*$", "", name, flags=re.IGNORECASE)
        if preparation:
            preparation += ", to taste"
        else:
            preparation = "to taste"

    # Extract preparation keywords from name
    found_preparations = []
    name_lower = name.lower()

    for keyword in PREPARATION_KEYWORDS:
        # Match whole words only
        pattern = r"\b" + re.escape(keyword) + r"\b"
        if re.search(pattern, name_lower):
            found_preparations.append(keyword)
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)

    if found_preparations:
        prep_str = ", ".join(found_preparations)
        if preparation:
            preparation += f", {prep_str}"
        else:
            preparation = prep_str

    # Clean up extra whitespace
    name = re.sub(r"\s+", " ", name).strip()
    # Clean up double commas or leading/trailing commas
    name = re.sub(r"\s*,\s*,\s*", ", ", name)
    name = name.strip(", ")

    return name.lower(), preparation


def parse_ingredient(ingredient_text: str) -> dict[str, Any]:
    """Parse a single ingredient string into structured components."""
    original = ingredient_text.strip()

    # Skip empty or section headers (e.g., "Tahini Sauce:", "(A)")
    if not original or original.endswith(":") or re.match(r"^\([A-Z]\)$", original):
        return {
            "original": original,
            "quantity": None,
            "unit": "",
            "name": original,
            "preparation": "",
            "is_valid": False,
        }

    # Extract quantity
    quantity, remaining = parse_quantity(original)

    # If no quantity found, treat entire text as name
    if quantity is None:
        preparation, name = extract_preparation(original)
        name, preparation = clean_name(name, preparation)
        return {
            "original": original,
            "quantity": None,
            "unit": "",
            "name": name,
            "preparation": preparation,
            "is_valid": True,
        }

    # Extract unit
    unit, remaining = parse_unit(remaining)

    # Extract preparation
    preparation, name = extract_preparation(remaining)

    # Clean name and extract preparation keywords
    name, preparation = clean_name(name, preparation)

    return {
        "original": original,
        "quantity": quantity,
        "unit": unit,
        "name": name,
        "preparation": preparation,
        "is_valid": len(name) > 0,
    }


def parse_recipe_ingredients(recipe: dict[str, Any]) -> dict[str, Any]:
    """Parse all ingredients in a recipe."""
    parsed_ingredients = []

    for ingredient_text in recipe.get("ingredients", []):
        parsed = parse_ingredient(ingredient_text)
        if parsed["is_valid"]:
            parsed_ingredients.append(parsed)

    recipe["parsed_ingredients"] = parsed_ingredients
    recipe["ingredient_parse_status"] = (
        "success" if parsed_ingredients else "failed"
    )

    return recipe


def process_all_recipes() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Process all extracted recipes and parse ingredients."""
    all_files = sorted(INPUT_DIR.glob("*.json"))

    results = {
        "total_files": len(all_files),
        "processed": 0,
        "failed": 0,
        "total_ingredients": 0,
        "parsed_with_quantity": 0,
        "parsed_without_quantity": 0,
        "failed_to_parse": 0,
        "failed_files": [],
    }

    parsed_recipes = []

    for filepath in all_files:
        try:
            with open(filepath, encoding="utf-8") as f:
                recipe = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            results["failed"] += 1
            results["failed_files"].append(filepath.name)
            continue

        recipe = parse_recipe_ingredients(recipe)

        results["processed"] += 1
        results["total_ingredients"] += len(recipe.get("ingredients", []))

        for ing in recipe.get("parsed_ingredients", []):
            if ing["quantity"] is not None:
                results["parsed_with_quantity"] += 1
            else:
                results["parsed_without_quantity"] += 1

        parsed_recipes.append(recipe)

    return parsed_recipes, results


def save_parsed_recipes(recipes: list[dict[str, Any]]) -> None:
    """Save parsed recipes to individual JSON files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for recipe in recipes:
        output_path = OUTPUT_DIR / f"{recipe['recipe_id']}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(recipe, f, indent=2, ensure_ascii=False)


def generate_report(results: dict[str, Any]) -> str:
    """Generate a formatted report from parsing results."""
    lines = []
    lines.append("=" * 60)
    lines.append("PHASE 3: INGREDIENT PARSING REPORT")
    lines.append("=" * 60)
    lines.append("")

    lines.append("PROCESSING STATISTICS")
    lines.append("-" * 40)
    lines.append(f"Total recipes: {results['total_files']}")
    lines.append(f"Successfully processed: {results['processed']}")
    lines.append(f"Failed: {results['failed']}")
    lines.append("")

    lines.append("INGREDIENT PARSING RESULTS")
    lines.append("-" * 40)
    lines.append(f"Total ingredients: {results['total_ingredients']}")
    lines.append(f"Parsed with quantity: {results['parsed_with_quantity']}")
    lines.append(f"Parsed without quantity: {results['parsed_without_quantity']}")
    lines.append("")

    if results["total_ingredients"] > 0:
        lines.append("SUCCESS RATES")
        lines.append("-" * 40)
        total_parsed = results["parsed_with_quantity"] + results["parsed_without_quantity"]
        lines.append(
            f"Overall parse rate: {total_parsed / results['total_ingredients'] * 100:.1f}%"
        )
        lines.append(
            f"Quantity parsed rate: {results['parsed_with_quantity'] / results['total_ingredients'] * 100:.1f}%"
        )
        lines.append("")

    if results["failed_files"]:
        lines.append("FAILED FILES")
        lines.append("-" * 40)
        for fname in results["failed_files"][:10]:
            lines.append(f"  {fname}")
        if len(results["failed_files"]) > 10:
            lines.append(f"  ... and {len(results['failed_files']) - 10} more")
        lines.append("")

    lines.append("OUTPUT LOCATION")
    lines.append("-" * 40)
    lines.append(f"Parsed recipes: {OUTPUT_DIR}")
    lines.append("")

    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)


def main() -> None:
    """Run Phase 3 ingredient parsing."""
    print("Phase 3: Ingredient Parsing")
    print("=" * 40)

    # Process all recipes
    print("Processing ingredients...")
    recipes, results = process_all_recipes()

    # Save parsed recipes
    print(f"Saving {len(recipes)} parsed recipes...")
    save_parsed_recipes(recipes)

    # Generate report
    report = generate_report(results)

    # Save report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_PATH}")
    print(f"Parsed recipes saved to: {OUTPUT_DIR}")
    print("\n" + report)


if __name__ == "__main__":
    main()
