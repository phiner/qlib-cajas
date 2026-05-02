"""Static IO runtime audit for scripts and tmp roots."""

from __future__ import annotations

import re
from pathlib import Path

from cajas.reports.runtime_io_summary import (
    count_files,
    summarize_directory_depth,
    summarize_extension_counts,
    summarize_largest_files,
)

SCAN_PATTERNS = ["rglob(", "glob(", "walk("]
READ_PATTERNS = ["read_csv(", "json.loads(", "read_text(", "open("]
WRITE_PATTERNS = ["to_csv(", "write_text(", "json.dumps(", "open("]


def _scan_script(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return {
        "path": path.as_posix(),
        "uses_recursive_scan": any(x in text for x in SCAN_PATTERNS),
        "uses_rglob": "rglob(" in text,
        "read_hits": sum(text.count(x) for x in READ_PATTERNS),
        "write_hits": sum(text.count(x) for x in WRITE_PATTERNS),
        "calls_smoke_runner": bool(re.search(r"run_[a-z0-9_]*_smoke\.py", text)),
    }


def build_io_runtime_audit(*, project_root: str | Path, tmp_root: str | Path | None = None) -> dict:
    project = Path(project_root).expanduser().resolve()
    script_files = sorted(project.rglob("*.py"))
    script_stats = [_scan_script(path) for path in script_files]

    recursive_scan_scripts = [x["path"] for x in script_stats if x["uses_recursive_scan"]]
    rglob_scripts = [x["path"] for x in script_stats if x["uses_rglob"]]
    nested_smoke_scripts = [x["path"] for x in script_stats if x["calls_smoke_runner"]]

    heavy_write_scripts = sorted(script_stats, key=lambda x: x["write_hits"], reverse=True)[:20]
    heavy_read_scripts = sorted(script_stats, key=lambda x: x["read_hits"], reverse=True)[:20]

    tmp_summary = {}
    if tmp_root is not None:
        tmp = Path(tmp_root).expanduser().resolve()
        tmp_summary = {
            "tmp_root": tmp.as_posix(),
            "file_count": count_files(tmp),
            "extension_counts": summarize_extension_counts(tmp, top_n=20),
            "largest_files": summarize_largest_files(tmp, top_n=20),
            "depth_summary": summarize_directory_depth(tmp),
        }

    recommendations: list[dict] = []
    for path in nested_smoke_scripts:
        recommendations.append({"path": path, "action": "move_to_fixture_or_non_nested_smoke"})
    for path in recursive_scan_scripts:
        recommendations.append({"path": path, "action": "prefer_manifest_cache_over_recursive_scan"})

    return {
        "schema_version": "v1",
        "project_root": project.as_posix(),
        "recursive_scan_scripts": recursive_scan_scripts,
        "rglob_scripts": rglob_scripts,
        "nested_smoke_scripts": nested_smoke_scripts,
        "heavy_read_scripts": heavy_read_scripts,
        "heavy_write_scripts": heavy_write_scripts,
        "tmp_summary": tmp_summary,
        "likely_redundant_patterns": [
            "repeated smoke nesting",
            "repeated recursive file scans",
            "repeated small artifact writes under deep tmp roots",
        ],
        "recommended_actions": recommendations,
    }


def render_io_runtime_audit_md(*, report: dict) -> str:
    lines = [
        "# IO Runtime Audit",
        "",
        f"- project_root: `{report.get('project_root')}`",
        f"- recursive_scan_scripts: `{len(report.get('recursive_scan_scripts', []))}`",
        f"- nested_smoke_scripts: `{len(report.get('nested_smoke_scripts', []))}`",
        "",
        "## Recursive Scan Scripts",
    ]
    for p in report.get("recursive_scan_scripts", [])[:30]:
        lines.append(f"- `{p}`")

    lines += ["", "## Nested Smoke Scripts"]
    for p in report.get("nested_smoke_scripts", [])[:30]:
        lines.append(f"- `{p}`")

    tmp_summary = report.get("tmp_summary", {})
    if tmp_summary:
        lines += ["", "## Tmp Summary"]
        lines.append(f"- tmp_root: `{tmp_summary.get('tmp_root')}`")
        lines.append(f"- file_count: `{tmp_summary.get('file_count')}`")
        depth = tmp_summary.get("depth_summary", {})
        lines.append(f"- max_depth: `{depth.get('max_depth')}`")

    lines += ["", "## Recommendations"]
    recs = report.get("recommended_actions", [])
    if not recs:
        lines.append("- none")
    else:
        for rec in recs[:40]:
            lines.append(f"- `{rec.get('path')}`: {rec.get('action')}")
    return "\n".join(lines) + "\n"
