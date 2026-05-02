#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.governance_review_decision import build_governance_review_decision, render_governance_review_decision_md


def _load(path: str | Path | None) -> dict | None:
    if path is None:
        return None
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Build governance review decision packet.")
    p.add_argument("--governance-remediation-report", required=True)
    p.add_argument("--final-readiness-packet", required=True)
    p.add_argument("--stable-reproducibility-report", required=True)
    p.add_argument("--decision", default=None)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args()

    rep = build_governance_review_decision(
        governance_remediation_report=_load(args.governance_remediation_report) or {},
        final_readiness_packet=_load(args.final_readiness_packet) or {},
        stable_reproducibility_report=_load(args.stable_reproducibility_report) or {},
        decision=_load(args.decision),
    )
    outj = Path(args.out_json).expanduser().resolve()
    outm = Path(args.out_md).expanduser().resolve()
    outj.parent.mkdir(parents=True, exist_ok=True)
    outm.parent.mkdir(parents=True, exist_ok=True)
    outj.write_text(json.dumps(rep, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    outm.write_text(render_governance_review_decision_md(packet=rep), encoding="utf-8")
    print(f"output json: {outj}")
    print(f"output md: {outm}")
    print(f"governance_review_status: {rep['governance_review_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

