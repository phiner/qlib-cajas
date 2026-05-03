"""Validation gate summary helpers for CI/reviewer automation."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class ValidationGate:
    name: str
    required: bool
    status: str  # pass|warn|fail|not_run
    summary: str
    artifact_json: str | None = None
    artifact_md: str | None = None


def aggregate_gate_status(gates: list[ValidationGate]) -> str:
    required = [g for g in gates if g.required]
    all_gates = gates or []
    if any(g.status == "fail" for g in required) or any(g.status == "fail" for g in all_gates):
        return "fail"
    if any(g.status in {"warn", "not_run"} for g in required):
        return "warn"
    if any(g.status == "warn" for g in all_gates):
        return "warn"
    return "pass"


def build_final_status_payload(
    *,
    gates: list[ValidationGate],
    bundle_name: str,
    created_at: str,
    git_branch: str,
    git_commit: str,
) -> dict[str, Any]:
    return {
        "bundle_name": bundle_name,
        "created_at": created_at,
        "git_branch": git_branch,
        "git_commit": git_commit,
        "overall_status": aggregate_gate_status(gates),
        "gates": [asdict(gate) for gate in gates],
    }


def render_final_status_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation Final Status",
        "",
        f"- bundle_name: `{payload.get('bundle_name', 'unknown')}`",
        f"- created_at: `{payload.get('created_at', 'unknown')}`",
        f"- git_branch: `{payload.get('git_branch', 'unknown')}`",
        f"- git_commit: `{payload.get('git_commit', 'unknown')}`",
        f"- overall_status: `{payload.get('overall_status', 'warn')}`",
        "",
        "## CI Gate Summary",
        "",
        "| Gate | Required | Status | Summary | Artifact JSON | Artifact MD |",
        "|---|---:|---|---|---|---|",
    ]
    for gate in payload.get("gates", []):
        lines.append(
            f"| {gate.get('name', 'unknown')} | "
            f"{'yes' if gate.get('required') else 'no'} | "
            f"{gate.get('status', 'not_run')} | "
            f"{gate.get('summary', '')} | "
            f"{gate.get('artifact_json') or ''} | "
            f"{gate.get('artifact_md') or ''} |"
        )
    lines.append("")
    return "\n".join(lines)
