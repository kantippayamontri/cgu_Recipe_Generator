"""Phase 4: Instruction Processing for Recipe Data Preprocessing.

This script extracts and cleans cooking instructions:
- Parse structured HowToStep objects
- Split text blocks into individual steps
- Remove step numbers and clean whitespace
- Extract metadata (temperatures, times, equipment)
"""

import json
import re
from pathlib import Path
from typing import Any


# Configuration
INPUT_DIR = Path("data/process/parsed_ingredients")
OUTPUT_DIR = Path("data/process/processed_recipes")
REPORT_PATH = Path("data/process/phase4_report.txt")

# Patterns for metadata extraction
TEMPERATURE_PATTERN = re.compile(
    r"(\d+)\s*°\s*(F|C|f|c)|"
    r"(\d+)\s*(degrees?|deg)\s*(Fahrenheit|Celsius|f|c)?|"
    r"(low|medium|high|medium-low|medium-high)\s*(heat)?",
    re.IGNORECASE,
)

TIME_PATTERN = re.compile(
    r"(\d+)\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)|"
    r"(a few minutes|several minutes|overnight)|"
    r"(until \w+|for about \d+)",
    re.IGNORECASE,
)

EQUIPMENT_PATTERN = re.compile(
    r"\b(oven|stove|microwave|blender|food processor|mixing bowl|"
    r"baking sheet|pan|skillet|pot|dutch oven|slow cooker|instant pot|"
    r"air fryer|grill|griddle|wok|saucepan|frying pan|cookie sheet|"
    r"casserole dish|roasting pan|pressure cooker|rice cooker|"
    r"whisk|spatula|wooden spoon|ladle|tongs|knife|cutting board|"
    r"measuring cup|measuring spoon|colander|strainer|sieve|"
    r"rolling pin|pastry brush|grater|peeler|knife|mandoline)\b",
    re.IGNORECASE,
)

# Step number patterns to remove
STEP_NUMBER_PATTERNS = [
    re.compile(r"^step\s*\d+[:.)\-]*\s*", re.IGNORECASE),
    re.compile(r"^\d+[:.)\-]+\s*"),
    re.compile(r"^\(\d+\)\s*"),
]


def clean_instruction(text: str) -> str:
    """Clean a single instruction step."""
    if not isinstance(text, str):
        text = str(text)

    text = text.strip()

    # Remove step numbers
    for pattern in STEP_NUMBER_PATTERNS:
        text = pattern.sub("", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing whitespace and punctuation
    text = text.strip(" -:;")

    return text


def split_text_into_steps(text: str) -> list[str]:
    """Split a text block into individual steps."""
    if not text:
        return []

    # Split on common step delimiters
    # Look for patterns like "1." "Step 1:" or just periods followed by capital letters
    delimiters = [
        r"(?:Step\s*\d+[:.)\-]*)",  # Step 1: or Step 1.
        r"(?:^\d+[:.)\-]+)",  # 1. or 1) at start
        r"(?<=\.)\s+(?=[A-Z])",  # Period followed by space and capital letter
        r"(?<=\;)\s+",  # Semicolon
    ]

    # Try to split on step indicators first
    pattern = "|".join(delimiters[:2])
    steps = re.split(pattern, text, flags=re.IGNORECASE | re.MULTILINE)

    # If no splits were made, try splitting on periods
    if len(steps) == 1 and len(text) > 200:
        steps = re.split(r"(?<=\.)\s+(?=[A-Z])", text)

    # Clean each step
    cleaned_steps = []
    for step in steps:
        cleaned = clean_instruction(step)
        if cleaned and len(cleaned) > 10:  # Filter out very short fragments
            cleaned_steps.append(cleaned)

    return cleaned_steps


def extract_metadata(instruction: str) -> dict[str, list[str]]:
    """Extract metadata from instruction text."""
    metadata = {
        "temperatures": [],
        "times": [],
        "equipment": [],
    }

    # Extract temperatures
    for match in TEMPERATURE_PATTERN.finditer(instruction):
        temp = match.group(0)
        if temp:
            metadata["temperatures"].append(temp)

    # Extract times
    for match in TIME_PATTERN.finditer(instruction):
        time_str = match.group(0)
        if time_str:
            metadata["times"].append(time_str)

    # Extract equipment
    for match in EQUIPMENT_PATTERN.finditer(instruction):
        equipment = match.group(0)
        if equipment:
            metadata["equipment"].append(equipment.lower())

    # Remove duplicates while preserving order
    metadata["temperatures"] = list(dict.fromkeys(metadata["temperatures"]))
    metadata["times"] = list(dict.fromkeys(metadata["times"]))
    metadata["equipment"] = list(dict.fromkeys(metadata["equipment"]))

    return metadata


def process_instructions(instructions: list[str]) -> dict[str, Any]:
    """Process all instructions for a recipe."""
    processed_steps = []
    all_metadata = {
        "temperatures": [],
        "times": [],
        "equipment": [],
    }

    for instruction in instructions:
        # Clean the instruction
        cleaned = clean_instruction(instruction)
        if not cleaned:
            continue

        # Split into steps if it's a long text block
        if len(cleaned) > 200 and (". " in cleaned or "; " in cleaned):
            steps = split_text_into_steps(cleaned)
        else:
            steps = [cleaned]

        for step in steps:
            metadata = extract_metadata(step)

            processed_steps.append(
                {
                    "text": step,
                    "metadata": metadata,
                }
            )

            # Aggregate metadata
            all_metadata["temperatures"].extend(metadata["temperatures"])
            all_metadata["times"].extend(metadata["times"])
            all_metadata["equipment"].extend(metadata["equipment"])

    # Remove duplicates from aggregated metadata
    all_metadata["temperatures"] = list(dict.fromkeys(all_metadata["temperatures"]))
    all_metadata["times"] = list(dict.fromkeys(all_metadata["times"]))
    all_metadata["equipment"] = list(dict.fromkeys(all_metadata["equipment"]))

    return {
        "steps": processed_steps,
        "step_count": len(processed_steps),
        "metadata": all_metadata,
    }


def process_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    """Process a single recipe's instructions."""
    instructions = recipe.get("instructions", [])

    if not instructions:
        recipe["processed_instructions"] = {
            "steps": [],
            "step_count": 0,
            "metadata": {"temperatures": [], "times": [], "equipment": []},
        }
        recipe["instruction_status"] = "no_instructions"
        return recipe

    processed = process_instructions(instructions)
    recipe["processed_instructions"] = processed
    recipe["instruction_status"] = (
        "success" if processed["step_count"] > 0 else "failed"
    )

    return recipe


def process_all_recipes() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Process all recipes and their instructions."""
    all_files = sorted(INPUT_DIR.glob("*.json"))

    results = {
        "total_files": len(all_files),
        "processed": 0,
        "failed": 0,
        "no_instructions": 0,
        "total_steps": 0,
        "with_temperatures": 0,
        "with_times": 0,
        "with_equipment": 0,
        "failed_files": [],
    }

    processed_recipes = []

    for filepath in all_files:
        try:
            with open(filepath, encoding="utf-8") as f:
                recipe = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            results["failed"] += 1
            results["failed_files"].append(filepath.name)
            continue

        recipe = process_recipe(recipe)

        results["processed"] += 1

        if recipe["instruction_status"] == "no_instructions":
            results["no_instructions"] += 1
        elif recipe["instruction_status"] == "success":
            results["total_steps"] += recipe["processed_instructions"]["step_count"]

            metadata = recipe["processed_instructions"]["metadata"]
            if metadata["temperatures"]:
                results["with_temperatures"] += 1
            if metadata["times"]:
                results["with_times"] += 1
            if metadata["equipment"]:
                results["with_equipment"] += 1

        processed_recipes.append(recipe)

    return processed_recipes, results


def save_processed_recipes(recipes: list[dict[str, Any]]) -> None:
    """Save processed recipes to individual JSON files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for recipe in recipes:
        output_path = OUTPUT_DIR / f"{recipe['recipe_id']}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(recipe, f, indent=2, ensure_ascii=False)


def generate_report(results: dict[str, Any]) -> str:
    """Generate a formatted report from processing results."""
    lines = []
    lines.append("=" * 60)
    lines.append("PHASE 4: INSTRUCTION PROCESSING REPORT")
    lines.append("=" * 60)
    lines.append("")

    lines.append("PROCESSING STATISTICS")
    lines.append("-" * 40)
    lines.append(f"Total recipes: {results['total_files']}")
    lines.append(f"Successfully processed: {results['processed']}")
    lines.append(f"Failed: {results['failed']}")
    lines.append(f"No instructions: {results['no_instructions']}")
    lines.append("")

    lines.append("INSTRUCTION RESULTS")
    lines.append("-" * 40)
    lines.append(f"Total steps extracted: {results['total_steps']}")
    if results["processed"] > 0:
        avg_steps = results["total_steps"] / results["processed"]
        lines.append(f"Average steps per recipe: {avg_steps:.1f}")
    lines.append("")

    lines.append("METADATA EXTRACTION")
    lines.append("-" * 40)
    lines.append(f"Recipes with temperatures: {results['with_temperatures']}")
    lines.append(f"Recipes with times: {results['with_times']}")
    lines.append(f"Recipes with equipment: {results['with_equipment']}")
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
    lines.append(f"Processed recipes: {OUTPUT_DIR}")
    lines.append("")

    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)


def main() -> None:
    """Run Phase 4 instruction processing."""
    print("Phase 4: Instruction Processing")
    print("=" * 40)

    # Process all recipes
    print("Processing instructions...")
    recipes, results = process_all_recipes()

    # Save processed recipes
    print(f"Saving {len(recipes)} processed recipes...")
    save_processed_recipes(recipes)

    # Generate report
    report = generate_report(results)

    # Save report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_PATH}")
    print(f"Processed recipes saved to: {OUTPUT_DIR}")
    print("\n" + report)


if __name__ == "__main__":
    main()
