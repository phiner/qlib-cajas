#!/usr/bin/env python3
"""Build golden shape snapshots from dataset quality smoke outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.dataset_quality_schema_contract import extract_schema_shape  # noqa: E402
from cajas.reports.runtime_io_summary import safe_json_write  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Build golden shape snapshots."""
    p = argparse.ArgumentParser(description="Build golden shape snapshots from smoke outputs.")
    p.add_argument("--smoke-root", required=True, help="Path to smoke output root")
    p.add_argument("--out-dir", required=True, help="Output directory for golden shapes")
    args = p.parse_args(argv)

    smoke_root = Path(args.smoke_root).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report_paths = {
        "dataset_quality_report": smoke_root / "dataset_quality" / "dataset_quality_report.json",
        "label_coverage_diagnostics": smoke_root / "labels" / "label_coverage_diagnostics.json",
        "time_coverage_diagnostics": smoke_root / "time" / "time_coverage_diagnostics.json",
        "chunked_feature_dry_run": smoke_root / "features" / "chunked_feature_dry_run.json",
        "feature_schema_manifest": smoke_root / "features" / "feature_schema_manifest.json",
        "offline_research_queue_summary": smoke_root / "research_queue" / "offline_research_queue_summary.json",
    }

    for name, path in report_paths.items():
        if not path.exists():
            print(f"warning: {name} not found at {path}", file=sys.stderr)
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        shape = extract_schema_shape(report, max_depth=4)
        out_path = out_dir / f"{name}_shape.json"
        safe_json_write(out_path, shape)
        print(f"wrote: {out_path}")

    # Bundle shape
    bundle_shape = {
        "dataset_quality_report": "object",
        "feature_schema_manifest": "object",
        "offline_research_queue_summary": "object",
    }
    bundle_path = out_dir / "bundle_shape.json"
    safe_json_write(bundle_path, bundle_shape)
    print(f"wrote: {bundle_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
