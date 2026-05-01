"""Model factory for food image classification."""
from __future__ import annotations

import tensorflow as tf
from tensorflow.keras import layers, models


def build_mobilenet_classifier(num_classes: int) -> tf.keras.Model:
    """Build a MobileNetV2 transfer-learning classifier.

    Args:
        num_classes: Number of output classes (ingredients).

    Returns:
        Compiled Keras model ready for training.
    """
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    inputs = layers.Input(shape=(224, 224, 3))
    x = base_model(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = models.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


def unfreeze_top_layers(model: tf.keras.Model, layers_to_unfreeze: int = 20) -> None:
    """Unfreeze top layers of MobileNet base for fine-tuning.

    Args:
        model: The compiled MobileNet classifier.
        layers_to_unfreeze: Number of top layers to unfreeze in the base model.
    """
    base_model = model.layers[1]
    base_model.trainable = True
    for layer in base_model.layers[:-layers_to_unfreeze]:
        layer.trainable = False
