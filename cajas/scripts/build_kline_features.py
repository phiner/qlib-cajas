#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.features.kline_structure_features import add_kline_structure_features


def main() -> int:
    p = argparse.ArgumentParser(description="Build K-line structure feature dataset.")
    p.add_argument("--input", required=True)
    p.add_argument("--output")
    p.add_argument("--window", action="append", type=int)
    p.add_argument("--report-output")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    _, rep = add_kline_structure_features(input_path=args.input, output_path=args.output, windows=args.window)
    payload = rep.to_dict()
    if args.report_output:
        out = Path(args.report_output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Kline feature build completed.")
        print(f"added features: {len(payload['added_features'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
