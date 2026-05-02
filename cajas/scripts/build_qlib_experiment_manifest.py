#!/usr/bin/env python3
"""Build Qlib experiment reproducibility manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.qlib_experiment_manifest import (
    build_qlib_experiment_manifest,
    generate_manifest_markdown,
    manifest_to_dict,
    validate_qlib_experiment_manifest,
)


def safe_json_write(path: Path, data: dict) -> None:
    """Write JSON safely."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build Qlib experiment reproducibility manifest")
    parser.add_argument("--experiment-name", required=True, help="Experiment name")
    parser.add_argument("--dataset-path", help="Dataset path")
    parser.add_argument("--dataset-quality-report", help="Dataset quality report JSON path")
    parser.add_argument("--contract-report", help="Contract report JSON path")
    parser.add_argument("--trend-snapshot", help="Trend snapshot JSON path")
    parser.add_argument("--golden-scenario-manifest", help="Golden scenario manifest JSON path")
    parser.add_argument("--qlib-config", help="Qlib config path")
    parser.add_argument("--notes", help="Additional notes")
    parser.add_argument("--out-json", required=True, help="Output manifest JSON path")
    parser.add_argument("--out-md", required=True, help="Output manifest Markdown path")
    parser.add_argument("--allow-missing-optional", action="store_true", help="Allow missing optional paths")
    args = parser.parse_args(argv)

    manifest = build_qlib_experiment_manifest(
        experiment_name=args.experiment_name,
        dataset_path=args.dataset_path,
        dataset_quality_report_path=args.dataset_quality_report,
        contract_report_path=args.contract_report,
        trend_snapshot_path=args.trend_snapshot,
        golden_scenario_manifest_path=args.golden_scenario_manifest,
        qlib_config_path=args.qlib_config,
        notes=args.notes,
    )

    # Validate manifest
    errors = validate_qlib_experiment_manifest(manifest)
    if errors and not args.allow_missing_optional:
        print("error: manifest validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    # Write outputs
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    manifest_dict = manifest_to_dict(manifest)
    safe_json_write(out_json, manifest_dict)

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    markdown = generate_manifest_markdown(manifest, manifest_dict)
    out_md.write_text(markdown, encoding="utf-8")

    print(json.dumps({"status": "ok", "out_json": str(out_json), "out_md": str(out_md)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
