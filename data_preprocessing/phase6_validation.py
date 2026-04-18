"""Phase 6: Validation & Quality Control.

This script audits the recipes_processed.csv from Phase 5, creates a cleaned
"golden" dataset, and generates comprehensive Markdown reports.

═══════════════════════════════════════════════════════════════════════════════
HOW TO RUN THIS FILE
═══════════════════════════════════════════════════════════════════════════════

Option 1: Using uv (Recommended)
    $ uv run python -m data_preprocessing.phase6_validation

Option 2: Using python directly (from project root)
    $ python -m data_preprocessing.phase6_validation

Option 3: Run as standalone script
    $ python data_preprocessing/phase6_validation.py

═══════════════════════════════════════════════════════════════════════════════
INPUT
═══════════════════════════════════════════════════════════════════════════════

Source: data/process/recipes_processed.csv
        (894 recipe records from Phase 5)

Columns: recipe_id, title, ingredients (JSON), instructions (JSON),
         prep_time, cook_time, total_time, servings, cuisine, category,
         extraction_status, ingredient_count, step_count,
         instruction_temperatures, instruction_times, instruction_equipment,
         has_empty_title, has_zero_ingredients, has_zero_steps

═══════════════════════════════════════════════════════════════════════════════
OUTPUT
═══════════════════════════════════════════════════════════════════════════════

1. data/process/recipes_final_validated.csv
   - Cleaned "golden" dataset with only valid records
   - Anomalous rows removed

2. data/process/phase6_summary_report.md
   - Comprehensive Markdown quality report
   - Statistics, anomaly breakdown, coverage metrics

3. data/process/phase6_anomalies.log
   - Machine-readable log listing every dropped recipe_id
   - Exact technical reason for each anomaly

4. data/process/phase6_sample_review.md
   - 15 randomly sampled recipes from cleaned dataset
   - Human-readable for manual sanity checking

═══════════════════════════════════════════════════════════════════════════════
DEPENDENCIES
═══════════════════════════════════════════════════════════════════════════════

Required packages (from pyproject.toml):
    - pandas>=2.0.0

All dependencies should be installed via:
    $ uv sync

═══════════════════════════════════════════════════════════════════════════════
"""

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


# Configuration
INPUT_CSV = Path("data/process/recipes_processed.csv")
OUTPUT_CLEAN_CSV = Path("data/process/recipes_final_validated.csv")
SUMMARY_REPORT_PATH = Path("data/process/phase6_summary_report.md")
ANOMALY_LOG_PATH = Path("data/process/phase6_anomalies.log")
SAMPLE_REVIEW_PATH = Path("data/process/phase6_sample_review.md")
SAMPLE_SIZE = 15


@dataclass
class Anomaly:
    """Record of a single validation anomaly."""

    recipe_id: int
    title: str
    errors: list[str] = field(default_factory=list)


@dataclass
class ValidationStats:
    """Aggregated validation statistics."""

    total_records: int = 0
    valid_records: int = 0
    anomaly_records: int = 0
    duplicate_ids: int = 0
    empty_titles: int = 0
    invalid_ingredients_json: int = 0
    invalid_instructions_json: int = 0
    non_numeric_quantities: int = 0
    empty_instruction_steps: int = 0
    zero_ingredients: int = 0
    zero_steps: int = 0
    total_ingredients: int = 0
    total_steps: int = 0
    with_temperatures: int = 0
    with_times: int = 0
    with_equipment: int = 0
    with_cuisine: int = 0
    with_category: int = 0
    with_prep_time: int = 0
    with_cook_time: int = 0
    with_servings: int = 0


def load_data() -> pd.DataFrame:
    """Load the processed CSV from Phase 5.

    Returns:
        DataFrame with recipe data

    Raises:
        FileNotFoundError: If input CSV doesn't exist
    """
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} records from {INPUT_CSV}")
    return df


def validate_ingredients_json(row: pd.Series) -> list[str]:
    """Validate the ingredients JSON column.

    Checks:
        - Valid JSON syntax
        - Is an array
        - Each item has numeric or null quantity
        - Each item has a non-empty name

    Args:
        row: DataFrame row

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    raw = row.get("ingredients", "")

    try:
        ingredients = json.loads(raw) if isinstance(raw, str) and raw else []
    except json.JSONDecodeError:
        errors.append(f"Invalid JSON in 'ingredients' column")
        return errors

    if not isinstance(ingredients, list):
        errors.append(
            f"'ingredients' JSON is not an array: {type(ingredients).__name__}"
        )
        return errors

    for i, ing in enumerate(ingredients):
        if not isinstance(ing, dict):
            errors.append(f"Ingredient [{i}] is not a dict: {type(ing).__name__}")
            continue

        # Check quantity is numeric or null
        qty = ing.get("quantity")
        if qty is not None and not isinstance(qty, (int, float)):
            errors.append(
                f"Ingredient [{i}] '{ing.get('name', '?')}' has non-numeric quantity: {qty!r}"
            )

        # Check name is non-empty
        name = ing.get("name", "")
        if not name or not isinstance(name, str) or not name.strip():
            errors.append(f"Ingredient [{i}] has empty name")

    return errors


def validate_instructions_json(row: pd.Series) -> list[str]:
    """Validate the instructions JSON column.

    Checks:
        - Valid JSON syntax
        - Is an array
        - No empty string steps

    Args:
        row: DataFrame row

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    raw = row.get("instructions", "")

    try:
        instructions = json.loads(raw) if isinstance(raw, str) and raw else []
    except json.JSONDecodeError:
        errors.append(f"Invalid JSON in 'instructions' column")
        return errors

    if not isinstance(instructions, list):
        errors.append(
            f"'instructions' JSON is not an array: {type(instructions).__name__}"
        )
        return errors

    for i, step in enumerate(instructions):
        if not isinstance(step, str):
            errors.append(
                f"Instruction step [{i}] is not a string: {type(step).__name__}"
            )
            continue
        if not step.strip():
            errors.append(f"Instruction step [{i}] is empty or whitespace only")

    return errors


def validate_row(row: pd.Series) -> list[str]:
    """Run all validations on a single row.

    Args:
        row: DataFrame row

    Returns:
        List of all error messages for this row
    """
    errors = []

    # Title check
    title = row.get("title", "")
    if not isinstance(title, str) or not title.strip():
        errors.append("Empty or missing title")

    # Ingredients validation
    errors.extend(validate_ingredients_json(row))

    # Instructions validation
    errors.extend(validate_instructions_json(row))

    return errors


def audit_dataset(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[Anomaly], ValidationStats]:
    """Run full audit on the dataset.

    Args:
        df: Raw DataFrame from Phase 5

    Returns:
        Tuple of (clean DataFrame, anomalies list, stats)
    """
    stats = ValidationStats(total_records=len(df))

    # Track duplicates
    seen_ids: set[int] = set()
    duplicate_mask = pd.Series(False, index=df.index)
    for idx, row in df.iterrows():
        rid = int(row["recipe_id"])
        if rid in seen_ids:
            duplicate_mask.iloc[idx] = True
        else:
            seen_ids.add(rid)

    stats.duplicate_ids = int(duplicate_mask.sum())

    # Flag empty titles
    empty_title_mask = df["title"].isna() | (df["title"].astype(str).str.strip() == "")
    stats.empty_titles = int(empty_title_mask.sum())

    # Track JSON-level anomalies
    anomalies: list[Anomaly] = []
    valid_indices: list[int] = []

    for idx, row in df.iterrows():
        errors = validate_row(row)

        # Check duplicate
        if duplicate_mask.iloc[idx]:
            errors.append(f"Duplicate recipe_id: {int(row['recipe_id'])}")

        if errors:
            anomalies.append(
                Anomaly(
                    recipe_id=int(row["recipe_id"]),
                    title=str(row.get("title", "")),
                    errors=errors,
                )
            )
        else:
            valid_indices.append(idx)

    # Build clean DataFrame
    clean_df = df.loc[valid_indices].reset_index(drop=True)

    stats.valid_records = len(clean_df)
    stats.anomaly_records = len(anomalies)

    # Count specific anomaly types from error messages
    all_errors = [e for a in anomalies for e in a.errors]
    stats.invalid_ingredients_json = sum(
        1 for e in all_errors if "Invalid JSON in 'ingredients'" in e
    )
    stats.invalid_instructions_json = sum(
        1 for e in all_errors if "Invalid JSON in 'instructions'" in e
    )
    stats.non_numeric_quantities = sum(
        1 for e in all_errors if "non-numeric quantity" in e
    )
    stats.empty_instruction_steps = sum(
        1 for e in all_errors if "empty or whitespace only" in e
    )
    stats.zero_ingredients = int((clean_df["ingredient_count"] == 0).sum())
    stats.zero_steps = int((clean_df["step_count"] == 0).sum())

    # Content statistics from clean data
    stats.total_ingredients = int(clean_df["ingredient_count"].sum())
    stats.total_steps = int(clean_df["step_count"].sum())

    # Metadata coverage
    for col, target_attr in [
        ("instruction_temperatures", "with_temperatures"),
        ("instruction_times", "with_times"),
        ("instruction_equipment", "with_equipment"),
    ]:
        if col in clean_df.columns:
            count = 0
            for val in clean_df[col]:
                try:
                    parsed = json.loads(val) if isinstance(val, str) and val else []
                    if isinstance(parsed, list) and len(parsed) > 0:
                        count += 1
                except (json.JSONDecodeError, TypeError):
                    pass
            setattr(stats, target_attr, count)

    # Other field coverage
    if "cuisine" in clean_df.columns:
        mask = clean_df["cuisine"].notna() & (
            clean_df["cuisine"].astype(str).str.strip() != ""
        )
        stats.with_cuisine = int(mask.sum())
    if "category" in clean_df.columns:
        mask = clean_df["category"].notna() & (
            clean_df["category"].astype(str).str.strip() != ""
        )
        stats.with_category = int(mask.sum())
    for col, attr in [
        ("prep_time", "with_prep_time"),
        ("cook_time", "with_cook_time"),
        ("servings", "with_servings"),
    ]:
        if col in clean_df.columns:
            mask = clean_df[col].notna() & (clean_df[col].astype(str).str.strip() != "")
            setattr(stats, attr, int(mask.sum()))

    return clean_df, anomalies, stats


def save_clean_csv(clean_df: pd.DataFrame) -> None:
    """Save the validated clean dataset.

    Args:
        clean_df: DataFrame with only valid records
    """
    OUTPUT_CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(OUTPUT_CLEAN_CSV, index=False, encoding="utf-8")
    print(f"✓ Saved {len(clean_df)} valid records to {OUTPUT_CLEAN_CSV}")


def save_anomaly_log(anomalies: list[Anomaly]) -> None:
    """Save anomaly log file.

    Args:
        anomalies: List of Anomaly objects
    """
    ANOMALY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ANOMALY_LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"Phase 6 Anomaly Log\n")
        f.write(f"{'=' * 50}\n")
        f.write(f"Total anomalies: {len(anomalies)}\n")
        f.write(f"{'=' * 50}\n\n")

        for anomaly in anomalies:
            f.write(f"recipe_id {anomaly.recipe_id}: ")
            f.write("; ".join(anomaly.errors))
            f.write("\n")

    print(f"✓ Saved anomaly log to {ANOMALY_LOG_PATH}")


def save_summary_report(stats: ValidationStats, anomalies: list[Anomaly]) -> None:
    """Save comprehensive Markdown quality report.

    Args:
        stats: Validation statistics
        anomalies: List of anomalies found
    """
    valid_pct = (
        stats.valid_records / stats.total_records * 100 if stats.total_records else 0
    )
    anomaly_pct = (
        stats.anomaly_records / stats.total_records * 100 if stats.total_records else 0
    )

    avg_ingredients = (
        stats.total_ingredients / stats.valid_records if stats.valid_records else 0
    )
    avg_steps = stats.total_steps / stats.valid_records if stats.valid_records else 0

    lines = [
        "# Phase 6: Validation & Quality Control Report",
        "",
        "## Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| **Input records** | {stats.total_records} |",
        f"| **Valid records** | {stats.valid_records} ({valid_pct:.1f}%) |",
        f"| **Anomalous records** | {stats.anomaly_records} ({anomaly_pct:.1f}%) |",
        f"| **Duplicate IDs** | {stats.duplicate_ids} |",
        "",
        "---",
        "",
        "## Anomaly Breakdown",
        "",
        "| Anomaly Type | Count |",
        "|-------------|-------|",
        f"| Empty titles | {stats.empty_titles} |",
        f"| Invalid ingredients JSON | {stats.invalid_ingredients_json} |",
        f"| Invalid instructions JSON | {stats.invalid_instructions_json} |",
        f"| Non-numeric ingredient quantities | {stats.non_numeric_quantities} |",
        f"| Empty instruction steps | {stats.empty_instruction_steps} |",
        f"| Zero ingredients | {stats.zero_ingredients} |",
        f"| Zero steps | {stats.zero_steps} |",
        f"| Duplicate recipe_ids | {stats.duplicate_ids} |",
        "",
    ]

    # Anomaly details table
    if anomalies:
        lines.append("### Anomalous Recipes Detail")
        lines.append("")
        lines.append("| recipe_id | Title | Errors |")
        lines.append("|-----------|-------|--------|")
        for a in anomalies[:20]:
            title = a.title[:40] + "..." if len(a.title) > 40 else a.title
            errors_str = "; ".join(a.errors)
            if len(errors_str) > 80:
                errors_str = errors_str[:77] + "..."
            lines.append(f"| {a.recipe_id} | {title} | {errors_str} |")
        if len(anomalies) > 20:
            lines.append(f"| ... | ... | _and {len(anomalies) - 20} more_ |")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Content Statistics (Clean Dataset)",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total ingredients | {stats.total_ingredients} |",
            f"| Total instruction steps | {stats.total_steps} |",
            f"| Avg ingredients per recipe | {avg_ingredients:.1f} |",
            f"| Avg steps per recipe | {avg_steps:.1f} |",
            f"| Recipes with zero ingredients | {stats.zero_ingredients} |",
            f"| Recipes with zero steps | {stats.zero_steps} |",
            "",
            "---",
            "",
            "## Metadata Coverage (Clean Dataset)",
            "",
            "| Field | Count | Coverage |",
            "|-------|-------|----------|",
        ]
    )

    coverage_fields = [
        ("Temperatures", stats.with_temperatures),
        ("Times", stats.with_times),
        ("Equipment", stats.with_equipment),
        ("Cuisine", stats.with_cuisine),
        ("Category", stats.with_category),
        ("Prep time", stats.with_prep_time),
        ("Cook time", stats.with_cook_time),
        ("Servings", stats.with_servings),
    ]
    for label, count in coverage_fields:
        pct = count / stats.valid_records * 100 if stats.valid_records else 0
        lines.append(f"| {label} | {count} | {pct:.1f}% |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Output Files",
            "",
            "| File | Description |",
            "|------|-------------|",
            f"| `{OUTPUT_CLEAN_CSV}` | Cleaned dataset ({stats.valid_records} records) |",
            f"| `{ANOMALY_LOG_PATH}` | Dropped recipe IDs and reasons |",
            f"| `{SAMPLE_REVIEW_PATH}` | 15 random recipes for manual review |",
            "",
            "---",
            "",
            f"_Generated by Phase 6 validation script_",
        ]
    )

    SUMMARY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✓ Saved summary report to {SUMMARY_REPORT_PATH}")


def save_sample_review(clean_df: pd.DataFrame) -> None:
    """Save sample review with 15 random recipes in Markdown.

    Args:
        clean_df: Clean DataFrame with valid records
    """
    n = min(SAMPLE_SIZE, len(clean_df))
    sampled = clean_df.sample(n=n, random_state=42)

    lines = [
        "# Phase 6: Sample Review",
        "",
        f"_{n} randomly selected recipes from the validated dataset for manual sanity checking._",
        "",
        "---",
        "",
    ]

    for i, (_, row) in enumerate(sampled.iterrows()):
        rid = int(row["recipe_id"])
        title = str(row["title"])
        servings = str(row.get("servings", ""))
        cuisine = str(row.get("cuisine", ""))
        category = str(row.get("category", ""))
        prep = str(row.get("prep_time", ""))
        cook = str(row.get("cook_time", ""))

        lines.append(f"## {i + 1}. {title}")
        lines.append("")
        lines.append(f"| Field | Value |")
        lines.append(f"|-------|-------|")
        lines.append(f"| **recipe_id** | {rid} |")
        if cuisine and cuisine != "nan":
            lines.append(f"| **cuisine** | {cuisine} |")
        if category and category != "nan":
            lines.append(f"| **category** | {category} |")
        if servings and servings != "nan":
            lines.append(f"| **servings** | {servings} |")
        if prep and prep != "nan":
            lines.append(f"| **prep_time** | {prep} |")
        if cook and cook != "nan":
            lines.append(f"| **cook_time** | {cook} |")
        lines.append("")

        # Ingredients
        try:
            ingredients = json.loads(row["ingredients"])
        except (json.JSONDecodeError, TypeError):
            ingredients = []

        lines.append("### Ingredients")
        lines.append("")
        if ingredients:
            lines.append("| # | Name | Quantity | Unit | Preparation |")
            lines.append("|---|------|----------|------|-------------|")
            for j, ing in enumerate(ingredients, 1):
                name = ing.get("name", "")
                qty = ing.get("quantity", "-")
                if qty is None:
                    qty = "-"
                unit = ing.get("unit", "")
                prep_note = ing.get("preparation", "")
                lines.append(f"| {j} | {name} | {qty} | {unit} | {prep_note} |")
        else:
            lines.append("_No ingredients_")
        lines.append("")

        # Instructions
        try:
            instructions = json.loads(row["instructions"])
        except (json.JSONDecodeError, TypeError):
            instructions = []

        lines.append("### Instructions")
        lines.append("")
        if instructions:
            for j, step in enumerate(instructions, 1):
                lines.append(f"**Step {j}:** {step}  ")
        else:
            lines.append("_No instructions_")
        lines.append("")
        lines.append("---")
        lines.append("")

    SAMPLE_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SAMPLE_REVIEW_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✓ Saved sample review to {SAMPLE_REVIEW_PATH}")


def main() -> None:
    """Run Phase 6 validation & quality control."""
    print("Phase 6: Validation & Quality Control")
    print("=" * 50)
    print()

    # Step 1: Load data
    print("Loading data...")
    df = load_data()

    # Step 2: Audit
    print("Auditing dataset...")
    clean_df, anomalies, stats = audit_dataset(df)

    # Step 3: Save outputs
    print("\nGenerating outputs...")
    save_clean_csv(clean_df)
    save_anomaly_log(anomalies)
    save_summary_report(stats, anomalies)
    save_sample_review(clean_df)

    # Step 4: Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total records:       {stats.total_records}")
    print(
        f"✅ Valid records:    {stats.valid_records} ({stats.valid_records / stats.total_records * 100:.1f}%)"
    )
    print(
        f"❌ Anomalous records: {stats.anomaly_records} ({stats.anomaly_records / stats.total_records * 100:.1f}%)"
    )
    print(f"📋 Output files:")
    print(f"   - {OUTPUT_CLEAN_CSV}")
    print(f"   - {SUMMARY_REPORT_PATH}")
    print(f"   - {ANOMALY_LOG_PATH}")
    print(f"   - {SAMPLE_REVIEW_PATH}")


if __name__ == "__main__":
    main()
