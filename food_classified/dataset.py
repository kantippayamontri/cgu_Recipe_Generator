"""Dataset preparation for ingredient image classification."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np
import tensorflow as tf
from datasets import Dataset, DatasetDict
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from food_classified.paths import FOOD_CLASSIFIED_PROCESSED_DIR


def build_label_mapping(labels: Iterable[str]) -> dict[str, int]:
    """Build deterministic ingredient-to-index mapping."""
    unique_labels = sorted(set(labels))
    return {label: index for index, label in enumerate(unique_labels)}


def filter_rare_ingredients(
    rows: list[dict[str, object]],
    min_samples: int = 3,
) -> list[dict[str, object]]:
    """Drop classes with too few samples for stable splitting."""
    counts = Counter(str(row["ingredient"]) for row in rows)
    return [
        row for row in rows if counts[str(row["ingredient"])] >= min_samples
    ]


def prepare_dataset_splits(
    dataset: DatasetDict,
    min_samples_per_class: int = 3,
    validation_fraction: float = 0.1,
    test_fraction: float = 0.1,
    seed: int = 42,
) -> tuple[DatasetDict, dict[str, int]]:
    """Create deterministic train/validation/test splits with ingredient labels.

    Args:
        dataset: Hugging Face DatasetDict with 'train' split.
        min_samples_per_class: Minimum samples per class to keep.
        validation_fraction: Fraction of training data for validation.
        test_fraction: Fraction of data for final test holdout.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (splits DatasetDict, label_mapping dict).
    """
    train = dataset["train"]
    rows = [train[index] for index in range(len(train))]

    # Filter rare ingredients
    rows = filter_rare_ingredients(rows, min_samples=min_samples_per_class)

    # Build label mapping
    labels = [str(row["ingredient"]) for row in rows]
    label_mapping = build_label_mapping(labels)

    # Create normalized dataset
    normalized_rows = []
    for row in rows:
        normalized_rows.append(
            {
                "image": row["image"],
                "ingredient": str(row["ingredient"]),
                "label_id": label_mapping[str(row["ingredient"])],
            }
        )

    full_dataset = Dataset.from_list(normalized_rows)

    # First split: train vs test
    temp = full_dataset.train_test_split(test_size=test_fraction, seed=seed)

    # Second split: train vs validation from remaining train
    remaining_validation_fraction = validation_fraction / (1.0 - test_fraction)
    train_valid = temp["train"].train_test_split(
        test_size=remaining_validation_fraction,
        seed=seed,
    )

    return (
        DatasetDict(
            {
                "train": train_valid["train"],
                "validation": train_valid["test"],
                "test": temp["test"],
            }
        ),
        label_mapping,
    )


def save_processed_splits(splits: DatasetDict, output_dir: Path | None = None) -> None:
    """Persist processed splits locally."""
    if output_dir is None:
        output_dir = FOOD_CLASSIFIED_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    splits.save_to_disk(str(output_dir / "splits"))


def image_size_for_mobilenet() -> tuple[int, int]:
    """Return MobileNet input image size."""
    return (224, 224)


def preprocess_example(example: dict[str, object]) -> tuple[np.ndarray, int]:
    """Convert one Hugging Face example to model-ready image and label."""
    image = example["image"].convert("RGB")
    image = image.resize(image_size_for_mobilenet())
    image_array = np.asarray(image, dtype="float32")
    image_array = preprocess_input(image_array)
    return image_array, int(example["label_id"])


def build_tf_dataset(
    split,
    batch_size: int,
    shuffle: bool,
) -> tf.data.Dataset:
    """Convert a split into tf.data.Dataset."""

    def generator():
        for example in split:
            yield preprocess_example(example)

    dataset = tf.data.Dataset.from_generator(
        generator,
        output_signature=(
            tf.TensorSpec(shape=(224, 224, 3), dtype=tf.float32),
            tf.TensorSpec(shape=(), dtype=tf.int32),
        ),
    )

    if shuffle:
        dataset = dataset.shuffle(512, seed=42)

    return dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)
