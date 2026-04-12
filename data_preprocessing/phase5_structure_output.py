"""Phase 5: Structured Output Generation.

This script generates the final processed CSV from individual recipe JSON files.
Creates a unified dataset with structured recipe data for downstream tasks.

═══════════════════════════════════════════════════════════════════════════════
HOW TO RUN THIS FILE
═══════════════════════════════════════════════════════════════════════════════

Option 1: Using uv (Recommended)
    $ uv run python -m data_preprocessing.phase5_structure_output

Option 2: Using python directly (from project root)
    $ python -m data_preprocessing.phase5_structure_output

Option 3: Run as standalone script
    $ python data_preprocessing/phase5_structure_output.py

═══════════════════════════════════════════════════════════════════════════════
INPUT
═══════════════════════════════════════════════════════════════════════════════

Source: data/process/processed_recipes/
        (894 individual JSON files from Phase 4)

Each JSON contains:
    - recipe_id: Unique identifier
    - title: Recipe name
    - parsed_ingredients: Structured ingredient data
    - processed_instructions: Cleaned instruction steps with metadata
    - prep_time, cook_time, total_time: ISO 8601 duration format
    - servings: Number of servings
    - cuisine: Recipe cuisine type
    - category: Recipe category (e.g., dinner, lunch)

═══════════════════════════════════════════════════════════════════════════════
OUTPUT
═══════════════════════════════════════════════════════════════════════════════

1. data/process/recipes_processed.csv
   - Unified dataset with recipe records
   - Columns include extraction_status, ingredient_count, step_count,
     instruction_temperatures, instruction_times, instruction_equipment,
     and quality flags for Phase 6 validation

2. data/process/phase5_report.txt
   - Processing statistics
   - Success rates by extraction status
   - Content statistics (avg ingredients, steps)
   - Quality signals for Phase 6 (empty titles, zero ingredients, etc.)
   - Sample recipes by status

═══════════════════════════════════════════════════════════════════════════════
DEPENDENCIES
═══════════════════════════════════════════════════════════════════════════════

Required packages (from pyproject.toml):
    - pandas>=2.0.0
    - tqdm (for progress bars)

All dependencies should be installed via:
    $ uv sync

═══════════════════════════════════════════════════════════════════════════════
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from tqdm import tqdm


# Configuration
INPUT_DIR = Path("data/process/processed_recipes")
OUTPUT_CSV = Path("data/process/recipes_processed.csv")
REPORT_PATH = Path("data/process/phase5_report.txt")


@dataclass
class RecipeRecord:
    """Structured recipe record for CSV output."""

    recipe_id: int
    title: str
    ingredients: str
    instructions: str
    prep_time: str
    cook_time: str
    total_time: str
    servings: str
    cuisine: str
    category: str
    extraction_status: str
    ingredient_count: int
    step_count: int
    instruction_temperatures: str
    instruction_times: str
    instruction_equipment: str
    has_empty_title: bool
    has_zero_ingredients: bool
    has_zero_steps: bool
    has_validation_errors: bool


@dataclass
class ValidationResult:
    """Validation result for a recipe."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)


def validate_recipe_structure(recipe: dict[str, Any]) -> ValidationResult:
    """Validate upstream data structure to catch issues early.

    Args:
        recipe: Recipe dictionary from JSON

    Returns:
        ValidationResult with validity status and error messages
    """
    errors = []

    # Validate parsed_ingredients is a list
    parsed_ingredients = recipe.get("parsed_ingredients")
    if parsed_ingredients is not None and not isinstance(parsed_ingredients, list):
        errors.append(f"parsed_ingredients is not a list: {type(parsed_ingredients)}")

    # Validate processed_instructions["steps"] is a list
    processed_instructions = recipe.get("processed_instructions", {})
    if processed_instructions and not isinstance(processed_instructions, dict):
        errors.append(
            "processed_instructions is not a dict: "
            f"{type(processed_instructions)}"
        )
    elif processed_instructions:
        steps = processed_instructions.get("steps")
        if steps is not None and not isinstance(steps, list):
            errors.append(
                f"processed_instructions['steps'] is not a list: {type(steps)}"
            )

    # Validate title is present
    title = recipe.get("title", "")
    if not title or not isinstance(title, str):
        errors.append(f"title is empty or invalid: {title!r}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def determine_extraction_status(
    has_empty_title: bool,
    has_zero_ingredients: bool,
    has_zero_steps: bool,
) -> str:
    """Determine extraction status based on data completeness.

    Args:
        has_empty_title: Whether title is empty
        has_zero_ingredients: Whether there are no ingredients
        has_zero_steps: Whether there are no instruction steps

    Returns:
        Status: "success", "partial", or "failed"
    """
    # Flag recipes with empty title as partial
    if has_empty_title:
        return "partial"

    has_ingredients = not has_zero_ingredients
    has_instructions = not has_zero_steps

    if has_ingredients and has_instructions:
        return "success"
    elif has_ingredients or has_instructions:
        return "partial"
    else:
        return "failed"


def sanitize_recipe_structure(
    recipe: dict[str, Any],
) -> tuple[dict[str, Any], ValidationResult]:
    """Normalize malformed upstream fields into safe defaults.

    Args:
        recipe: Raw recipe dictionary from JSON

    Returns:
        Tuple of sanitized recipe data and validation details
    """
    validation = validate_recipe_structure(recipe)
    sanitized = dict(recipe)

    title = sanitized.get("title", "")
    if not isinstance(title, str):
        sanitized["title"] = ""

    parsed_ingredients = sanitized.get("parsed_ingredients", [])
    if parsed_ingredients is None:
        sanitized["parsed_ingredients"] = []
    elif not isinstance(parsed_ingredients, list):
        sanitized["parsed_ingredients"] = []
    else:
        sanitized["parsed_ingredients"] = [
            item for item in parsed_ingredients if isinstance(item, dict)
        ]

    processed_instructions = sanitized.get("processed_instructions", {})
    if not isinstance(processed_instructions, dict):
        sanitized["processed_instructions"] = {}
    else:
        steps = processed_instructions.get("steps", [])
        if not isinstance(steps, list):
            steps = []

        metadata = processed_instructions.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        sanitized["processed_instructions"] = {
            **processed_instructions,
            "steps": steps,
            "metadata": metadata,
        }

    return sanitized, validation


def serialize_ingredients(ingredients: list[dict[str, Any]]) -> str:
    """Serialize parsed ingredients to compact JSON string.

    Args:
        ingredients: List of ingredient dictionaries

    Returns:
        JSON string representation
    """
    # Clean up ingredients - remove internal tracking fields
    cleaned = []
    for ing in ingredients:
        cleaned.append(
            {
                "name": ing.get("name", ""),
                "quantity": ing.get("quantity"),
                "unit": ing.get("unit", ""),
                "preparation": ing.get("preparation", ""),
            }
        )
    return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))


def serialize_instructions(processed_instructions: dict[str, Any]) -> str:
    """Serialize instruction steps to compact JSON string.

    Args:
        processed_instructions: Dictionary with steps and metadata

    Returns:
        JSON string of instruction texts
    """
    steps = processed_instructions.get("steps", [])
    # Extract just the text from each step
    texts = [step.get("text", "") for step in steps if step.get("text")]
    return json.dumps(texts, ensure_ascii=False, separators=(",", ":"))


def extract_instruction_metadata(
    processed_instructions: dict[str, Any],
) -> dict[str, Any]:
    """Extract metadata from processed instructions.

    Args:
        processed_instructions: Dictionary with steps and metadata

    Returns:
        Dictionary with temperatures, times, equipment as JSON strings
    """
    metadata = processed_instructions.get("metadata", {})
    return {
        "temperatures": json.dumps(
            metadata.get("temperatures", []),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "times": json.dumps(
            metadata.get("times", []),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        "equipment": json.dumps(
            metadata.get("equipment", []),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }


def process_recipe(filepath: Path) -> RecipeRecord | None:
    """Process a single recipe JSON file.

    Args:
        filepath: Path to recipe JSON file

    Returns:
        RecipeRecord if successful, None otherwise
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            recipe = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading {filepath}: {e}")
        return None

    recipe, validation = sanitize_recipe_structure(recipe)
    if not validation.is_valid:
        print(f"Validation errors in {filepath.name}: {validation.errors}")

    # Extract recipe_id with validation
    recipe_id_raw = recipe.get("recipe_id") or filepath.stem
    try:
        recipe_id = int(recipe_id_raw)
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid recipe_id '{recipe_id_raw}' in {filepath.name}: {e}")
        return None  # Count as failed file

    # Calculate quality signals
    title = recipe.get("title", "")
    has_empty_title = not title or not isinstance(title, str)

    parsed_ingredients = recipe.get("parsed_ingredients", [])
    has_zero_ingredients = len(parsed_ingredients) == 0

    processed_instructions = recipe.get("processed_instructions", {})
    has_zero_steps = processed_instructions.get("step_count", 0) == 0

    # Determine extraction status with quality signals
    status = determine_extraction_status(
        has_empty_title, has_zero_ingredients, has_zero_steps
    )

    # Serialize ingredients
    ingredients_json = serialize_ingredients(parsed_ingredients)
    ingredient_count = len(parsed_ingredients)

    # Serialize instructions
    instructions_json = serialize_instructions(processed_instructions)
    step_count = processed_instructions.get("step_count", 0)

    # Extract instruction metadata for CSV columns
    metadata = extract_instruction_metadata(processed_instructions)

    return RecipeRecord(
        recipe_id=recipe_id,
        title=title,
        ingredients=ingredients_json,
        instructions=instructions_json,
        prep_time=recipe.get("prep_time", ""),
        cook_time=recipe.get("cook_time", ""),
        total_time=recipe.get("total_time", ""),
        servings=str(recipe.get("servings", "")),
        cuisine=recipe.get("cuisine", ""),
        category=recipe.get("category", ""),
        extraction_status=status,
        ingredient_count=ingredient_count,
        step_count=step_count,
        instruction_temperatures=metadata["temperatures"],
        instruction_times=metadata["times"],
        instruction_equipment=metadata["equipment"],
        has_empty_title=has_empty_title,
        has_zero_ingredients=has_zero_ingredients,
        has_zero_steps=has_zero_steps,
        has_validation_errors=not validation.is_valid,
    )


def process_all_recipes() -> tuple[list[RecipeRecord], dict[str, Any]]:
    """Process all recipe JSON files.

    Returns:
        Tuple of (list of RecipeRecords, statistics dict)
    """
    all_files = sorted(INPUT_DIR.glob("*.json"))
    total_files = len(all_files)

    print(f"Found {total_files} recipe files to process\n")

    records = []
    seen_ids: set[int] = set()
    duplicate_ids: list[int] = []

    stats = {
        "total_files": total_files,
        "processed": 0,
        "failed": 0,
        "success": 0,
        "partial": 0,
        "failed_status": 0,
        "total_ingredients": 0,
        "total_steps": 0,
        # Phase 6 quality signals
        "empty_titles": 0,
        "zero_ingredients": 0,
        "zero_steps": 0,
        "duplicate_ids": 0,
        "validation_errors": 0,
        "failed_files": [],
    }

    for filepath in tqdm(all_files, desc="Processing recipes", unit="recipe"):
        record = process_recipe(filepath)

        if record is None:
            stats["failed"] += 1
            stats["failed_files"].append(filepath.name)
            continue

        # Check for duplicate IDs
        if record.recipe_id in seen_ids:
            stats["duplicate_ids"] += 1
            duplicate_ids.append(record.recipe_id)
            continue
        seen_ids.add(record.recipe_id)

        stats["processed"] += 1
        stats["total_ingredients"] += record.ingredient_count
        stats["total_steps"] += record.step_count

        # Track quality signals
        if record.has_empty_title:
            stats["empty_titles"] += 1
        if record.has_zero_ingredients:
            stats["zero_ingredients"] += 1
        if record.has_zero_steps:
            stats["zero_steps"] += 1
        if record.has_validation_errors:
            stats["validation_errors"] += 1

        if record.extraction_status == "success":
            stats["success"] += 1
        elif record.extraction_status == "partial":
            stats["partial"] += 1
        else:
            stats["failed_status"] += 1

        records.append(record)

    if duplicate_ids:
        print(
            f"\n⚠️  Warning: Found {len(duplicate_ids)} duplicate recipe_ids: {duplicate_ids[:10]}"
        )

    return records, stats


def save_to_csv(records: list[RecipeRecord]) -> None:
    """Save recipe records to CSV file using dataclasses.asdict().

    Args:
        records: List of RecipeRecord objects
    """
    # Convert to list of dictionaries using dataclasses.asdict()
    data = [asdict(record) for record in records]

    # Create DataFrame and save
    df = pd.DataFrame(data)

    # Ensure output directory exists
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    print(f"✓ Saved {len(records)} recipes to {OUTPUT_CSV}")


def generate_report(records: list[RecipeRecord], stats: dict[str, Any]) -> str:
    """Generate formatted report from processing results.

    Args:
        records: List of processed RecipeRecords
        stats: Processing statistics

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("PHASE 5: STRUCTURED OUTPUT GENERATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    lines.append("PROCESSING STATISTICS")
    lines.append("-" * 40)
    lines.append(f"Total files found: {stats['total_files']}")
    lines.append(f"Successfully processed: {stats['processed']}")
    lines.append(f"Failed to load: {stats['failed']}")
    lines.append(f"Duplicate IDs skipped: {stats['duplicate_ids']}")
    lines.append("")

    lines.append("EXTRACTION STATUS BREAKDOWN")
    lines.append("-" * 40)
    lines.append(f"✅ Success (complete data): {stats['success']}")
    lines.append(f"⚠️  Partial (incomplete data): {stats['partial']}")
    lines.append(f"❌ Failed (no usable data): {stats['failed_status']}")
    lines.append("")

    if stats["processed"] > 0:
        lines.append("SUCCESS RATES")
        lines.append("-" * 40)
        success_rate = stats["success"] / stats["processed"] * 100
        partial_rate = stats["partial"] / stats["processed"] * 100
        failed_rate = stats["failed_status"] / stats["processed"] * 100
        lines.append(f"Complete data: {success_rate:.1f}%")
        lines.append(f"Partial data: {partial_rate:.1f}%")
        lines.append(f"Failed: {failed_rate:.1f}%")
        lines.append("")

    lines.append("CONTENT STATISTICS")
    lines.append("-" * 40)
    lines.append(f"Total ingredients: {stats['total_ingredients']}")
    lines.append(f"Total instruction steps: {stats['total_steps']}")
    if stats["processed"] > 0:
        avg_ingredients = stats["total_ingredients"] / stats["processed"]
        avg_steps = stats["total_steps"] / stats["processed"]
        lines.append(f"Avg ingredients per recipe: {avg_ingredients:.1f}")
        lines.append(f"Avg steps per recipe: {avg_steps:.1f}")
    lines.append("")

    # Phase 6 quality signals
    lines.append("QUALITY SIGNALS (for Phase 6 validation)")
    lines.append("-" * 40)
    lines.append(f"Recipes with empty titles: {stats['empty_titles']}")
    lines.append(f"Recipes with zero ingredients: {stats['zero_ingredients']}")
    lines.append(f"Recipes with zero steps: {stats['zero_steps']}")
    lines.append(f"Duplicate recipe_ids found: {stats['duplicate_ids']}")
    lines.append(f"Recipes with validation errors: {stats['validation_errors']}")
    lines.append("")

    lines.append("OUTPUT FILES")
    lines.append("-" * 40)
    lines.append(f"CSV file: {OUTPUT_CSV}")
    lines.append(f"Total records: {len(records)}")
    lines.append("")

    lines.append("CSV COLUMNS")
    lines.append("-" * 40)
    lines.append("- recipe_id: Unique identifier")
    lines.append("- title: Recipe name")
    lines.append("- ingredients: JSON array of parsed ingredients")
    lines.append("- instructions: JSON array of instruction steps")
    lines.append("- prep_time, cook_time, total_time: ISO 8601 durations")
    lines.append("- servings: Number of servings")
    lines.append("- cuisine: Recipe cuisine")
    lines.append("- category: Recipe category")
    lines.append("- extraction_status: success/partial/failed")
    lines.append("- ingredient_count, step_count: Counts")
    lines.append("- instruction_temperatures: JSON array of temps")
    lines.append("- instruction_times: JSON array of time references")
    lines.append("- instruction_equipment: JSON array of equipment")
    lines.append(
        "- has_empty_title, has_zero_ingredients, has_zero_steps: Quality flags"
    )
    lines.append("- has_validation_errors: Upstream structure needed sanitizing")
    lines.append("")

    # Sample recipes by status
    lines.append("SAMPLE RECIPES BY STATUS")
    lines.append("-" * 40)

    success_samples = [r for r in records if r.extraction_status == "success"][:3]
    if success_samples:
        lines.append("")
        lines.append("✅ SUCCESS (sample):")
        for r in success_samples:
            lines.append(
                f"  - {r.title} ({r.ingredient_count} ingredients, {r.step_count} steps)"
            )

    partial_samples = [r for r in records if r.extraction_status == "partial"][:3]
    if partial_samples:
        lines.append("")
        lines.append("⚠️  PARTIAL (sample):")
        for r in partial_samples:
            lines.append(
                f"  - {r.title} ({r.ingredient_count} ingredients, {r.step_count} steps)"
            )

    if stats["failed_files"]:
        lines.append("")
        lines.append("FAILED FILES")
        lines.append("-" * 40)
        for fname in stats["failed_files"][:10]:
            lines.append(f"  {fname}")
        if len(stats["failed_files"]) > 10:
            lines.append(f"  ... and {len(stats['failed_files']) - 10} more")

    lines.append("")
    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)


def save_report(report: str) -> None:
    """Save report to file.

    Args:
        report: Report content string
    """
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✓ Report saved to {REPORT_PATH}")


def main() -> None:
    """Run Phase 5 structured output generation."""
    print("Phase 5: Structured Output Generation")
    print("=" * 50)
    print()

    # Process all recipes
    print("Processing recipes...")
    records, stats = process_all_recipes()

    if not records:
        print("\nNo recipes were processed successfully!")
        return

    # Save to CSV
    print("\nSaving to CSV...")
    save_to_csv(records)

    # Generate and save report
    print("\nGenerating report...")
    report = generate_report(records, stats)
    save_report(report)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total processed: {stats['processed']}")
    print(f"✅ Success: {stats['success']}")
    print(f"⚠️  Partial: {stats['partial']}")
    print(f"❌ Failed: {stats['failed_status']}")
    print(
        f"📊 Quality issues: {stats['empty_titles']} empty titles, "
        f"{stats['zero_ingredients']} zero ingredients, "
        f"{stats['zero_steps']} zero steps"
    )
    print(f"\nOutput: {OUTPUT_CSV}")
    print(f"Records: {len(records)}")

    # Print full report
    print("\n" + report)


if __name__ == "__main__":
    main()
