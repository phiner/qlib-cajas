#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.research_blocker_localizer import build_research_blocker_localization, render_research_blocker_localization_md


def _load(path: str | Path | None, *, required: bool) -> dict | None:
    if path is None:
        if required:
            raise ValueError("missing required input")
        return None
    p = Path(path).expanduser()
    if not p.exists():
        if required:
            raise FileNotFoundError(str(p))
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Localize research readiness blockers.")
    p.add_argument("--stable-repro-report", required=True)
    p.add_argument("--repro-explanation", required=True)
    p.add_argument("--normalization-coverage", default=None)
    p.add_argument("--governance-audit", required=True)
    p.add_argument("--governance-remediation", required=True)
    p.add_argument("--final-readiness", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args()

    rep = build_research_blocker_localization(
        stable_repro_report=_load(args.stable_repro_report, required=True) or {},
        repro_explanation=_load(args.repro_explanation, required=True) or {},
        normalization_coverage=_load(args.normalization_coverage, required=False),
        governance_audit=_load(args.governance_audit, required=True) or {},
        governance_remediation=_load(args.governance_remediation, required=True) or {},
        final_readiness=_load(args.final_readiness, required=True) or {},
    )
    outj = Path(args.out_json).expanduser().resolve()
    outm = Path(args.out_md).expanduser().resolve()
    outj.parent.mkdir(parents=True, exist_ok=True)
    outm.parent.mkdir(parents=True, exist_ok=True)
    outj.write_text(json.dumps(rep, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    outm.write_text(render_research_blocker_localization_md(report=rep), encoding="utf-8")
    print(f"output json: {outj}")
    print(f"output md: {outm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

