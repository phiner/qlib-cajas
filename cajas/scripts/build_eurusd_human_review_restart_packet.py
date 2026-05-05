#!/usr/bin/env python3
"""Build EURUSD human review restart packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_human_review_restart_packet import (
    build_human_review_restart_packet,
    render_human_review_restart_packet_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD human review restart packet")
    parser.add_argument("--language-boundary-json", type=Path, default=Path("tmp/validation-eurusd-language-boundary.json"))
    parser.add_argument("--zh-rationale-json", type=Path, default=Path("tmp/validation-eurusd-zh-rationale-fields.json"))
    parser.add_argument("--human-review-quality-json", type=Path, default=Path("tmp/validation-eurusd-human-review-quality.json"))
    parser.add_argument("--review-standard-json", type=Path, default=Path("tmp/validation-eurusd-review-standard-v0.json"))
    parser.add_argument("--llm-artifacts-json", type=Path, default=Path("tmp/validation-eurusd-llm-review-artifacts.json"))
    parser.add_argument("--llm-second-review-json", type=Path, default=Path("tmp/validation-eurusd-llm-second-review.json"))
    parser.add_argument("--real-llm-readiness-json", type=Path, default=Path("tmp/validation-eurusd-real-llm-integration-readiness.json"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--fast-validation-timing-json", type=Path, default=Path("tmp/fast_validation_latest.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-human-review-restart-packet.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-human-review-restart-packet.md"))
    args = parser.parse_args()

    payload = build_human_review_restart_packet(
        language_boundary_json=args.language_boundary_json,
        zh_rationale_json=args.zh_rationale_json,
        human_review_quality_json=args.human_review_quality_json,
        review_standard_json=args.review_standard_json,
        llm_artifacts_json=args.llm_artifacts_json,
        llm_second_review_json=args.llm_second_review_json,
        real_llm_readiness_json=args.real_llm_readiness_json,
        trial_approval_json=args.trial_approval_json,
        fast_validation_timing_json=args.fast_validation_timing_json,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_human_review_restart_packet_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": payload.get("report_status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
