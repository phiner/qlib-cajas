#!/usr/bin/env python3
"""Build dataset quality golden scenario fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.dataset_quality_research import build_dataset_quality_research_artifacts
from cajas.reports.dataset_quality_schema_contract import extract_schema_shape


def safe_json_write(path: Path, data: dict) -> None:
    """Write JSON safely."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def generate_tiny_balanced_fixture() -> str:
    """Generate tiny balanced fixture."""
    return (
        "instrument,datetime,Open,High,Low,Close,Volume,future_direction_8\n"
        "EURUSD,2025-01-01 00:00:00,1.0,1.1,0.9,1.05,100,up\n"
        "EURUSD,2025-01-01 00:15:00,1.05,1.15,1.0,1.1,110,down\n"
        "EURUSD,2025-01-01 00:30:00,1.1,1.2,1.05,1.15,120,up\n"
    )


def generate_missing_label_values_fixture() -> str:
    """Generate fixture with missing label values."""
    return (
        "instrument,datetime,Open,High,Low,Close,Volume,future_direction_8\n"
        "EURUSD,2025-01-01 00:00:00,1.0,1.1,0.9,1.05,100,up\n"
        "EURUSD,2025-01-01 00:15:00,1.05,1.15,1.0,1.1,110,\n"
        "EURUSD,2025-01-01 00:30:00,1.1,1.2,1.05,1.15,120,\n"
    )


def generate_single_class_label_fixture() -> str:
    """Generate fixture with single class label."""
    return (
        "instrument,datetime,Open,High,Low,Close,Volume,future_direction_8\n"
        "EURUSD,2025-01-01 00:00:00,1.0,1.1,0.9,1.05,100,up\n"
        "EURUSD,2025-01-01 00:15:00,1.05,1.15,1.0,1.1,110,up\n"
        "EURUSD,2025-01-01 00:30:00,1.1,1.2,1.05,1.15,120,up\n"
    )


def generate_time_gap_fixture() -> str:
    """Generate fixture with time gap."""
    return (
        "instrument,datetime,Open,High,Low,Close,Volume,future_direction_8\n"
        "EURUSD,2025-01-01 00:00:00,1.0,1.1,0.9,1.05,100,up\n"
        "EURUSD,2025-01-01 00:15:00,1.05,1.15,1.0,1.1,110,down\n"
        "EURUSD,2025-01-01 12:00:00,1.1,1.2,1.05,1.15,120,up\n"
    )


def generate_minimal_columns_fixture() -> str:
    """Generate fixture with minimal columns."""
    return (
        "instrument,datetime,Close,future_direction_8\n"
        "EURUSD,2025-01-01 00:00:00,1.05,up\n"
        "EURUSD,2025-01-01 00:15:00,1.1,down\n"
        "EURUSD,2025-01-01 00:30:00,1.15,up\n"
    )


SCENARIOS = {
    "tiny_balanced": {
        "description": "Healthy tiny balanced fixture",
        "generator": generate_tiny_balanced_fixture,
        "feature_cols": ["Open", "High", "Low", "Close", "Volume"],
    },
    "missing_label_values": {
        "description": "Rows with missing label values",
        "generator": generate_missing_label_values_fixture,
        "feature_cols": ["Open", "High", "Low", "Close", "Volume"],
    },
    "single_class_label": {
        "description": "Label with only one class",
        "generator": generate_single_class_label_fixture,
        "feature_cols": ["Open", "High", "Low", "Close", "Volume"],
    },
    "time_gap": {
        "description": "Timestamp series with deliberate gap",
        "generator": generate_time_gap_fixture,
        "feature_cols": ["Open", "High", "Low", "Close", "Volume"],
    },
    "minimal_columns": {
        "description": "Minimal required columns only",
        "generator": generate_minimal_columns_fixture,
        "feature_cols": ["Close"],
    },
}


def build_scenario_golden_shapes(scenario_name: str, out_dir: Path) -> None:
    """Build golden shapes for a scenario."""
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}")

    scenario = SCENARIOS[scenario_name]
    print(f"Building scenario: {scenario_name}")

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        csv_path = tmp_path / "fixture.csv"
        csv_path.write_text(scenario["generator"](), encoding="utf-8")

        bundle = build_dataset_quality_research_artifacts(
            input_csv=csv_path,
            label_columns=["future_direction_8"],
            feature_columns=scenario["feature_cols"],
            chunk_size=10,
        )

        scenario_dir = out_dir / scenario_name
        scenario_dir.mkdir(parents=True, exist_ok=True)

        # Extract and save shapes
        report_keys = [
            "dataset_quality_report",
            "feature_schema_manifest",
            "offline_research_queue_summary",
        ]

        for key in report_keys:
            if key in bundle:
                shape = extract_schema_shape(bundle[key], max_depth=4)
                safe_json_write(scenario_dir / f"{key}_shape.json", shape)

        # Save bundle shape
        bundle_shape = {k: extract_schema_shape(v, max_depth=4) for k, v in bundle.items()}
        safe_json_write(scenario_dir / "bundle_shape.json", bundle_shape)

        print(f"  Saved shapes to {scenario_dir}")


def build_scenario_manifest(out_dir: Path) -> None:
    """Build scenario manifest."""
    manifest = {
        "schema_version": "v1",
        "scenarios": [
            {
                "name": name,
                "description": info["description"],
                "fixture_generator": info["generator"].__name__,
                "feature_columns": info["feature_cols"],
                "expected_reports": [
                    "dataset_quality_report",
                    "feature_schema_manifest",
                    "offline_research_queue_summary",
                ],
            }
            for name, info in SCENARIOS.items()
        ],
    }
    safe_json_write(out_dir / "scenario_manifest.json", manifest)
    print(f"Saved manifest to {out_dir / 'scenario_manifest.json'}")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build dataset quality golden scenario fixtures")
    parser.add_argument("--out-dir", required=True, help="Output directory for golden scenarios")
    parser.add_argument("--scenario", help="Build specific scenario only (default: all)")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"error: unknown scenario: {args.scenario}", file=sys.stderr)
            print(f"available: {', '.join(SCENARIOS.keys())}", file=sys.stderr)
            return 1
        build_scenario_golden_shapes(args.scenario, out_dir)
    else:
        for scenario_name in SCENARIOS:
            build_scenario_golden_shapes(scenario_name, out_dir)

    build_scenario_manifest(out_dir)
    print(json.dumps({"status": "ok", "out_dir": str(out_dir)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
