#!/usr/bin/env python3
"""Build EURUSD GUI entrypoint disambiguation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_gui_entrypoints import (
    build_eurusd_gui_entrypoints_report,
    render_eurusd_gui_entrypoints_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD GUI entrypoints report")
    parser.add_argument("--pattern-launcher", type=Path, default=Path("scripts/run_eurusd_review_gui.sh"))
    parser.add_argument("--pattern-app", type=Path, default=Path("cajas/apps/eurusd_pattern_review_app.py"))
    parser.add_argument("--market-state-launcher", type=Path, default=Path("scripts/run_eurusd_market_state_inspection_gui.sh"))
    parser.add_argument("--market-state-app", type=Path, default=Path("cajas/apps/eurusd_market_state_inspection_app.py"))
    parser.add_argument("--kickoff-doc", type=Path, default=Path("cajas/docs/eurusd_pattern_research_kickoff.md"))
    parser.add_argument("--roadmap-doc", type=Path, default=Path("tasks/eurusd_15m_research_end_to_end_roadmap.md"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-gui-entrypoints.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-gui-entrypoints.md"))
    args = parser.parse_args()

    payload = build_eurusd_gui_entrypoints_report(
        pattern_launcher=args.pattern_launcher,
        pattern_app=args.pattern_app,
        market_state_launcher=args.market_state_launcher,
        market_state_app=args.market_state_app,
        kickoff_doc=args.kickoff_doc,
        roadmap_doc=args.roadmap_doc,
        trial_approval_json=args.trial_approval_json,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_eurusd_gui_entrypoints_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "report_status": payload.get("report_status"),
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
