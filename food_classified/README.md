# Food Classified Module

Standalone ingredient image classification using Hugging Face dataset images and MobileNet transfer learning.

## Optional: Hugging Face Token for Faster Downloads

To speed up dataset downloads, add your Hugging Face token to `.env`:

```bash
HF_TOKEN=your_huggingface_token_here
```

Get your token at: https://huggingface.co/settings/tokens (create with "read" permissions)

**Benefits:**
- Higher rate limits (2GB/hour vs 600MB/hour for anonymous)
- Faster download speeds
- Required for gated datasets (not needed for this public dataset)

## Quick Start

```bash
# 1. Download the dataset
uv run python -m food_classified download

# 2. Inspect the dataset
uv run python -m food_classified inspect

# 3. Train the model (adjust epochs as needed)
uv run python -m food_classified train --epochs 5 --batch-size 32

# 4. Predict on a new image
uv run python -m food_classified predict --image path/to/image.jpg --top-k 3

# 5. Evaluate on test split
uv run python -m food_classified evaluate
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `download` | Download the Hugging Face dataset and cache locally |
| `inspect` | Show dataset schema and statistics |
| `train` | Train the MobileNet classifier |
| `predict` | Predict ingredient labels for an image |
| `evaluate` | Evaluate model on test split |

## Train Options

| Option | Default | Description |
|--------|---------|-------------|
| `--epochs` | 5 | Number of training epochs |
| `--batch-size` | 32 | Training batch size |
| `--min-samples` | 3 | Minimum samples per class to keep |

## Predict Options

| Option | Default | Description |
|--------|---------|-------------|
| `--image` | (required) | Path to input image |
| `--top-k` | 3 | Number of predictions to return |

## Data Layout

```
data/food_classified/
├── raw/              # Downloaded dataset
├── cache/            # Hugging Face cache
├── processed/        # Processed splits
└── artifacts/        # Trained model and metadata
    ├── model.keras
    ├── labels.json
    └── history.json
```

## Dataset

- **Source:** [Scuccorese/food-ingredients-dataset](https://huggingface.co/datasets/Scuccorese/food-ingredients-dataset)
- **Target:** Ingredient classification (e.g., "tomato", "spinach", "lettuce")
- **Splits:** Train/validation/test created from source with deterministic seeding
- **Filtering:** Classes with fewer than 3 samples are dropped for stability

## Model

- **Base:** MobileNetV2 (ImageNet weights, frozen backbone)
- **Head:** Global average pooling + dropout (0.2) + dense (softmax)
- **Input:** 224x224 RGB images with MobileNet preprocessing

## Implementation Notes

- Does not modify `config.py` - paths are in `food_classified/paths.py`
- Uses TensorFlow/Keras for model training and inference
- Deterministic splits with seed=42
- Rare class filtering ensures stable training and evaluation
