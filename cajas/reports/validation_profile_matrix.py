"""Validation profile matrix report builder."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from cajas.reports.validation_gate_summary import (
    DEFAULT_CI_PROFILES,
    ValidationGate,
    _normalize_profile_config,
    aggregate_gate_status,
    _is_gate_escalated,
)


def _count_escalated_gates(gates_data: list[dict[str, Any]]) -> int:
    return sum(1 for g in gates_data if g.get("escalated", False) and g.get("status") != "pass")

def _count_blocking_gates(gates_data: list[dict[str, Any]]) -> int:
    return sum(1 for g in gates_data if g.get("status") == "fail" and g.get("escalated", False))

def _get_next_action(overall: str) -> str:
    if overall == "fail":
        return "fix"
    elif overall == "warn":
        return "review optional warning"
    return "none"


def build_profile_matrix(
    *,
    base_payload: dict[str, Any],
    profile_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-evaluates gates under different profiles to build a matrix report."""
    
    # Load default profiles or provided config
    profiles_def = profile_config.get("profiles", DEFAULT_CI_PROFILES) if profile_config else DEFAULT_CI_PROFILES
    
    # Extract gates from the existing payload
    raw_gates = base_payload.get("gates", [])
    gates = []
    for g in raw_gates:
        # Reconstruct ValidationGate objects
        gates.append(ValidationGate(
            name=g["name"],
            required=g["required"],
            status=g["status"],
            reason_code=g["reason_code"],
            action=g["action"],
            summary=g["summary"],
            artifact_json=g.get("artifact_json"),
            artifact_md=g.get("artifact_md"),
        ))
        
    matrix_profiles: dict[str, Any] = {}
    
    target_profiles = ["local", "ci", "strict"]
    
    for prof in target_profiles:
        prof_cfg = profiles_def.get(prof) or profiles_def.get("ci") or DEFAULT_CI_PROFILES["ci"]
        effective_cfg = _normalize_profile_config(prof_cfg)
        
        overall = aggregate_gate_status(gates, profile=prof, profile_config=effective_cfg)
        
        # Calculate escalated/non-escalated gates
        gate_dicts = []
        for gate in gates:
            row = asdict(gate)
            escalated = _is_gate_escalated(gate, effective_cfg)
            row["escalated"] = escalated
            gate_dicts.append(row)
            
        escalated_warn = _count_escalated_gates(gate_dicts) - _count_blocking_gates(gate_dicts)
        
        non_escalated = [g for g in gate_dicts if g["status"] in {"warn", "not_run"} and not g["escalated"]]
        blocking = [g for g in gate_dicts if g["status"] == "fail" and g["escalated"]]
        
        matrix_profiles[prof] = {
            "overall_status": overall,
            "overall_reason_code": "all_required_gates_passed" if overall == "pass" else "gates_require_review",
            "blocking_gates": blocking,
            "warning_gates": [g for g in gate_dicts if g["status"] == "warn"],
            "non_escalated_warnings": non_escalated,
            "escalated_count": _count_escalated_gates(gate_dicts),
            "blocking_count": _count_blocking_gates(gate_dicts),
            "next_action": _get_next_action(overall)
        }

    status_transitions = []
    for g in gates:
        gate_transition = {"gate": g.name}
        differences = False
        prev_effect = None
        for prof in target_profiles:
            prof_cfg = profiles_def.get(prof) or profiles_def.get("ci") or DEFAULT_CI_PROFILES["ci"]
            effective_cfg = _normalize_profile_config(prof_cfg)
            escalated = _is_gate_escalated(g, effective_cfg)
            
            effect = g.status
            if g.status in ("warn", "not_run"):
                effect = "escalated" if escalated else "non_escalated"
                
            gate_transition[prof] = effect
            if prev_effect is not None and effect != prev_effect:
                differences = True
            prev_effect = effect
            
        if differences:
            status_transitions.append(gate_transition)

    return {
        "schema_version": "v1",
        "profiles": matrix_profiles,
        "status_transitions": status_transitions,
        "recommended_profile": base_payload.get("profile", "local"),
        "reviewer_note": "Matrix compares local, ci, and strict profiles."
    }

def render_profile_matrix_markdown(payload: dict[str, Any]) -> str:
    """Renders profile matrix JSON payload as Markdown."""
    lines = [
        "# Validation Profile Matrix",
        "",
        "> Compares gate evaluation across local, CI, and strict profiles.",
        "",
        "## Profile Outcomes",
        "",
        "| Profile | Overall | Escalated | Blocking | Next action |",
        "|---|---|---:|---:|---|"
    ]
    
    profiles = payload.get("profiles", {})
    for prof in ["local", "ci", "strict"]:
        if prof in profiles:
            p = profiles[prof]
            lines.append(
                f"| {prof} | {p['overall_status']} | {p['escalated_count']} | {p['blocking_count']} | {p['next_action']} |"
            )
            
    lines.append("")
    
    transitions = payload.get("status_transitions", [])
    if transitions:
        lines.append("## Status Transitions")
        lines.append("")
        lines.append("| Gate | local | ci | strict |")
        lines.append("|---|---|---|---|")
        for t in transitions:
            lines.append(f"| {t['gate']} | {t.get('local', '-')} | {t.get('ci', '-')} | {t.get('strict', '-')} |")
        lines.append("")
        
    return "\n".join(lines)
