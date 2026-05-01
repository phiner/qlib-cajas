#!/usr/bin/env python3
"""Run a dry-run validation for the prepared workflow bridge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.datasets.prepared_dataset import DEFAULT_SEGMENTS
from cajas.workflows.prepared_workflow import PreparedWorkflow, PreparedWorkflowConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run PreparedWorkflow dry-run validation."
    )
    parser.add_argument("--input", required=True, help="Path to prepared_dataset.csv")
    parser.add_argument("--label-col", default="future_direction_8", help="Label column")
    parser.add_argument("--train-start", default=DEFAULT_SEGMENTS["train"][0])
    parser.add_argument("--train-end", default=DEFAULT_SEGMENTS["train"][1])
    parser.add_argument("--valid-start", default=DEFAULT_SEGMENTS["valid"][0])
    parser.add_argument("--valid-end", default=DEFAULT_SEGMENTS["valid"][1])
    parser.add_argument("--test-start", default=DEFAULT_SEGMENTS["test"][0])
    parser.add_argument("--test-end", default=DEFAULT_SEGMENTS["test"][1])
    parser.add_argument("--json", action="store_true", help="Print summary as JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    segments = {
        "train": (args.train_start, args.train_end),
        "valid": (args.valid_start, args.valid_end),
        "test": (args.test_start, args.test_end),
    }
    try:
        config = PreparedWorkflowConfig(
            csv_path=args.input,
            label_col=args.label_col,
            segments=segments,
        )
        summary = PreparedWorkflow(config).dry_run()
        if args.json:
            print(json.dumps(summary.to_dict(), ensure_ascii=True, indent=2))
            return 0

        print("Prepared workflow dry-run completed.")
        print(f"label: {summary.label_col}")
        print(f"feature count: {len(summary.feature_columns)}")
        print("segments:")
        for shape in summary.segment_shapes:
            print(
                f"  {shape.segment}: features=({shape.feature_rows}, {shape.feature_cols}), "
                f"labels={shape.label_rows}"
            )
        print(
            "leakage columns in features: "
            + ("yes" if summary.leakage_columns_in_features else "no")
        )
        print(
            "training executed: " + ("yes" if summary.training_executed else "no")
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
