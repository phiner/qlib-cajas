#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.final_readiness_packet import build_final_readiness_packet


def _load(path: str | Path) -> dict:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Build final readiness packet from research artifacts.")
    p.add_argument("--gate-packet", required=True)
    p.add_argument("--no-broker-packet", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--reproducibility-report", required=True)
    p.add_argument("--stable-reproducibility-report", default=None)
    p.add_argument("--stable-reproducibility-explanation", default=None)
    p.add_argument("--governance-remediation-report", default=None)
    p.add_argument("--normalization-coverage-report", default=None)
    p.add_argument("--governance-review-decision", default=None)
    p.add_argument("--research-only-approval-packet", default=None)
    p.add_argument("--ci-plan", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    packet = build_final_readiness_packet(
        gate_packet=_load(args.gate_packet),
        no_broker_packet=_load(args.no_broker_packet),
        manifest=_load(args.manifest),
        reproducibility_report=_load(args.reproducibility_report),
        stable_reproducibility_report=None if args.stable_reproducibility_report is None else _load(args.stable_reproducibility_report),
        stable_reproducibility_explanation=None if args.stable_reproducibility_explanation is None else _load(args.stable_reproducibility_explanation),
        governance_remediation_report=None if args.governance_remediation_report is None else _load(args.governance_remediation_report),
        normalization_coverage_report=None if args.normalization_coverage_report is None else _load(args.normalization_coverage_report),
        governance_review_decision=None if args.governance_review_decision is None else _load(args.governance_review_decision),
        research_only_approval_packet=None if args.research_only_approval_packet is None else _load(args.research_only_approval_packet),
        ci_plan=_load(args.ci_plan),
    )
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Final readiness packet completed.")
    print(f"output: {out}")
    print(f"final_status: {packet['final_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
