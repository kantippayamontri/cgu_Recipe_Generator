"""Run the full preprocessing pipeline (Phase 1 through Phase 6).

===============================================================================
HOW TO RUN THIS FILE
===============================================================================

Option 1: Using uv (Recommended)
    $ uv run python -m data_preprocessing.full_preprocess

Option 2: Using python directly (from project root)
    $ python -m data_preprocessing.full_preprocess

Option 3: Run as standalone script
    $ python data_preprocessing/full_preprocess.py

===============================================================================
COMMAND-LINE OPTIONS
===============================================================================

Run all phases (default):
    $ uv run python -m data_preprocessing.full_preprocess

Run from a specific phase onward:
    $ uv run python -m data_preprocessing.full_preprocess --from 3

Run up to a specific phase:
    $ uv run python -m data_preprocessing.full_preprocess --to 4

Run a range of phases:
    $ uv run python -m data_preprocessing.full_preprocess --from 2 --to 4

Run a single phase only:
    $ uv run python -m data_preprocessing.full_preprocess --only 5

===============================================================================
PIPELINE OVERVIEW
===============================================================================

Phase 1: Data Assessment & Exploration
    Input:  data/backup_search/instructions_extracted/ (JSON files)
    Output: data/process/phase1_report.txt

Phase 2: Text Extraction & Cleaning
    Input:  data/backup_search/instructions_extracted/ (JSON files)
    Output: data/process/extracted_recipes/ (individual JSON files)

Phase 3: Ingredient Parsing
    Input:  data/process/extracted_recipes/ (JSON files from Phase 2)
    Output: data/process/parsed_ingredients/ (JSON files)

Phase 4: Instruction Processing
    Input:  data/process/parsed_ingredients/ (JSON files from Phase 3)
    Output: data/process/processed_recipes/ (JSON files)

Phase 5: Structured Output Generation
    Input:  data/process/processed_recipes/ (JSON files from Phase 4)
    Output: data/process/recipes_processed.csv

Phase 6: Validation & Quality Control
    Input:  data/process/recipes_processed.csv (from Phase 5)
    Output: data/process/recipes_final_validated.csv
            data/process/phase6_summary_report.md
            data/process/phase6_anomalies.log
            data/process/phase6_sample_review.md

===============================================================================
DEPENDENCIES
===============================================================================

Required packages (from pyproject.toml):
    - pandas>=2.0.0
    - extruct>=0.18.0

All dependencies should be installed via:
    $ uv sync

===============================================================================
"""

import argparse
import sys
import time

from data_preprocessing.phase1_data_assessment import main as phase1_main
from data_preprocessing.phase2_text_extraction import main as phase2_main
from data_preprocessing.phase3_ingredient_parsing import main as phase3_main
from data_preprocessing.phase4_instruction_processing import main as phase4_main
from data_preprocessing.phase5_structure_output import main as phase5_main
from data_preprocessing.phase6_validation import main as phase6_main

PHASES: dict[int, tuple[str, callable]] = {
    1: ("Data Assessment & Exploration", phase1_main),
    2: ("Text Extraction & Cleaning", phase2_main),
    3: ("Ingredient Parsing", phase3_main),
    4: ("Instruction Processing", phase4_main),
    5: ("Structured Output Generation", phase5_main),
    6: ("Validation & Quality Control", phase6_main),
}

MIN_PHASE = min(PHASES)
MAX_PHASE = max(PHASES)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace with start/end phase numbers.
    """
    parser = argparse.ArgumentParser(
        description="Run the full recipe preprocessing pipeline (Phases 1-6).",
    )
    parser.add_argument(
        "--from",
        dest="start",
        type=int,
        default=MIN_PHASE,
        choices=range(MIN_PHASE, MAX_PHASE + 1),
        help="Phase to start from (default: 1)",
    )
    parser.add_argument(
        "--to",
        dest="end",
        type=int,
        default=MAX_PHASE,
        choices=range(MIN_PHASE, MAX_PHASE + 1),
        help="Phase to end at (default: 6)",
    )
    parser.add_argument(
        "--only",
        type=int,
        default=None,
        choices=range(MIN_PHASE, MAX_PHASE + 1),
        help="Run only this single phase",
    )

    args = parser.parse_args()

    if args.only is not None:
        args.start = args.only
        args.end = args.only

    if args.start > args.end:
        parser.error(f"--from ({args.start}) must be <= --to ({args.end})")

    return args


def run_pipeline(start: int, end: int) -> None:
    """Execute preprocessing phases sequentially.

    Args:
        start: First phase number to run (inclusive).
        end: Last phase number to run (inclusive).
    """
    phases_to_run = {k: v for k, v in PHASES.items() if start <= k <= end}
    total = len(phases_to_run)

    print("=" * 60)
    print("RECIPE PREPROCESSING PIPELINE")
    print("=" * 60)
    print(f"Running phase(s): {start} -> {end}  ({total} phase(s))")
    print("=" * 60)
    print()

    timings: dict[int, float] = {}
    pipeline_start = time.perf_counter()

    for phase_num, (description, phase_fn) in phases_to_run.items():
        header = f"PHASE {phase_num}/{MAX_PHASE}: {description}"
        print("\n" + "#" * 60)
        print(f"# {header}")
        print("#" * 60 + "\n")

        phase_start = time.perf_counter()
        try:
            phase_fn()
        except Exception as exc:
            elapsed = time.perf_counter() - phase_start
            print(f"\nPhase {phase_num} FAILED after {elapsed:.1f}s: {exc}")
            print("Pipeline aborted.")
            sys.exit(1)

        elapsed = time.perf_counter() - phase_start
        timings[phase_num] = elapsed
        print(f"\nPhase {phase_num} completed in {elapsed:.1f}s")

    pipeline_elapsed = time.perf_counter() - pipeline_start

    # Summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"{'Phase':<8} {'Description':<40} {'Time':>8}")
    print("-" * 60)
    for phase_num in phases_to_run:
        description = PHASES[phase_num][0]
        t = timings[phase_num]
        print(f"{phase_num:<8} {description:<40} {t:>7.1f}s")
    print("-" * 60)
    print(f"{'Total':<49} {pipeline_elapsed:>7.1f}s")


def main() -> None:
    """Entry point for the full preprocessing pipeline."""
    args = parse_args()
    run_pipeline(args.start, args.end)


if __name__ == "__main__":
    main()
