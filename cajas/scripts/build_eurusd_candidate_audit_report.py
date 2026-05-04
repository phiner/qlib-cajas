"""Build EURUSD candidate causality/coverage audit report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_candidate_audit import (
    build_validation_eurusd_candidate_audit,
    render_validation_eurusd_candidate_audit_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EURUSD candidate audit report")
    parser.add_argument("--candidate-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_candidates.csv"))
    parser.add_argument("--template-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_template.csv"))
    parser.add_argument("--batch-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"))
    parser.add_argument("--clean-view-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"))
    parser.add_argument("--rejected-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-candidate-audit.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-candidate-audit.md"))
    args = parser.parse_args()

    payload = build_validation_eurusd_candidate_audit(
        candidate_csv=args.candidate_csv,
        template_csv=args.template_csv,
        batch_csv=args.batch_csv,
        clean_view_csv=args.clean_view_csv,
        rejected_csv=args.rejected_csv,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_candidate_audit_markdown(payload), encoding="utf-8")

    print(json.dumps({"status": payload.get("status"), "out_json": str(args.output_json), "out_md": str(args.output_md)}))


if __name__ == "__main__":
    main()
