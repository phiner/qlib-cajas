"""Build a compact validation delivery packet for handoff/readiness."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess


NO_EXECUTION_BOUNDARIES = [
    "No broker adapters",
    "No live trading",
    "No paper trading execution",
    "No order generation/routing",
    "No position sizing",
    "No PnL optimization",
    "No execution simulation",
    "No network calls in validation",
]


def _load_json(path: str | Path | None, warnings: list[str]) -> dict[str, Any]:
    if path is None:
        warnings.append("missing input path")
        return {}
    p = Path(path).expanduser()
    if not p.exists():
        warnings.append(f"missing input file: {p}")
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive guard
        warnings.append(f"failed to parse json {p}: {exc}")
        return {}


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()


def _git_branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()


def _extract_micro_runtime(runtime_audit: dict[str, Any]) -> float | None:
    timing = runtime_audit.get("timing_summary")
    if isinstance(timing, dict):
        micro = timing.get("micro_smoke_seconds")
        if isinstance(micro, (int, float)):
            return float(micro)
    return None


def build_validation_delivery_packet(
    *,
    fast_timing: str | Path | None,
    data_source_audit: str | Path | None,
    runtime_audit: str | Path | None,
    allow_missing_inputs: bool,
) -> dict[str, Any]:
    warnings: list[str] = []
    fast = _load_json(fast_timing, warnings)
    data = _load_json(data_source_audit, warnings)
    runtime = _load_json(runtime_audit, warnings)

    if warnings and not allow_missing_inputs:
        raise FileNotFoundError("; ".join(warnings))

    fast_total = fast.get("total_seconds")
    fast_pytest = None
    for item in fast.get("results", []):
        if item.get("name") == "pytest_fast":
            fast_pytest = item.get("elapsed_seconds") or item.get("seconds")
            break

    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    reads_full_csv_likely_count = summary.get("reads_full_csv_likely_count")
    high_risk_count = summary.get("high_risk_count", 0)

    packet = {
        "schema_version": "v1",
        "branch": _git_branch(),
        "git_commit": _git_head(),
        "validation_runtime": {
            "fast_total_seconds": fast_total,
            "fast_pytest_seconds": fast_pytest,
            "micro_smoke_seconds": _extract_micro_runtime(runtime),
        },
        "data_source_audit": {
            "reads_full_csv_likely_count": reads_full_csv_likely_count,
            "high_risk_count": high_risk_count,
        },
        "runtime_audit": {
            "fast_subset_test_count": runtime.get("fast_subset_test_count"),
            "pytest_collection_count": runtime.get("pytest_collection_count"),
            "unmarked_subprocess_files": len(runtime.get("unmarked_subprocess_files", [])),
        },
        "validation_tier_commands": {
            "fast": "./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast",
            "quick": "./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick",
            "micro": "./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro",
            "integration": "./.venv-qlib313/bin/python -m pytest cajas/tests -m \"integration and not slow and not smoke\"",
        },
        "known_remaining_risks": [
            "Fast tier runtime can vary across environments.",
            "Remaining CLI/report artifact tests still dominate top slow slots.",
            "Full/closure smoke tiers are intentionally expensive.",
        ],
        "recommended_user_actions": [
            "Run fast tier before each commit.",
            "Run micro smoke before merge or handoff.",
            "Keep data-source audit at reads_full_csv_likely_count <= 2.",
            "Use integration marker runs only when needed.",
        ],
        "no_execution_boundaries": NO_EXECUTION_BOUNDARIES,
        "warnings": warnings,
    }
    return packet


def render_validation_delivery_packet_md(packet: dict[str, Any]) -> str:
    rt = packet.get("validation_runtime", {})
    ds = packet.get("data_source_audit", {})
    ra = packet.get("runtime_audit", {})
    lines = [
        "# Validation Delivery Packet",
        "",
        f"- branch: `{packet.get('branch')}`",
        f"- git_commit: `{packet.get('git_commit')}`",
        "",
        "## Runtime",
        f"- fast_total_seconds: `{rt.get('fast_total_seconds')}`",
        f"- fast_pytest_seconds: `{rt.get('fast_pytest_seconds')}`",
        f"- micro_smoke_seconds: `{rt.get('micro_smoke_seconds')}`",
        "",
        "## Data Source Audit",
        f"- reads_full_csv_likely_count: `{ds.get('reads_full_csv_likely_count')}`",
        f"- high_risk_count: `{ds.get('high_risk_count')}`",
        "",
        "## Runtime Audit",
        f"- fast_subset_test_count: `{ra.get('fast_subset_test_count')}`",
        f"- pytest_collection_count: `{ra.get('pytest_collection_count')}`",
        f"- unmarked_subprocess_files: `{ra.get('unmarked_subprocess_files')}`",
        "",
        "## Validation Commands",
    ]
    for _, cmd in packet.get("validation_tier_commands", {}).items():
        lines.append(f"- `{cmd}`")
    lines += ["", "## Known Remaining Risks"]
    for risk in packet.get("known_remaining_risks", []):
        lines.append(f"- {risk}")
    lines += ["", "## Recommended User Actions"]
    for item in packet.get("recommended_user_actions", []):
        lines.append(f"- {item}")
    lines += ["", "## No-Execution Boundaries"]
    for boundary in packet.get("no_execution_boundaries", []):
        lines.append(f"- {boundary}")
    warnings = packet.get("warnings", [])
    lines += ["", "## Warnings"]
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
