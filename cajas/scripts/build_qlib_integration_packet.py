#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_adapter_contract import ContractIssue, validate_qlib_adapter_contract
from cajas.reports.qlib_integration_packet import build_qlib_integration_packet


def main() -> int:
    p = argparse.ArgumentParser(description="Build dry-run Qlib integration packet from adapter contract.")
    p.add_argument("--adapter-contract", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--strict-paths", action="store_true")
    args = p.parse_args()

    contract = json.loads(Path(args.adapter_contract).expanduser().read_text(encoding="utf-8"))
    issues = validate_qlib_adapter_contract(contract, strict_paths=args.strict_paths)
    packet = build_qlib_integration_packet(contract=contract, issues=issues)

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "qlib_integration_packet.json").write_text(
        json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "qlib_integration_packet.md").write_text(
        "# Qlib Integration Packet\n\n"
        f"- readiness_decision: `{packet['readiness_decision']}`\n"
        f"- blocking_issues: `{len(packet['blocking_issues'])}`\n"
        f"- warnings: `{len(packet['non_blocking_warnings'])}`\n",
        encoding="utf-8",
    )
    print("Qlib integration packet completed.")
    print(f"output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
