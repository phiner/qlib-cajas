#!/usr/bin/env python3
"""Inspect baseline run artifacts and optionally generate prediction review outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.baseline_artifact_inspector import inspect_baseline_run_artifacts
from cajas.baseline.prediction_review import build_prediction_review


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect local baseline artifacts without retraining.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-review-artifacts", action="store_true")
    parser.add_argument("--output-dir", default="tmp/cajas/baseline_reviews")
    parser.add_argument("--run-name", default="phase21_baseline_review")
    parser.add_argument("--low-confidence-threshold", type=float, default=0.45)
    parser.add_argument("--high-confidence-error-threshold", type=float, default=0.70)
    return parser.parse_args()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    try:
        inspection = inspect_baseline_run_artifacts(args.run_dir)
    except (FileNotFoundError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = inspection.to_dict()
    review_payload = None

    if args.write_review_artifacts:
        out_root = Path(args.output_dir).expanduser().resolve()
        run_out = out_root / args.run_name
        if run_out.exists():
            print(f"ERROR: Refusing to overwrite existing output directory: {run_out}", file=sys.stderr)
            return 1
        run_out.mkdir(parents=True, exist_ok=False)

        valid_review = build_prediction_review(
            prediction_csv=Path(args.run_dir) / "predictions_valid.csv",
            output_dir=run_out,
            split="valid",
            low_confidence_threshold=args.low_confidence_threshold,
            high_confidence_error_threshold=args.high_confidence_error_threshold,
        )
        test_review = build_prediction_review(
            prediction_csv=Path(args.run_dir) / "predictions_test.csv",
            output_dir=run_out,
            split="test",
            low_confidence_threshold=args.low_confidence_threshold,
            high_confidence_error_threshold=args.high_confidence_error_threshold,
        )

        _write_json(run_out / "baseline_artifact_inspection_report.json", payload)
        _write_json(run_out / "valid_prediction_review_report.json", valid_review.to_dict())
        _write_json(run_out / "test_prediction_review_report.json", test_review.to_dict())

        review_payload = {
            "output_dir": str(run_out),
            "valid": valid_review.to_dict(),
            "test": test_review.to_dict(),
        }

    output = dict(payload)
    if review_payload is not None:
        output["review_artifacts"] = review_payload

    if args.json:
        print(json.dumps(output, ensure_ascii=True, indent=2))
        return 0

    print("Baseline artifact inspection completed.")
    print(f"run dir: {payload['run_dir']}")
    print("required files present: " + ("yes" if payload["required_files_present"] else "no"))
    print("model family used: " + str(payload.get("model_family_used")))
    print("target label: " + str(payload.get("target_label")))
    print("feature count: " + str(payload.get("feature_count")))
    print("valid accuracy: " + str(payload.get("metrics_valid", {}).get("accuracy")))
    print("test accuracy: " + str(payload.get("metrics_test", {}).get("accuracy")))
    print("issues:")
    if payload["issues"]:
        for issue in payload["issues"]:
            print(f"  - [{issue['severity']}] {issue['code']}: {issue['message']}")
    else:
        print("  - none")
    print("warnings:")
    if payload["warnings"]:
        for warning in payload["warnings"]:
            print(f"  - {warning}")
    else:
        print("  - none")
    if review_payload is not None:
        print("review artifacts written: yes")
        print("review output dir: " + review_payload["output_dir"])
    else:
        print("review artifacts written: no")
    print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
