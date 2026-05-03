"""Validation gate summary helpers for CI/reviewer automation."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
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


def _normalize_profile_config(config: dict[str, Any]) -> dict[str, bool]:
    return {
        "optional_not_run_affects_status": bool(config.get("optional_not_run_affects_status", False)),
        "optional_warn_affects_status": bool(config.get("optional_warn_affects_status", True)),
        "required_warn_affects_status": bool(config.get("required_warn_affects_status", True)),
    }


def load_ci_profile_policy(
    profile: str,
    config_path: str | Path | None = None,
) -> tuple[dict[str, bool], dict[str, Any]]:
    source = "built-in defaults"
    profiles: dict[str, Any] = DEFAULT_CI_PROFILES
    if config_path:
        p = Path(config_path)
        data = json.loads(p.read_text(encoding="utf-8"))
        loaded_profiles = data.get("profiles", {})
        if isinstance(loaded_profiles, dict) and loaded_profiles:
            profiles = loaded_profiles
            source = str(p)
    profile_cfg = profiles.get(profile) or profiles.get("ci") or DEFAULT_CI_PROFILES["ci"]
    normalized = _normalize_profile_config(profile_cfg)
    profile_policy = {
        "source": source,
        "profile": profile if profile in profiles else "ci",
        **normalized,
    }
    return normalized, profile_policy


def _is_gate_escalated(gate: ValidationGate, profile_config: dict[str, bool]) -> bool:
    if gate.status == "fail":
        return True
    if gate.required and gate.status == "warn":
        return profile_config["required_warn_affects_status"]
    if gate.required and gate.status == "not_run":
        return True
    if (not gate.required) and gate.status == "warn":
        return profile_config["optional_warn_affects_status"]
    if (not gate.required) and gate.status == "not_run":
        return profile_config["optional_not_run_affects_status"]
    return False


def _profile_effect(gate: ValidationGate, profile: str, profile_config: dict[str, bool]) -> str:
    if gate.status == "pass":
        return "no_effect"
    if gate.status == "fail":
        return "fail_always_escalated"
    if gate.required and gate.status == "warn":
        return "required_warn_escalated" if profile_config["required_warn_affects_status"] else "required_warn_not_escalated"
    if gate.required and gate.status == "not_run":
        return "required_not_run_escalated"
    if (not gate.required) and gate.status == "warn":
        return (
            f"optional_warn_escalated_under_{profile}"
            if profile_config["optional_warn_affects_status"]
            else f"optional_warn_not_escalated_under_{profile}"
        )
    if (not gate.required) and gate.status == "not_run":
        return (
            f"optional_not_run_escalated_under_{profile}"
            if profile_config["optional_not_run_affects_status"]
            else f"optional_not_run_not_escalated_under_{profile}"
        )
    return "no_effect"


def aggregate_gate_status(
    gates: list[ValidationGate],
    *,
    profile: str = "ci",
    profile_config: dict[str, bool] | None = None,
) -> str:
    profile_config = profile_config or _normalize_profile_config(DEFAULT_CI_PROFILES.get(profile, DEFAULT_CI_PROFILES["ci"]))
    required = [g for g in gates if g.required]
    all_gates = gates or []
    if any(g.status == "fail" for g in required) or any(g.status == "fail" for g in all_gates):
        return "fail"
    if profile_config["required_warn_affects_status"] and any(g.status == "warn" for g in required):
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
    profile_config: dict[str, bool] | None = None,
    profile_policy: dict[str, Any] | None = None,
    command: str | None = None,
) -> dict[str, Any]:
    created = created_at or datetime.now(timezone.utc).isoformat()
    effective_profile_config = profile_config or _normalize_profile_config(DEFAULT_CI_PROFILES.get(profile, DEFAULT_CI_PROFILES["ci"]))
    overall = aggregate_gate_status(gates, profile=profile, profile_config=effective_profile_config)
    gate_dicts = []
    for gate in gates:
        row = asdict(gate)
        escalated = _is_gate_escalated(gate, effective_profile_config)
        row["escalated"] = escalated
        row["profile_effect"] = _profile_effect(gate, profile, effective_profile_config)
        gate_dicts.append(row)
    blocking = [g for g in gate_dicts if g["status"] == "fail" and g["escalated"]]
    warning = [g for g in gate_dicts if g["status"] == "warn"]
    optional_or_not_run = [g for g in gate_dicts if (not g["required"]) and g["status"] in {"warn", "not_run"}]

    reason_candidates = (
        [g for g in gate_dicts if g["required"] and g["status"] == "fail"]
        + [g for g in gate_dicts if g["required"] and g["status"] == "warn" and g["escalated"]]
        + [g for g in gate_dicts if (not g["required"]) and g["status"] == "warn" and g["escalated"]]
        + [g for g in gate_dicts if (not g["required"]) and g["status"] == "not_run" and g["escalated"]]
        + [g for g in gate_dicts if (not g["required"]) and g["status"] == "warn" and (not g["escalated"])]
    )
    primary_gate = reason_candidates[0] if reason_candidates else gate_dicts[0] if gate_dicts else None
    primary_reason = primary_gate["summary"] if primary_gate else "all configured gates passed"
    overall_reason_code = primary_gate["reason_code"] if primary_gate else "all_gates_pass"
    primary_artifact = None
    if primary_gate:
        primary_artifact = primary_gate.get("artifact_md") or primary_gate.get("artifact_json")
    reviewer_next_action = "none"
    if overall == "fail":
        reviewer_next_action = "fix"
    elif overall == "warn":
        reviewer_next_action = "review"
    if primary_gate and not primary_gate.get("escalated", False) and overall == "pass":
        reviewer_next_action = "none"
    return {
        "schema_version": "v1",
        "run_id": str(uuid4()),
        "bundle_name": bundle_name,
        "created_at": created,
        "git_branch": git_branch,
        "git_commit": git_commit,
        "profile": profile,
        "profile_policy": profile_policy or {"source": "built-in defaults", "profile": profile, **effective_profile_config},
        "command": command,
        "overall_status": overall,
        "overall_reason_code": overall_reason_code,
        "overall_reason": primary_reason,
        "blocking_gates": blocking,
        "warning_gates": warning,
        "optional_or_not_run_gates": optional_or_not_run,
        "reviewer_next_action": reviewer_next_action,
        "primary_artifact": primary_artifact,
        "gates": gate_dicts,
    }


def render_final_status_markdown(payload: dict[str, Any]) -> str:
    profile_policy = payload.get("profile_policy", {})
    profile_name = profile_policy.get("profile", payload.get("profile", "ci"))
    optional_warn = bool(profile_policy.get("optional_warn_affects_status", True))
    optional_not_run = bool(profile_policy.get("optional_not_run_affects_status", False))
    profile_explainer = (
        "Optional warnings are visible but do not escalate overall status."
        if not optional_warn
        else "Optional warnings escalate overall status."
    )
    if optional_not_run:
        profile_explainer += " Optional not-run gates escalate status."
    else:
        profile_explainer += " Optional not-run gates do not escalate status."
    lines = [
        "# Validation Final Status",
        "",
        f"- bundle_name: `{payload.get('bundle_name', 'unknown')}`",
        f"- created_at: `{payload.get('created_at', 'unknown')}`",
        f"- run_id: `{payload.get('run_id', 'unknown')}`",
        f"- profile: `{payload.get('profile', 'ci')}`",
        f"- profile_policy_source: `{profile_policy.get('source', 'built-in defaults')}`",
        f"- git_branch: `{payload.get('git_branch', 'unknown')}`",
        f"- git_commit: `{payload.get('git_commit', 'unknown')}`",
        "",
        f"Overall status: `{payload.get('overall_status', 'warn')}`",
        f"Overall reason code: `{payload.get('overall_reason_code', 'unknown')}`",
        "",
        f"Profile: `{profile_name}`",
        profile_explainer,
        "",
        f"Primary reason: {payload.get('overall_reason', 'unknown')}",
        f"Reviewer next action: `{payload.get('reviewer_next_action', 'review')}`",
        f"Primary artifact: `{payload.get('primary_artifact')}`",
        "",
        "## CI Gate Summary",
        "",
        "| Gate | Required | Status | Escalated | Profile Effect | Reason | Action | Summary | Artifact JSON | Artifact MD |",
        "|---|---:|---|---:|---|---|---|---|---|---|",
    ]
    for gate in payload.get("gates", []):
        lines.append(
            f"| {gate.get('name', 'unknown')} | "
            f"{'yes' if gate.get('required') else 'no'} | "
            f"{gate.get('status', 'not_run')} | "
            f"{'yes' if gate.get('escalated') else 'no'} | "
            f"{gate.get('profile_effect', '')} | "
            f"{gate.get('reason_code', '')} | "
            f"{gate.get('action', '')} | "
            f"{gate.get('summary', '')} | "
            f"{gate.get('artifact_json') or ''} | "
            f"{gate.get('artifact_md') or ''} |"
        )
    lines.append("")
    return "\n".join(lines)
