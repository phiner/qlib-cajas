#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.research_gate_summary import render_research_gate_summary


def main() -> int:
    p = argparse.ArgumentParser(description="Build markdown summary for research gate/no-broker packets.")
    p.add_argument("--gate-packet", required=True)
    p.add_argument("--no-broker-packet", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    gate = json.loads(Path(args.gate_packet).expanduser().read_text(encoding="utf-8"))
    nb = json.loads(Path(args.no_broker_packet).expanduser().read_text(encoding="utf-8"))
    md = render_research_gate_summary(gate_packet=gate, no_broker_packet=nb)
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print("Research gate summary completed.")
    print(f"output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
