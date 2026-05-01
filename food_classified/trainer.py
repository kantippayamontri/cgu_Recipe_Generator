"""Training workflow for food image classification."""
from __future__ import annotations

import json
from pathlib import Path

from food_classified.dataset import build_tf_dataset, prepare_dataset_splits
from food_classified.loader import load_local_dataset
from food_classified.model import build_mobilenet_classifier
from food_classified.paths import FOOD_CLASSIFIED_ARTIFACTS_DIR


def model_artifact_paths(base_dir: Path | None = None) -> dict[str, Path]:
    """Return output artifact paths."""
    root = FOOD_CLASSIFIED_ARTIFACTS_DIR if base_dir is None else base_dir
    root.mkdir(parents=True, exist_ok=True)
    return {
        "model": root / "model.keras",
        "labels": root / "labels.json",
        "history": root / "history.json",
    }


def train_model(
    epochs: int = 5,
    batch_size: int = 32,
    min_samples_per_class: int = 3,
) -> dict[str, Path]:
    """Train the MobileNet classifier and save artifacts.

    Args:
        epochs: Number of training epochs.
        batch_size: Batch size for training.
        min_samples_per_class: Minimum samples per class to keep.

    Returns:
        Dictionary of saved artifact paths.
    """
    dataset = load_local_dataset()
    splits, label_mapping = prepare_dataset_splits(
        dataset, min_samples_per_class=min_samples_per_class
    )

    train_ds = build_tf_dataset(splits["train"], batch_size=batch_size, shuffle=True)
    validation_ds = build_tf_dataset(
        splits["validation"], batch_size=batch_size, shuffle=False
    )

    model = build_mobilenet_classifier(num_classes=len(label_mapping))
    history = model.fit(
        train_ds,
        validation_data=validation_ds,
        epochs=epochs,
        verbose=1,
    )

    paths = model_artifact_paths()
    model.save(paths["model"])

    inverse_mapping = {index: label for label, index in label_mapping.items()}
    with paths["labels"].open("w", encoding="utf-8") as f:
        json.dump(inverse_mapping, f, indent=2)

    with paths["history"].open("w", encoding="utf-8") as f:
        json.dump(history.history, f, indent=2)

    return paths


def evaluate_model(batch_size: int = 32) -> dict[str, float]:
    """Evaluate the saved classifier on the test split.

    Args:
        batch_size: Batch size for evaluation.

    Returns:
        Dictionary with 'loss' and 'accuracy' metrics.
    """
    import tensorflow as tf

    dataset = load_local_dataset()
    splits, label_mapping = prepare_dataset_splits(dataset)

    test_ds = build_tf_dataset(splits["test"], batch_size=batch_size, shuffle=False)

    model = tf.keras.models.load_model(model_artifact_paths()["model"])
    loss, accuracy = model.evaluate(test_ds, verbose=0)

    return {"loss": float(loss), "accuracy": float(accuracy)}
