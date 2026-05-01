#!/usr/bin/env python3
"""Validate DatasetH-like prepared dataset adapter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.handlers.prepared_csv_handler import LEAKAGE_COLUMNS
from cajas.datasets.prepared_dataset import DEFAULT_SEGMENTS, PreparedDataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate PreparedDataset segment feature/label shape."
    )
    parser.add_argument("--input", required=True, help="Path to prepared_dataset.csv")
    parser.add_argument("--label-col", default="future_direction_8", help="Label column name")
    parser.add_argument("--train-start", default=DEFAULT_SEGMENTS["train"][0])
    parser.add_argument("--train-end", default=DEFAULT_SEGMENTS["train"][1])
    parser.add_argument("--valid-start", default=DEFAULT_SEGMENTS["valid"][0])
    parser.add_argument("--valid-end", default=DEFAULT_SEGMENTS["valid"][1])
    parser.add_argument("--test-start", default=DEFAULT_SEGMENTS["test"][0])
    parser.add_argument("--test-end", default=DEFAULT_SEGMENTS["test"][1])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    segments = {
        "train": (args.train_start, args.train_end),
        "valid": (args.valid_start, args.valid_end),
        "test": (args.test_start, args.test_end),
    }
    try:
        dataset = PreparedDataset(
            csv_path=args.input,
            label_col=args.label_col,
            segments=segments,
        )
        if not dataset.feature_columns:
            raise ValueError("No feature columns")
        leakage_found = sorted(set(dataset.feature_columns).intersection(LEAKAGE_COLUMNS))
        if leakage_found:
            raise ValueError(
                "Leakage columns found in features: " + ", ".join(leakage_found)
            )

        print("Prepared dataset adapter validation completed.")
        print(f"feature columns: {', '.join(dataset.feature_columns)}")
        print(f"label: {args.label_col}")
        print("segments:")
        print("label distribution:")
        for name in ("train", "valid", "test"):
            features, labels = dataset.prepare(name)
            if len(features) != len(labels):
                raise ValueError(f"features/labels row count mismatch for {name}")
            print(f"  {name}: {len(features)} rows, {len(labels)} labels")
            print(f"  {name}: {labels.value_counts(dropna=False).sort_index().to_dict()}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
