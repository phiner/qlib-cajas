#!/usr/bin/env python3
"""Build EURUSD candidate selection standards report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_candidate_selection_standards import (
    build_validation_eurusd_candidate_selection_standards,
    render_validation_eurusd_candidate_selection_standards_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EURUSD candidate selection standards report")
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-candidate-selection-standards.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-candidate-selection-standards.md"))
    args = parser.parse_args()

    payload = build_validation_eurusd_candidate_selection_standards()
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_candidate_selection_standards_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": payload.get("status"), "out_json": str(args.output_json), "out_md": str(args.output_md)}))


if __name__ == "__main__":
    main()
