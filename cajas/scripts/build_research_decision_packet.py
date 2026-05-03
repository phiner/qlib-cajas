#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.research_decision_builder import build_research_decision


def _write_csv(path: Path, rows: list[dict], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _render_md(packet: dict) -> str:
    lines = [
        "# Research Decision Packet",
        "",
        f"- final_decision: `{packet['final_decision']}`",
        f"- confidence_level: `{packet['confidence_level']}`",
        "",
        "## Required Artifact Checklist",
    ]
    for key in [
        "label_variant_summary_path",
        "feature_set_summary_path",
        "calibration_summary_path",
        "seed_stability_summary_path",
        "rolling_validation_plan_path",
        "error_slice_summary_path",
        "leakage_drift_audit_path",
        "qlib_readiness_report_path",
    ]:
        lines.append(f"- `{key}`: `{packet.get(key, '')}`")
    lines += ["", "## Blocking Findings"]
    for item in packet.get("blocking_findings", []):
        lines.append(f"- `{item['code']}`: {item['message']}")
    if not packet.get("blocking_findings"):
        lines.append("- none")
    lines += ["", "## Non-Blocking Findings"]
    for item in packet.get("non_blocking_findings", []):
        lines.append(f"- `{item['code']}`: {item['message']}")
    if not packet.get("non_blocking_findings"):
        lines.append("- none")
    lines += ["", "## Recommended Next Actions"]
    for item in packet.get("recommended_next_actions", []):
        lines.append(f"- [{item['priority']}] {item['action']}: {item['rationale']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build conservative research decision packet.")
    p.add_argument("--reports-dir", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--run-id", default="phase56_65_decision_packet")
    p.add_argument("--notes", default="")
    p.add_argument("--strict", action="store_true")
    args = p.parse_args(argv)

    result = build_research_decision(reports_dir=args.reports_dir, run_id=args.run_id, notes=args.notes)
    packet = result.to_dict()
    out = Path(args.out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    (out / "research_decision_packet.json").write_text(json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "research_decision_packet.md").write_text(_render_md(packet), encoding="utf-8")
    _write_csv(out / "research_decision_findings.csv", packet["blocking_findings"] + packet["non_blocking_findings"], ["severity", "code", "message", "source_path"])
    _write_csv(out / "research_decision_recommendations.csv", packet["recommended_next_actions"], ["priority", "action", "rationale"])

    if args.strict and packet["blocking_findings"]:
        print("Research decision packet built with blocking findings under --strict.")
        return 2
    print("Research decision packet completed.")
    print(f"output dir: {out}")
    print(f"final decision: {packet['final_decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
