#!/usr/bin/env python3
"""Check review bundle manifest canonical/legacy history compatibility."""

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cajas.reports.validation_review_bundle_metadata import (
    normalize_history_metadata,
    validate_history_metadata_compatibility,
)


def build_compatibility_report(manifest: dict, manifest_path: str) -> dict:
    """Build compatibility report payload from a loaded manifest."""
    normalized = normalize_history_metadata(manifest)
    warnings = validate_history_metadata_compatibility(manifest)
    return {
        "status": "warn" if warnings else "pass",
        "manifest_path": manifest_path,
        "history_source": normalized.get("source"),
        "history_enabled": normalized.get("enabled"),
        "history_status": normalized.get("status"),
        "warnings": warnings,
    }


def render_compatibility_markdown(report: dict) -> str:
    """Render compatibility report markdown."""
    lines = [
        "# Review Bundle Manifest Compatibility",
        "",
        f"- status: `{report['status']}`",
        f"- history_source: `{report['history_source']}`",
        f"- history_enabled: `{report['history_enabled']}`",
        f"- history_status: `{report['history_status']}`",
        "",
        "## Warnings",
        "",
    ]
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check review bundle manifest compatibility")
    parser.add_argument("--manifest", type=Path, required=True, help="Path to review_bundle_manifest.json")
    parser.add_argument("--out-json", type=Path, required=True, help="Output JSON report path")
    parser.add_argument("--out-md", type=Path, required=True, help="Output Markdown report path")
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = build_compatibility_report(manifest, str(args.manifest))

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_compatibility_markdown(report), encoding="utf-8")

    print(json.dumps({"status": report["status"], "warnings": len(report["warnings"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
