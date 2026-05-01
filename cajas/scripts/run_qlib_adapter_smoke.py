#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run end-to-end Qlib adapter contract dry-run smoke.")
    p.add_argument("--out-root", default="tmp/qlib-adapter-smoke")
    args = p.parse_args()

    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "promotion_id": "promotion_phase66_smoke",
        "decision_packet_path": str(out_root / "inputs" / "research_decision_packet.json"),
        "known_limitations": ["smoke fixture only"],
        "status": "candidate_for_manual_review",
    }
    inputs = out_root / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (inputs / "research_decision_packet.json").write_text(json.dumps({"final_decision": "candidate_for_qlib_trial"}), encoding="utf-8")
    manifest_path = inputs / "candidate_promotion_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    py = sys.executable
    contract_path = out_root / "contract" / "qlib_adapter_contract.json"
    _run(
        [
            py,
            "cajas/scripts/build_qlib_adapter_contract.py",
            "--promotion-manifest",
            str(manifest_path),
            "--out",
            str(contract_path),
            "--candidate-id",
            "candidate_phase66_smoke",
            "--feature-set-id",
            "structure_v1",
            "--label-variant-id",
            "label_h8_binary_drop_flat",
            "--target-name",
            "future_direction_8",
            "--frequency",
            "15m",
        ]
    )
    _run([py, "cajas/scripts/build_qlib_integration_packet.py", "--adapter-contract", str(contract_path), "--out-dir", str(out_root / "packet")])
    _run([py, "cajas/scripts/build_qlib_compatibility_report.py", "--adapter-contract", str(contract_path), "--out-dir", str(out_root / "compat")])

    report = json.loads((out_root / "compat" / "qlib_compatibility_report.json").read_text(encoding="utf-8"))
    if report.get("blocking_issues"):
        print("Qlib adapter smoke failed: blocking issues present.")
        return 2

    print("Qlib adapter smoke completed.")
    print(f"contract: {contract_path}")
    print(f"integration packet: {out_root / 'packet'}")
    print(f"compatibility report: {out_root / 'compat'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
