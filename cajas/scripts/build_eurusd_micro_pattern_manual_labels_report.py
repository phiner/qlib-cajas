#!/usr/bin/env python3
"""Build EURUSD micro-pattern manual labels report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_micro_pattern_manual_labels import (
    build_micro_pattern_manual_labels_report,
    render_micro_pattern_manual_labels_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD micro pattern manual labels report")
    parser.add_argument("--packet-csv", type=Path, required=True)
    parser.add_argument("--completed-labels-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    template_path = args.completed_labels_csv
    report = build_micro_pattern_manual_labels_report(
        packet_csv=args.packet_csv,
        completed_labels_csv=args.completed_labels_csv,
        output_template_csv=template_path,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_micro_pattern_manual_labels_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
