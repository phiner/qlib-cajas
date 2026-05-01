#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.reproducibility_check import build_reproducibility_report


def main() -> int:
    p = argparse.ArgumentParser(description="Check reproducibility between two pipeline manifests.")
    p.add_argument("--left", required=True)
    p.add_argument("--right", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    left = json.loads(Path(args.left).expanduser().read_text(encoding="utf-8"))
    right = json.loads(Path(args.right).expanduser().read_text(encoding="utf-8"))
    rep = build_reproducibility_report(left_manifest=left, right_manifest=right)

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Reproducibility check completed.")
    print(f"output: {out}")
    print(f"final_status: {rep['final_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
