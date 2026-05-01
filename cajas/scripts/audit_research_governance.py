#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.audits.research_governance_audit import run_research_governance_audit


def main() -> int:
    p = argparse.ArgumentParser(description="Run conservative research governance audit.")
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    rep = run_research_governance_audit(root=args.root)
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"governance audit: {out}")
    print(f"status: {rep['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
