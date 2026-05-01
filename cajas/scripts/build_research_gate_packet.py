#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.research_gate_builder import build_research_gate_packet


def main() -> int:
    p = argparse.ArgumentParser(description="Build research gate packet from model bridge artifacts.")
    p.add_argument("--contract", required=True)
    p.add_argument("--experiment-dir", required=True)
    p.add_argument("--registry", default=None)
    p.add_argument("--comparison", default=None)
    p.add_argument("--handler-smoke-report", default=None)
    p.add_argument("--compatibility-report", default=None)
    p.add_argument("--research-decision-packet", default=None)
    p.add_argument("--min-macro-f1", type=float, default=0.20)
    p.add_argument("--min-accuracy", type=float, default=0.20)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    packet = build_research_gate_packet(
        contract_path=args.contract,
        experiment_dir=args.experiment_dir,
        registry_path=args.registry,
        comparison_path=args.comparison,
        handler_smoke_report_path=args.handler_smoke_report,
        compatibility_report_path=args.compatibility_report,
        research_decision_packet_path=args.research_decision_packet,
        min_macro_f1=args.min_macro_f1,
        min_accuracy=args.min_accuracy,
    )
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Research gate packet completed.")
    print(f"output: {out}")
    print(f"final_status: {packet['final_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
