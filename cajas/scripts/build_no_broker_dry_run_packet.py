#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.no_broker_dry_run_packet import build_no_broker_dry_run_packet


def main() -> int:
    p = argparse.ArgumentParser(description="Build no-broker dry-run packet from research gate packet.")
    p.add_argument("--gate-packet", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    gate = json.loads(Path(args.gate_packet).expanduser().read_text(encoding="utf-8"))
    packet = build_no_broker_dry_run_packet(gate_packet=gate)

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("No-broker dry-run packet completed.")
    print(f"output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
