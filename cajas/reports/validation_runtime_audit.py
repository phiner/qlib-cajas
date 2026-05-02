"""Validation runtime audit helpers."""

from __future__ import annotations

import ast
import re
from pathlib import Path

REQUIRED_MARKERS = ["unit", "integration", "smoke", "slow", "closure", "full"]
SMOKE_FILE_RE = re.compile(r"test_run_.*_smoke\.py$")


def _extract_markers(tree: ast.AST) -> set[str]:
    markers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
            if isinstance(node.value.value, ast.Name) and node.value.value.id == "pytest":
                if node.value.attr == "mark":
                    markers.add(node.attr)
    return markers


def _uses_subprocess(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                return True
    return False


def _referenced_smoke_scripts(text: str) -> list[str]:
    found = sorted(set(re.findall(r"run_[a-z0-9_]*_smoke\.py", text)))
    return found


def _load_test_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    markers = _extract_markers(tree)
    smoke_refs = _referenced_smoke_scripts(text)
    return {
        "path": path.as_posix(),
        "markers": sorted(markers),
        "is_smoke_file": bool(SMOKE_FILE_RE.search(path.name)),
        "uses_subprocess": _uses_subprocess(tree),
        "referenced_smoke_scripts": smoke_refs,
    }


def build_validation_runtime_audit(*, tests_root: str | Path) -> dict:
    root = Path(tests_root).expanduser().resolve()
    files = sorted(root.glob("test_*.py"))
    records = [_load_test_file(path) for path in files]

    marker_counts = {"unmarked": 0}
    for marker in REQUIRED_MARKERS:
        marker_counts[marker] = 0

    heavy_name_matches: list[str] = []
    nested_smoke_calls: list[str] = []
    subprocess_cli_files: list[str] = []

    recommendations: list[dict[str, str]] = []
    for rec in records:
        markers = set(rec["markers"])
        if not markers:
            marker_counts["unmarked"] += 1
        for marker in REQUIRED_MARKERS:
            if marker in markers:
                marker_counts[marker] += 1

        if rec["is_smoke_file"]:
            heavy_name_matches.append(rec["path"])
            if "smoke" not in markers or "slow" not in markers:
                recommendations.append(
                    {
                        "path": rec["path"],
                        "action": "add smoke+slow markers",
                    }
                )
            if "full_research_stack" in rec["path"] or "research_quality_loop" in rec["path"] or "research_remediation" in rec["path"]:
                if "full" not in markers:
                    recommendations.append({"path": rec["path"], "action": "consider full marker"})
            if "final_reproducibility_closure" in rec["path"] or "governance_review_closure" in rec["path"]:
                if "closure" not in markers:
                    recommendations.append({"path": rec["path"], "action": "consider closure marker"})

        if rec["uses_subprocess"]:
            subprocess_cli_files.append(rec["path"])
        if rec["referenced_smoke_scripts"]:
            nested_smoke_calls.append(rec["path"])

    recommendations = sorted({(x["path"], x["action"]) for x in recommendations})

    return {
        "schema_version": "v1",
        "tests_root": root.as_posix(),
        "pytest_collection_count": len(records),
        "tests_by_marker": marker_counts,
        "heavy_naming_matches": heavy_name_matches,
        "nested_smoke_call_files": nested_smoke_calls,
        "subprocess_cli_workflow_files": subprocess_cli_files,
        "recommended_actions": [{"path": p, "action": a} for p, a in recommendations],
    }


def render_validation_runtime_audit_md(*, report: dict) -> str:
    lines = [
        "# Validation Runtime Audit",
        "",
        f"- tests_root: `{report.get('tests_root')}`",
        f"- pytest_collection_count: `{report.get('pytest_collection_count')}`",
        "",
        "## Marker Counts",
    ]
    for k, v in sorted(report.get("tests_by_marker", {}).items()):
        lines.append(f"- {k}: `{v}`")

    lines += ["", "## Heavy Naming Matches"]
    for path in report.get("heavy_naming_matches", []):
        lines.append(f"- `{path}`")

    lines += ["", "## Nested Smoke Call Files"]
    for path in report.get("nested_smoke_call_files", []):
        lines.append(f"- `{path}`")

    lines += ["", "## Subprocess CLI Workflow Files"]
    for path in report.get("subprocess_cli_workflow_files", []):
        lines.append(f"- `{path}`")

    lines += ["", "## Recommendations"]
    actions = report.get("recommended_actions", [])
    if not actions:
        lines.append("- none")
    else:
        for item in actions:
            lines.append(f"- `{item.get('path')}`: {item.get('action')}")
    return "\n".join(lines) + "\n"
