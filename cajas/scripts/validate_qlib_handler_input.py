#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_handler_smoke_validator import validate_qlib_handler_input


def main() -> int:
    p = argparse.ArgumentParser(description="Validate offline Qlib handler input package.")
    p.add_argument("--handler-dir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    rep = validate_qlib_handler_input(handler_dir=args.handler_dir)
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Qlib handler input validation completed.")
    print(f"output: {out}")
    print(f"status: {rep['status']}")
    return 0 if rep["status"] != "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
