"""Phase 1: Data Assessment & Exploration for Recipe Data Preprocessing.

This script loads and analyzes JSON files from the extracted HTML data
to assess data quality, understand schema patterns, and generate a report.
"""

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


# Configuration
DATA_DIR = Path("data/backup_search/instructions_extracted")
SAMPLE_SIZE = 20
REPORT_PATH = Path("data/process/phase1_report.txt")


def load_json_file(filepath: Path) -> dict[str, Any] | None:
    """Load a single JSON file and return its contents."""
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading {filepath}: {e}")
        return None


def extract_schema_types(data: dict[str, Any]) -> list[str]:
    """Extract all schema types from microdata and json-ld sections."""
    types = []

    # Check microdata
    for item in data.get("microdata", []):
        if "type" in item:
            types.append(item["type"])

    # Check json-ld
    for item in data.get("json-ld", []):
        if "@type" in item:
            t = item["@type"]
            if isinstance(t, list):
                types.extend(t)
            else:
                types.append(t)

        # Check @graph if present
        if "@graph" in item:
            for graph_item in item["@graph"]:
                if "@type" in graph_item:
                    t = graph_item["@type"]
                    if isinstance(t, list):
                        types.extend(t)
                    else:
                        types.append(t)

    return types


def has_recipe_data(data: dict[str, Any]) -> bool:
    """Check if the data contains recipe-related schema types."""
    types = extract_schema_types(data)
    recipe_types = [t for t in types if "Recipe" in str(t)]
    return len(recipe_types) > 0


def extract_recipe_info(data: dict[str, Any]) -> dict[str, Any] | None:
    """Extract recipe information from microdata or json-ld if present."""
    # First check microdata (most common)
    for item in data.get("microdata", []):
        item_type = item.get("type", "")
        if "Recipe" in str(item_type) and "properties" in item:
            props = item["properties"]
            return {
                "name": props.get("name", ""),
                "has_ingredients": "ingredients" in props
                and len(props.get("ingredients", [])) > 0,
                "ingredient_count": len(props.get("ingredients", [])),
                "has_instructions": "recipeInstructions" in props
                and len(props.get("recipeInstructions", [])) > 0,
                "instruction_count": len(props.get("recipeInstructions", [])),
                "has_prep_time": "prepTime" in props,
                "has_cook_time": "cookTime" in props,
                "has_total_time": "totalTime" in props,
                "has_servings": "recipeYield" in props,
                "has_cuisine": "recipeCuisine" in props,
                "has_category": "recipeCategory" in props,
            }

    # Then check json-ld @graph (for files without microdata Recipe)
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
                    return {
                        "name": graph_item.get("name", ""),
                        "has_ingredients": "recipeIngredient" in graph_item
                        and len(graph_item.get("recipeIngredient", [])) > 0,
                        "ingredient_count": len(
                            graph_item.get("recipeIngredient", [])
                        ),
                        "has_instructions": "recipeInstructions" in graph_item
                        and len(graph_item.get("recipeInstructions", [])) > 0,
                        "instruction_count": len(
                            graph_item.get("recipeInstructions", [])
                        ),
                        "has_prep_time": "prepTime" in graph_item,
                        "has_cook_time": "cookTime" in graph_item,
                        "has_total_time": "totalTime" in graph_item,
                        "has_servings": "recipeYield" in graph_item,
                        "has_cuisine": "recipeCuisine" in graph_item,
                        "has_category": "recipeCategory" in graph_item,
                    }

    return None


def analyze_sample_files(filepaths: list[Path]) -> dict[str, Any]:
    """Analyze a sample of files to understand data patterns."""
    results = {
        "total_files": len(filepaths),
        "loaded_successfully": 0,
        "failed_to_load": 0,
        "has_recipe_schema": 0,
        "has_ingredients": 0,
        "has_instructions": 0,
        "has_both": 0,
        "schema_types": Counter(),
        "recipe_details": [],
        "failed_files": [],
    }

    for filepath in filepaths:
        data = load_json_file(filepath)
        if data is None:
            results["failed_to_load"] += 1
            results["failed_files"].append(filepath.name)
            continue

        results["loaded_successfully"] += 1

        # Count schema types
        types = extract_schema_types(data)
        for t in types:
            results["schema_types"][t] += 1

        # Check for recipe data
        if has_recipe_data(data):
            results["has_recipe_schema"] += 1
            recipe_info = extract_recipe_info(data)
            if recipe_info:
                results["recipe_details"].append(recipe_info)
                if recipe_info["has_ingredients"]:
                    results["has_ingredients"] += 1
                if recipe_info["has_instructions"]:
                    results["has_instructions"] += 1
                if recipe_info["has_ingredients"] and recipe_info["has_instructions"]:
                    results["has_both"] += 1

    return results


def generate_report(results: dict[str, Any]) -> str:
    """Generate a formatted report from analysis results."""
    lines = []
    lines.append("=" * 60)
    lines.append("PHASE 1: DATA ASSESSMENT REPORT")
    lines.append("=" * 60)
    lines.append("")

    # File statistics
    lines.append("FILE STATISTICS")
    lines.append("-" * 40)
    lines.append(f"Total files analyzed: {results['total_files']}")
    lines.append(f"Loaded successfully: {results['loaded_successfully']}")
    lines.append(f"Failed to load: {results['failed_to_load']}")
    lines.append("")

    # Recipe statistics
    lines.append("RECIPE DATA STATISTICS")
    lines.append("-" * 40)
    lines.append(f"Files with Recipe schema: {results['has_recipe_schema']}")
    lines.append(f"Files with ingredients: {results['has_ingredients']}")
    lines.append(f"Files with instructions: {results['has_instructions']}")
    lines.append(f"Files with both ingredients AND instructions: {results['has_both']}")
    lines.append("")

    # Success rates
    if results["loaded_successfully"] > 0:
        lines.append("SUCCESS RATES")
        lines.append("-" * 40)
        lines.append(
            f"Recipe schema rate: {results['has_recipe_schema'] / results['loaded_successfully'] * 100:.1f}%"
        )
        lines.append(
            f"Ingredients extraction rate: {results['has_ingredients'] / results['loaded_successfully'] * 100:.1f}%"
        )
        lines.append(
            f"Instructions extraction rate: {results['has_instructions'] / results['loaded_successfully'] * 100:.1f}%"
        )
        lines.append(
            f"Complete data rate: {results['has_both'] / results['loaded_successfully'] * 100:.1f}%"
        )
        lines.append("")

    # Schema types found
    lines.append("SCHEMA TYPES FOUND")
    lines.append("-" * 40)
    for schema_type, count in results["schema_types"].most_common():
        lines.append(f"  {count:4d} x {schema_type}")
    lines.append("")

    # Recipe field analysis
    if results["recipe_details"]:
        lines.append("RECIPE FIELD ANALYSIS")
        lines.append("-" * 40)
        total = len(results["recipe_details"])

        field_counts = {
            "has_prep_time": sum(1 for r in results["recipe_details"] if r["has_prep_time"]),
            "has_cook_time": sum(1 for r in results["recipe_details"] if r["has_cook_time"]),
            "has_total_time": sum(1 for r in results["recipe_details"] if r["has_total_time"]),
            "has_servings": sum(1 for r in results["recipe_details"] if r["has_servings"]),
            "has_cuisine": sum(1 for r in results["recipe_details"] if r["has_cuisine"]),
            "has_category": sum(1 for r in results["recipe_details"] if r["has_category"]),
        }

        for field, count in field_counts.items():
            lines.append(f"  {field}: {count}/{total} ({count / total * 100:.1f}%)")

        # Average counts
        avg_ingredients = sum(r["ingredient_count"] for r in results["recipe_details"]) / total
        avg_instructions = sum(r["instruction_count"] for r in results["recipe_details"]) / total
        lines.append("")
        lines.append(f"Average ingredients per recipe: {avg_ingredients:.1f}")
        lines.append(f"Average instructions per recipe: {avg_instructions:.1f}")
        lines.append("")

    # Failed files
    if results["failed_files"]:
        lines.append("FAILED FILES")
        lines.append("-" * 40)
        for fname in results["failed_files"]:
            lines.append(f"  {fname}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)


def main() -> None:
    """Run Phase 1 data assessment."""
    print("Phase 1: Data Assessment & Exploration")
    print("=" * 40)

    # Ensure output directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Get all JSON files
    all_files = sorted(DATA_DIR.glob("*.json"))
    total_files = len(all_files)
    print(f"Found {total_files} JSON files in {DATA_DIR}")

    # Analyze sample
    print(f"\nAnalyzing sample of {SAMPLE_SIZE} files...")
    sample_files = all_files[:SAMPLE_SIZE]
    sample_results = analyze_sample_files(sample_files)

    print("\nSample Analysis Complete!")
    print(f"  Files with recipe schema: {sample_results['has_recipe_schema']}")
    print(f"  Files with ingredients: {sample_results['has_ingredients']}")
    print(f"  Files with instructions: {sample_results['has_instructions']}")

    # Analyze all files
    print(f"\nAnalyzing all {total_files} files...")
    all_results = analyze_sample_files(all_files)

    # Generate report
    report = generate_report(all_results)

    # Save report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {REPORT_PATH}")
    print("\n" + report)


if __name__ == "__main__":
    main()
