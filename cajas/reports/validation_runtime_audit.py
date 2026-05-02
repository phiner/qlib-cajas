"""Validation runtime audit helpers."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

REQUIRED_MARKERS = ["unit", "integration", "smoke", "slow", "closure", "full"]
SMOKE_FILE_RE = re.compile(r"test_run_.*_smoke\.py$")
SUSPICIOUS_PATTERN = re.compile(r"(train|training|model|baseline|experiment|dataset|export|smoke|runner|subprocess)", re.IGNORECASE)
EXCLUDED_MARKERS = {"smoke", "slow", "closure", "full", "integration"}


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


def _subprocess_findings(text: str, path: Path) -> list[dict]:
    patterns = [
        ("subprocess.run(", "medium", "mark_integration_or_mock_subprocess"),
        ("subprocess.check_call(", "medium", "mark_integration_or_mock_subprocess"),
        ("subprocess.check_output(", "medium", "mark_integration_or_mock_subprocess"),
        ("os.system(", "high", "replace_with_direct_function_or_mock"),
        ("python cajas/scripts/", "medium", "prefer_direct_function_tests"),
        ("run_fast_validation.py", "high", "mark_integration"),
        ("run_smoke_validation.py", "high", "move_to_smoke_tier"),
    ]
    out: list[dict] = []
    for i, line in enumerate(text.splitlines(), start=1):
        for token, cost, action in patterns:
            if token in line:
                out.append(
                    {
                        "test_file": path.as_posix(),
                        "line": i,
                        "snippet": line.strip()[:200],
                        "suspected_cost": cost,
                        "suggested_action": action,
                    }
                )
                break
    return out


def _calls_main(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "main":
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "main":
                return True
    return False


def _referenced_smoke_scripts(text: str) -> list[str]:
    return sorted(set(re.findall(r"run_[a-z0-9_]*_smoke\.py", text)))


def _referenced_training_runners(text: str) -> list[str]:
    return sorted(set(re.findall(r"run_[a-z0-9_]*(?:train|training|baseline|experiment)[a-z0-9_]*\.py", text)))


def _load_test_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    markers = _extract_markers(tree)
    smoke_refs = _referenced_smoke_scripts(text)
    training_refs = _referenced_training_runners(text)
    return {
        "path": path.as_posix(),
        "name": path.name,
        "markers": sorted(markers),
        "is_smoke_file": bool(SMOKE_FILE_RE.search(path.name)),
        "uses_subprocess": _uses_subprocess(tree),
        "calls_main": _calls_main(tree),
        "referenced_smoke_scripts": smoke_refs,
        "referenced_training_runners": training_refs,
        "suspicious_name": bool(SUSPICIOUS_PATTERN.search(path.name)),
        "subprocess_findings": _subprocess_findings(text, path),
    }


def _recommendation_for_unmarked(rec: dict) -> str:
    name = rec["name"].lower()
    if rec["is_smoke_file"] or rec["referenced_smoke_scripts"]:
        return "move_to_smoke_tier"
    if rec["uses_subprocess"] or rec["calls_main"]:
        return "mark_integration"
    if any(x in name for x in ["train", "training", "baseline", "experiment", "model"]):
        return "mark_slow"
    if any(x in name for x in ["dataset", "export", "runner"]):
        return "mark_integration"
    return "keep_fast"


def build_validation_runtime_audit(*, tests_root: str | Path, fast_expression: str = "not smoke and not slow and not closure and not full and not integration", timing_json: str | Path | None = None) -> dict:
    root = Path(tests_root).expanduser().resolve()
    files = sorted(root.glob("test_*.py"))
    records = [_load_test_file(path) for path in files]

    marker_counts = {"unmarked": 0}
    for marker in REQUIRED_MARKERS:
        marker_counts[marker] = 0

    heavy_name_matches: list[str] = []
    nested_smoke_calls: list[str] = []
    subprocess_cli_files: list[str] = []
    suspicious_unmarked_files: list[str] = []
    unmarked_subprocess_files: list[str] = []
    unmarked_main_call_files: list[str] = []
    unmarked_runner_call_files: list[str] = []

    recommendations: list[tuple[str, str]] = []
    subprocess_findings: list[dict] = []
    fast_subset_count = 0
    excluded_marker_count = 0

    for rec in records:
        markers = set(rec["markers"])
        if not markers:
            marker_counts["unmarked"] += 1
        for marker in REQUIRED_MARKERS:
            if marker in markers:
                marker_counts[marker] += 1

        if not markers.intersection(EXCLUDED_MARKERS):
            fast_subset_count += 1
        else:
            excluded_marker_count += 1

        if rec["is_smoke_file"]:
            heavy_name_matches.append(rec["path"])
            if "smoke" not in markers or "slow" not in markers:
                recommendations.append((rec["path"], "move_to_smoke_tier"))

        if rec["uses_subprocess"]:
            subprocess_cli_files.append(rec["path"])
        subprocess_findings.extend(rec.get("subprocess_findings", []))
        if rec["referenced_smoke_scripts"]:
            nested_smoke_calls.append(rec["path"])

        if not markers and rec["suspicious_name"]:
            suspicious_unmarked_files.append(rec["path"])
            recommendations.append((rec["path"], _recommendation_for_unmarked(rec)))
        if not markers and rec["uses_subprocess"]:
            unmarked_subprocess_files.append(rec["path"])
            recommendations.append((rec["path"], "mark_integration"))
        if not markers and rec["calls_main"]:
            unmarked_main_call_files.append(rec["path"])
            recommendations.append((rec["path"], "mark_integration"))
        if not markers and (rec["referenced_smoke_scripts"] or rec["referenced_training_runners"]):
            unmarked_runner_call_files.append(rec["path"])
            recommendations.append((rec["path"], "move_to_smoke_tier"))

    timing_payload = None
    if timing_json is not None:
        tj = Path(timing_json).expanduser()
        if tj.exists():
            timing_payload = json.loads(tj.read_text(encoding="utf-8"))

    dedup_recs = sorted(set(recommendations))

    return {
        "schema_version": "v1",
        "tests_root": root.as_posix(),
        "fast_expression": fast_expression,
        "pytest_collection_count": len(records),
        "fast_subset_test_count": fast_subset_count,
        "excluded_marker_count": excluded_marker_count,
        "tests_by_marker": marker_counts,
        "heavy_naming_matches": heavy_name_matches,
        "nested_smoke_call_files": nested_smoke_calls,
        "subprocess_cli_workflow_files": subprocess_cli_files,
        "suspicious_unmarked_files": suspicious_unmarked_files,
        "unmarked_subprocess_files": unmarked_subprocess_files,
        "unmarked_main_call_files": unmarked_main_call_files,
        "unmarked_runner_call_files": unmarked_runner_call_files,
        "recommended_actions": [{"path": p, "action": a} for p, a in dedup_recs],
        "subprocess_findings": subprocess_findings,
        "timing_summary": timing_payload,
    }


def render_validation_runtime_audit_md(*, report: dict) -> str:
    lines = [
        "# Validation Runtime Audit",
        "",
        f"- tests_root: `{report.get('tests_root')}`",
        f"- pytest_collection_count: `{report.get('pytest_collection_count')}`",
        f"- fast_subset_test_count: `{report.get('fast_subset_test_count')}`",
        f"- excluded_marker_count: `{report.get('excluded_marker_count')}`",
        "",
        "## Marker Counts",
    ]
    for k, v in sorted(report.get("tests_by_marker", {}).items()):
        lines.append(f"- {k}: `{v}`")

    lines += ["", "## Suspicious Unmarked Files"]
    items = report.get("suspicious_unmarked_files", [])
    if not items:
        lines.append("- none")
    else:
        for path in items:
            lines.append(f"- `{path}`")

    lines += ["", "## Unmarked Subprocess Files"]
    items = report.get("unmarked_subprocess_files", [])
    if not items:
        lines.append("- none")
    else:
        for path in items:
            lines.append(f"- `{path}`")

    lines += ["", "## Heavy Naming Matches"]
    for path in report.get("heavy_naming_matches", []):
        lines.append(f"- `{path}`")

    lines += ["", "## Recommendations"]
    actions = report.get("recommended_actions", [])
    if not actions:
        lines.append("- none")
    else:
        for item in actions:
            lines.append(f"- `{item.get('path')}`: {item.get('action')}")

    lines += ["", "## Subprocess Findings"]
    findings = report.get("subprocess_findings", [])
    if not findings:
        lines.append("- none")
    else:
        for item in findings[:30]:
            lines.append(
                f"- `{item.get('test_file')}` line `{item.get('line')}` ({item.get('suspected_cost')}): "
                f"{item.get('suggested_action')} | `{item.get('snippet')}`"
            )

    timing = report.get("timing_summary")
    if timing:
        lines += ["", "## Timing JSON Summary"]
        lines.append(f"- tier: `{timing.get('tier')}`")
        lines.append(f"- total_seconds: `{timing.get('total_seconds')}`")
        budget = timing.get("budget", {})
        lines.append(f"- budget_exceeded: `{budget.get('exceeded')}`")

    return "\n".join(lines) + "\n"
