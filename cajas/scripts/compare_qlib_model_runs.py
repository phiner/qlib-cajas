#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_model_run_registry import load_qlib_model_registry
from cajas.reports.qlib_model_run_comparison import build_qlib_model_run_comparison


def main() -> int:
    p = argparse.ArgumentParser(description="Compare qlib model bridge runs from registry.")
    p.add_argument("--registry", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    records = load_qlib_model_registry(registry_path=args.registry)
    report = build_qlib_model_run_comparison(records=records)
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Qlib model run comparison completed.")
    print(f"output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
