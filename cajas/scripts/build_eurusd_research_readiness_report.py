#!/usr/bin/env python3
"""Build EURUSD research readiness report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_research_readiness import (
    build_validation_eurusd_research_readiness,
    render_validation_eurusd_research_readiness_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD research readiness report")
    parser.add_argument("--base-maintenance-continuation-report", required=True, type=Path)
    parser.add_argument("--dataset-contract-report", required=True, type=Path)
    parser.add_argument("--dataset-audit-report", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=args.base_maintenance_continuation_report,
        dataset_contract_report=args.dataset_contract_report,
        dataset_audit_report=args.dataset_audit_report,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_validation_eurusd_research_readiness_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
