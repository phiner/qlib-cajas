#!/usr/bin/env python3
"""Build EURUSD Qlib market-state capability report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_qlib_market_state_capability import (
    build_qlib_market_state_capability_report,
    render_qlib_market_state_capability_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD Qlib market-state capability report")
    parser.add_argument("--audit-doc", type=Path, default=Path("cajas/docs/eurusd_qlib_market_state_capability_audit.md"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-qlib-market-state-capability.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-qlib-market-state-capability.md"))
    args = parser.parse_args()

    payload = build_qlib_market_state_capability_report(audit_doc=args.audit_doc, trial_approval_json=args.trial_approval_json)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_qlib_market_state_capability_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": payload.get("report_status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
