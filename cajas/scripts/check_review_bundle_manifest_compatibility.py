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
    summarize_compatibility_issues,
    validate_history_metadata_compatibility,
)


def build_compatibility_report(manifest: dict, manifest_path: str) -> dict:
    """Build compatibility report payload from a loaded manifest."""
    normalized = normalize_history_metadata(manifest)
    issues = validate_history_metadata_compatibility(manifest)
    summary = summarize_compatibility_issues(issues)
    has_legacy_alias = isinstance(manifest.get("history_update"), dict)
    return {
        "status": summary["status"],
        "manifest_path": manifest_path,
        "history_source": normalized.get("source"),
        "history_enabled": normalized.get("enabled"),
        "history_status": normalized.get("status"),
        "error_count": summary["error_count"],
        "warning_count": summary["warning_count"],
        "info_count": summary["info_count"],
        "deprecated_alias_present": "yes" if has_legacy_alias else "no",
        "issues": issues,
        "reviewer_recommendation": (
            "block_until_manifest_compatibility_fixed"
            if summary["status"] == "fail"
            else "review_and_migrate_alias_usage"
            if summary["status"] == "warn"
            else "compatible"
        ),
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
        f"- deprecated_alias_present: `{report['deprecated_alias_present']}`",
        f"- errors: `{report['error_count']}`",
        f"- warnings: `{report['warning_count']}`",
        f"- info: `{report['info_count']}`",
        f"- reviewer_recommendation: `{report['reviewer_recommendation']}`",
        "",
        "## Issues",
        "",
        "| Severity | Code | Message |",
        "|---|---|---|",
    ]
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"| {issue['severity']} | {issue['code']} | {issue['message']} |")
    else:
        lines.append("| none | none | none |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check review bundle manifest compatibility")
    parser.add_argument("--manifest", type=Path, required=True, help="Path to review_bundle_manifest.json")
    parser.add_argument("--out-json", type=Path, required=True, help="Output JSON report path")
    parser.add_argument("--out-md", type=Path, required=True, help="Output Markdown report path")
    parser.add_argument("--fail-on-warn", action="store_true", help="Return non-zero when status is warn")
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = build_compatibility_report(manifest, str(args.manifest))

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_compatibility_markdown(report), encoding="utf-8")

    print(json.dumps({"status": report["status"], "warnings": report["warning_count"], "errors": report["error_count"]}))
    if report["status"] == "fail":
        return 1
    if report["status"] == "warn" and args.fail_on_warn:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
