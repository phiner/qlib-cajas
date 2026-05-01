#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.baseline.feature_importance_inspector import inspect_feature_importance


def main() -> int:
    p = argparse.ArgumentParser(description="Inspect baseline model feature importance.")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--top-k", type=int, default=30)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = inspect_feature_importance(run_dir=args.run_dir, top_k=args.top_k)
    payload = rep.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print("Feature importance inspection completed.")
        print(f"available: {'yes' if payload['available'] else 'no'}")
        print(f"top features: {len(payload['top_features'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
