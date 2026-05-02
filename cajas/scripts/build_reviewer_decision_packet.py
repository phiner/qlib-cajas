#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.reviewer_decision_packet import build_reviewer_decision_packet


def _load(path: str | Path | None) -> dict | None:
    if path is None:
        return None
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Build reviewer decision packet.")
    p.add_argument("--decision", required=True)
    p.add_argument("--final-readiness-packet", required=True)
    p.add_argument("--governance-remediation-report", default=None)
    p.add_argument("--reproducibility-explanation", default=None)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    packet = build_reviewer_decision_packet(
        decision=_load(args.decision) or {},
        final_readiness_packet=_load(args.final_readiness_packet) or {},
        governance_remediation_report=_load(args.governance_remediation_report),
        reproducibility_explanation=_load(args.reproducibility_explanation),
    )
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"output: {out}")
    print(f"decision: {packet['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

