#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.research_only_approval_packet import build_research_only_approval_packet, render_research_only_approval_packet_md


def _load(path: str | Path) -> dict:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Build research-only approval packet.")
    p.add_argument("--final-readiness-packet", required=True)
    p.add_argument("--stable-reproducibility-report", required=True)
    p.add_argument("--governance-remediation-report", required=True)
    p.add_argument("--governance-review-decision", required=True)
    p.add_argument("--offline-review-packet", required=True)
    p.add_argument("--final-research-bundle", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args()

    packet = build_research_only_approval_packet(
        final_readiness_packet=_load(args.final_readiness_packet),
        stable_reproducibility_report=_load(args.stable_reproducibility_report),
        governance_remediation_report=_load(args.governance_remediation_report),
        governance_review_decision=_load(args.governance_review_decision),
        offline_review_packet=_load(args.offline_review_packet),
        final_research_bundle=_load(args.final_research_bundle),
    )
    outj = Path(args.out_json).expanduser().resolve()
    outm = Path(args.out_md).expanduser().resolve()
    outj.parent.mkdir(parents=True, exist_ok=True)
    outm.parent.mkdir(parents=True, exist_ok=True)
    outj.write_text(json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    outm.write_text(render_research_only_approval_packet_md(packet=packet), encoding="utf-8")
    print(f"output json: {outj}")
    print(f"output md: {outm}")
    print(f"approval_status: {packet['approval_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

