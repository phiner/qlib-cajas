"""Validation gate summary helpers for CI/reviewer automation."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ValidationGate:
    name: str
    required: bool
    status: str  # pass|warn|fail|not_run
    reason_code: str
    action: str
    summary: str
    artifact_json: str | None = None
    artifact_md: str | None = None


DEFAULT_CI_PROFILES = {
    "local": {
        "optional_not_run_affects_status": False,
        "optional_warn_affects_status": False,
    },
    "ci": {
        "optional_not_run_affects_status": False,
        "optional_warn_affects_status": True,
    },
    "strict": {
        "optional_not_run_affects_status": True,
        "optional_warn_affects_status": True,
    },
}


def aggregate_gate_status(gates: list[ValidationGate], *, profile: str = "ci") -> str:
    profile_config = DEFAULT_CI_PROFILES.get(profile, DEFAULT_CI_PROFILES["ci"])
    required = [g for g in gates if g.required]
    all_gates = gates or []
    if any(g.status == "fail" for g in required) or any(g.status == "fail" for g in all_gates):
        return "fail"
    if any(g.status == "warn" for g in required):
        return "warn"
    if any(g.status == "not_run" for g in required):
        return "warn"
    if profile_config["optional_warn_affects_status"] and any((not g.required) and g.status == "warn" for g in all_gates):
        return "warn"
    if profile_config["optional_not_run_affects_status"] and any((not g.required) and g.status == "not_run" for g in all_gates):
        return "warn"
    return "pass"


def build_final_status_payload(
    *,
    gates: list[ValidationGate],
    bundle_name: str,
    created_at: str | None,
    git_branch: str,
    git_commit: str,
    profile: str = "ci",
    command: str | None = None,
) -> dict[str, Any]:
    created = created_at or datetime.now(timezone.utc).isoformat()
    overall = aggregate_gate_status(gates, profile=profile)
    gate_dicts = [asdict(gate) for gate in gates]
    blocking = [g for g in gate_dicts if g["status"] == "fail" and (g["required"] or True)]
    warning = [g for g in gate_dicts if g["status"] == "warn"]
    optional_or_not_run = [g for g in gate_dicts if (not g["required"]) and g["status"] in {"warn", "not_run"}]
    primary_gate = blocking[0] if blocking else warning[0] if warning else gate_dicts[0] if gate_dicts else None
    primary_reason = primary_gate["summary"] if primary_gate else "all configured gates passed"
    primary_artifact = None
    if primary_gate:
        primary_artifact = primary_gate.get("artifact_md") or primary_gate.get("artifact_json")
    reviewer_next_action = "none"
    if overall == "fail":
        reviewer_next_action = "fix"
    elif overall == "warn":
        reviewer_next_action = "review"
    return {
        "schema_version": "v1",
        "run_id": str(uuid4()),
        "bundle_name": bundle_name,
        "created_at": created,
        "git_branch": git_branch,
        "git_commit": git_commit,
        "profile": profile,
        "command": command,
        "overall_status": overall,
        "overall_reason": primary_reason,
        "blocking_gates": blocking,
        "warning_gates": warning,
        "optional_or_not_run_gates": optional_or_not_run,
        "reviewer_next_action": reviewer_next_action,
        "primary_artifact": primary_artifact,
        "gates": gate_dicts,
    }


def render_final_status_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation Final Status",
        "",
        f"- bundle_name: `{payload.get('bundle_name', 'unknown')}`",
        f"- created_at: `{payload.get('created_at', 'unknown')}`",
        f"- run_id: `{payload.get('run_id', 'unknown')}`",
        f"- profile: `{payload.get('profile', 'ci')}`",
        f"- git_branch: `{payload.get('git_branch', 'unknown')}`",
        f"- git_commit: `{payload.get('git_commit', 'unknown')}`",
        "",
        f"Overall status: `{payload.get('overall_status', 'warn')}`",
        "",
        f"Primary reason: {payload.get('overall_reason', 'unknown')}",
        f"Reviewer next action: `{payload.get('reviewer_next_action', 'review')}`",
        f"Primary artifact: `{payload.get('primary_artifact')}`",
        "",
        "## CI Gate Summary",
        "",
        "| Gate | Required | Status | Reason | Action | Summary | Artifact JSON | Artifact MD |",
        "|---|---:|---|---|---|---|---|---|",
    ]
    for gate in payload.get("gates", []):
        lines.append(
            f"| {gate.get('name', 'unknown')} | "
            f"{'yes' if gate.get('required') else 'no'} | "
            f"{gate.get('status', 'not_run')} | "
            f"{gate.get('reason_code', '')} | "
            f"{gate.get('action', '')} | "
            f"{gate.get('summary', '')} | "
            f"{gate.get('artifact_json') or ''} | "
            f"{gate.get('artifact_md') or ''} |"
        )
    lines.append("")
    return "\n".join(lines)
