"""Dataset download and loading helpers for food classification."""
from __future__ import annotations

from pathlib import Path

from datasets import DatasetDict, load_dataset, load_from_disk

from food_classified.paths import (
    FOOD_CLASSIFIED_ARTIFACTS_DIR,
    FOOD_CLASSIFIED_CACHE_DIR,
    FOOD_CLASSIFIED_PROCESSED_DIR,
    FOOD_CLASSIFIED_RAW_DIR,
)

# Optional: Hugging Face token for faster downloads (set HF_TOKEN in .env)
from config import HF_TOKEN

DATASET_NAME = "Scuccorese/food-ingredients-dataset"
LOCAL_DATASET_DIRNAME = "food_ingredients_dataset"


def dataset_storage_path() -> Path:
    """Return the local on-disk dataset path."""
    return FOOD_CLASSIFIED_RAW_DIR / LOCAL_DATASET_DIRNAME


def ensure_data_directories(base_dir: Path | None = None) -> dict[str, Path]:
    """Create data directories for the module."""
    if base_dir is None:
        raw_dir = FOOD_CLASSIFIED_RAW_DIR
        cache_dir = FOOD_CLASSIFIED_CACHE_DIR
        processed_dir = FOOD_CLASSIFIED_PROCESSED_DIR
        artifacts_dir = FOOD_CLASSIFIED_ARTIFACTS_DIR
    else:
        raw_dir = base_dir / "raw"
        cache_dir = base_dir / "cache"
        processed_dir = base_dir / "processed"
        artifacts_dir = base_dir / "artifacts"

    for path in (raw_dir, cache_dir, processed_dir, artifacts_dir):
        path.mkdir(parents=True, exist_ok=True)

    return {
        "raw": raw_dir,
        "cache": cache_dir,
        "processed": processed_dir,
        "artifacts": artifacts_dir,
    }


def download_dataset() -> Path:
    """Download the Hugging Face dataset and save it locally.

    Uses HF_TOKEN from .env if available for faster authenticated downloads.
    """
    ensure_data_directories()

    # Use token if available for higher rate limits
    if HF_TOKEN:
        dataset = load_dataset(
            DATASET_NAME,
            cache_dir=str(FOOD_CLASSIFIED_CACHE_DIR),
            token=HF_TOKEN,
        )
    else:
        dataset = load_dataset(DATASET_NAME, cache_dir=str(FOOD_CLASSIFIED_CACHE_DIR))

    dataset.save_to_disk(str(dataset_storage_path()))
    return dataset_storage_path()


def load_local_dataset() -> DatasetDict:
    """Load the previously saved local dataset."""
    return load_from_disk(str(dataset_storage_path()))


def inspect_dataset_schema(dataset: DatasetDict) -> dict[str, object]:
    """Return dataset summary for CLI inspection."""
    train_split = dataset["train"]
    return {
        "rows": len(train_split),
        "columns": list(train_split.features.keys()),
    }
