#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.datasets.threshold_label_generator import generate_threshold_labels


def main() -> int:
    p = argparse.ArgumentParser(description="Generate threshold-based label variants.")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=False)
    p.add_argument("--report-output")
    p.add_argument("--horizon", action="append", required=True, type=int)
    p.add_argument("--threshold", action="append", required=True, type=float)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    rep = generate_threshold_labels(
        input_path=args.input,
        output_path=args.output,
        horizons=args.horizon,
        thresholds=args.threshold,
    )
    payload = rep.to_dict()
    if args.report_output:
        out = Path(args.report_output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Threshold label generation completed.")
        print(f"row count: {payload['row_count']}")
        print(f"spec count: {len(payload['specs'])}")
        print("notice: thresholds are classification label thresholds only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
