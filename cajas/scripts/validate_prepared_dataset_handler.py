#!/usr/bin/env python3
"""Validate prepared dataset readability and segment slicing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.handlers.prepared_csv_handler import PreparedCsvHandler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate prepared CSV handler with summary and segment checks."
    )
    parser.add_argument("--input", required=True, help="Path to prepared_dataset.csv")
    parser.add_argument("--label-col", default="future_direction_8", help="Label column name")
    parser.add_argument("--train-start", default="2025-01-01")
    parser.add_argument("--train-end", default="2025-08-31")
    parser.add_argument("--valid-start", default="2025-09-01")
    parser.add_argument("--valid-end", default="2025-10-31")
    parser.add_argument("--test-start", default="2025-11-01")
    parser.add_argument("--test-end", default="2025-12-31")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        handler = PreparedCsvHandler(csv_path=args.input, label_col=args.label_col)
        summary = handler.summary()
        print(f"rows: {summary['row_count']}")
        print(f"time_range: {summary['time_start']} -> {summary['time_end']}")
        print(f"feature_count: {summary['feature_count']}")
        print(f"features: {', '.join(summary['feature_columns'])}")
        print(f"label_col: {summary['label_col']}")
        print(f"excluded_leakage_columns: {', '.join(summary['excluded_leakage_columns'])}")
        print(f"label_distribution_full: {handler.label_distribution()}")

        segments = {
            "train": (args.train_start, args.train_end),
            "valid": (args.valid_start, args.valid_end),
            "test": (args.test_start, args.test_end),
        }
        segment_dfs = handler.prepare_segments(segments)
        for name, df in segment_dfs.items():
            row_count = len(df)
            print(f"{name}_rows: {row_count}")
            if row_count == 0:
                raise ValueError(f"Segment has zero rows: {name}")
            print(f"{name}_label_distribution: {handler.label_distribution(df)}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
