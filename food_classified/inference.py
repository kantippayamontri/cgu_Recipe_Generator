"""Inference helpers for food image classification."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from food_classified.paths import FOOD_CLASSIFIED_ARTIFACTS_DIR


def top_k_predictions(
    probabilities: list[float],
    labels: dict[int, str],
    k: int = 3,
) -> list[dict[str, float | str]]:
    """Return top-k predictions sorted by descending score.

    Args:
        probabilities: List of probability scores for each class.
        labels: Mapping from class index to label name.
        k: Number of top predictions to return.

    Returns:
        List of dicts with 'label' and 'score' keys.
    """
    indexed = list(enumerate(probabilities))
    indexed.sort(key=lambda item: item[1], reverse=True)
    return [
        {"label": labels[index], "score": float(score)}
        for index, score in indexed[:k]
    ]


def predict_image(image_path: Path, k: int = 3) -> list[dict[str, float | str]]:
    """Predict ingredient label probabilities for one image.

    Args:
        image_path: Path to the input image file.
        k: Number of top predictions to return.

    Returns:
        List of top-k predictions with labels and scores.
    """
    model = tf.keras.models.load_model(FOOD_CLASSIFIED_ARTIFACTS_DIR / "model.keras")

    with (FOOD_CLASSIFIED_ARTIFACTS_DIR / "labels.json").open("r", encoding="utf-8") as f:
        raw_labels = json.load(f)
    labels = {int(index): label for index, label in raw_labels.items()}

    image = Image.open(image_path).convert("RGB").resize((224, 224))
    array = np.asarray(image, dtype="float32")
    array = preprocess_input(array)
    array = np.expand_dims(array, axis=0)

    probabilities = model.predict(array, verbose=0)[0].tolist()
    return top_k_predictions(probabilities, labels, k=k)
