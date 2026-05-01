"""CLI for the food classification module."""
from __future__ import annotations

import argparse

from food_classified.inference import predict_image
from food_classified.loader import download_dataset, inspect_dataset_schema, load_local_dataset
from food_classified.trainer import train_model


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description="Food image classification tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("download")
    subparsers.add_parser("inspect")

    train_parser = subparsers.add_parser("train")
    train_parser.add_argument("--epochs", type=int, default=5)
    train_parser.add_argument("--batch-size", type=int, default=32)
    train_parser.add_argument("--min-samples", type=int, default=3)

    predict_parser = subparsers.add_parser("predict")
    predict_parser.add_argument("--image", type=str, required=True)
    predict_parser.add_argument("--top-k", type=int, default=3)

    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--batch-size", type=int, default=32)

    return parser


def main() -> None:
    """Run CLI command."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "download":
        path = download_dataset()
        print(f"Dataset saved to: {path}")
    elif args.command == "inspect":
        dataset = load_local_dataset()
        summary = inspect_dataset_schema(dataset)
        print(summary)
    elif args.command == "train":
        paths = train_model(
            epochs=args.epochs,
            batch_size=args.batch_size,
            min_samples_per_class=args.min_samples,
        )
        print(f"Model saved to: {paths['model']}")
        print(f"Labels saved to: {paths['labels']}")
        print(f"History saved to: {paths['history']}")
    elif args.command == "predict":
        from pathlib import Path

        results = predict_image(Path(args.image), k=args.top_k)
        for pred in results:
            print(f"{pred['label']}: {pred['score']:.4f}")
    elif args.command == "evaluate":
        from food_classified.trainer import evaluate_model

        metrics = evaluate_model(batch_size=args.batch_size)
        print(f"Loss: {metrics['loss']:.4f}")
        print(f"Accuracy: {metrics['accuracy']:.4f}")


if __name__ == "__main__":
    main()
