"""Pytest fast runtime profiling report."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _parse_test_summary(text: str) -> dict[str, int | None]:
    def _match(key: str) -> int | None:
        m = re.search(rf"(\d+)\s+{key}", text)
        return int(m.group(1)) if m else None

    passed = _match("passed")
    deselected = _match("deselected")
    failed = _match("failed")
    skipped = _match("skipped")
    xfailed = _match("xfailed")
    xpassed = _match("xpassed")
    errors = _match("error(?:s)?")
    total_reported = None
    if passed is not None:
        total_reported = (
            passed
            + (deselected or 0)
            + (failed or 0)
            + (skipped or 0)
            + (xfailed or 0)
            + (xpassed or 0)
            + (errors or 0)
        )
    return {
        "passed": passed,
        "deselected": deselected,
        "failed": failed,
        "skipped": skipped,
        "xfailed": xfailed,
        "xpassed": xpassed,
        "errors": errors,
        "total_reported": total_reported,
    }


def _parse_slowest_tests(text: str, top_n: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    # Example line: "2.34s call     cajas/tests/test_x.py::test_y"
    pattern = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)s\s+\w+\s+(.+?)\s*$")
    for line in text.splitlines():
        m = pattern.match(line)
        if not m:
            continue
        seconds = float(m.group(1))
        nodeid = m.group(2)
        rows.append({"nodeid": nodeid, "seconds": seconds})
    rows.sort(key=lambda x: float(x["seconds"]), reverse=True)
    return rows[:top_n]


def _aggregate_slowest_files(slowest_tests: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    agg: dict[str, dict[str, Any]] = {}
    for row in slowest_tests:
        nodeid = str(row.get("nodeid", ""))
        file_part = nodeid.split("::", 1)[0] if "::" in nodeid else nodeid
        if not file_part:
            continue
        entry = agg.setdefault(file_part, {"file": file_part, "total_seconds": 0.0, "test_count": 0})
        entry["total_seconds"] += float(row.get("seconds", 0.0))
        entry["test_count"] += 1
    items = list(agg.values())
    items.sort(key=lambda x: float(x["total_seconds"]), reverse=True)
    for item in items:
        item["total_seconds"] = round(float(item["total_seconds"]), 3)
    return items[:top_n]


def build_validation_pytest_runtime_profile_report(
    *,
    pytest_output: str,
    total_seconds: float | None,
    top_n: int,
) -> dict[str, Any]:
    test_summary = _parse_test_summary(pytest_output)
    slowest_tests = _parse_slowest_tests(pytest_output, top_n=top_n)
    slowest_files = _aggregate_slowest_files(slowest_tests, top_n=top_n)

    if slowest_tests and any(float(item["seconds"]) >= 2.0 for item in slowest_tests[:3]):
        recommendation = "optimize_slow_tests"
        status = "warn"
    elif slowest_tests:
        recommendation = "monitor"
        status = "watch"
    else:
        recommendation = "ok"
        status = "watch" if test_summary.get("passed") is None else "pass"

    return {
        "schema_version": "v1",
        "status": status,
        "total_seconds": total_seconds,
        "test_summary": test_summary,
        "slowest_tests": slowest_tests,
        "slowest_files": slowest_files,
        "recommendation": recommendation,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_pytest_runtime_profile_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation Pytest Runtime Profile",
        "",
        f"- Status: `{payload.get('status', 'watch')}`",
        f"- Total seconds: `{payload.get('total_seconds')}`",
        f"- Recommendation: `{payload.get('recommendation', 'monitor')}`",
        f"- Test summary: `{json.dumps(payload.get('test_summary', {}), ensure_ascii=True)}`",
        "",
        "## Slowest Tests",
        "",
    ]
    slowest_tests = payload.get("slowest_tests", [])
    if slowest_tests:
        lines.extend([f"- `{row.get('seconds')}s` `{row.get('nodeid')}`" for row in slowest_tests])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Slowest Files",
            "",
        ]
    )
    slowest_files = payload.get("slowest_files", [])
    if slowest_files:
        lines.extend(
            [
                f"- `{row.get('file')}` total=`{row.get('total_seconds')}s` tests=`{row.get('test_count')}`"
                for row in slowest_files
            ]
        )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
    return "\n".join(lines)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
