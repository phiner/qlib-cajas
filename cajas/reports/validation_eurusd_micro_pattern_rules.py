"""Validation for externalized EURUSD micro-pattern rule library."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_EVENTS = {
    "lower_sweep_reclaim",
    "upper_sweep_reject",
    "three_bar_reversal_up",
    "three_bar_reversal_down",
    "three_bar_exhaustion_up",
    "three_bar_exhaustion_down",
    "failed_followthrough_up",
    "failed_followthrough_down",
    "micro_pause",
    "inside_range_pause",
    "micro_drift_up",
    "micro_drift_down",
    "micro_chop",
    "wick_conflict",
    "micro_compression",
    "micro_noise",
}

ALLOWED_CONDITION_KEYS = {
    "breaks_prior_low",
    "breaks_prior_high",
    "close_returns_inside_prior_range",
    "latest_close_position_min",
    "latest_close_position_max",
    "lower_wick_ratio_min",
    "upper_wick_ratio_min",
    "body_ratio_min",
    "body_ratio_max",
    "three_bar_return_min",
    "three_bar_return_max",
    "three_bar_return_abs_max",
    "range_width_max",
    "range_width_min",
    "range_ratio_3_8_max",
    "consecutive_direction",
    "direction_change",
    "latest_body_direction",
    "volatility_state_3",
    "max_wick_ratio_max",
}


def load_rules_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_rules_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        return ["rules_missing_or_empty"]

    events = set()
    priorities = []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"rule_{i}_not_object")
            continue
        for k in ["pattern_id", "event", "direction", "strength", "priority", "enabled", "description_zh", "conditions", "flags", "rationale_template_zh"]:
            if k not in rule:
                errors.append(f"rule_{i}_missing_{k}")
        cond = rule.get("conditions", {})
        if isinstance(cond, dict):
            invalid_keys = [k for k in cond.keys() if k not in ALLOWED_CONDITION_KEYS]
            if invalid_keys:
                errors.append(f"rule_{i}_invalid_condition_keys:{','.join(sorted(invalid_keys))}")
        else:
            errors.append(f"rule_{i}_conditions_not_object")
        event = str(rule.get("event", ""))
        if event:
            events.add(event)
        priorities.append(rule.get("priority"))
        if not str(rule.get("description_zh", "")).strip():
            errors.append(f"rule_{i}_description_zh_empty")
        if not str(rule.get("rationale_template_zh", "")).strip():
            errors.append(f"rule_{i}_rationale_template_zh_empty")

    missing_events = sorted(REQUIRED_EVENTS - events)
    if missing_events:
        errors.append(f"missing_required_events:{','.join(missing_events)}")

    if len(set(priorities)) != len(priorities):
        errors.append("priority_not_unique")

    return errors


def build_micro_pattern_rules_report(rules_json: Path, trial_approval_json: Path) -> dict[str, Any]:
    if not rules_json.exists():
        return {"report_status": "blocked", "reason": "rules_json_missing", "rules_json": str(rules_json)}

    payload = load_rules_json(rules_json)
    errors = validate_rules_payload(payload)

    rules = payload.get("rules", []) if isinstance(payload.get("rules"), list) else []
    enabled_rules = [r for r in rules if bool(r.get("enabled", False))]
    events = {str(r.get("event", "")) for r in rules}

    trial_status = "not_approved"
    if trial_approval_json.exists():
        trial_payload = json.loads(trial_approval_json.read_text(encoding="utf-8"))
        trial_status = str(trial_payload.get("status", "not_approved"))

    condition_keys_valid = not any(e.startswith("rule_") and "invalid_condition_keys" in e for e in errors)
    missing_required = sorted(REQUIRED_EVENTS - events)

    report_status = "micro_pattern_rules_ready"
    if errors or trial_status != "not_approved":
        report_status = "blocked"

    return {
        "report_status": report_status,
        "rule_version": payload.get("rule_version", "unknown"),
        "rule_count": len(rules),
        "enabled_rule_count": len(enabled_rules),
        "required_events_covered": len(missing_required) == 0,
        "missing_required_events": missing_required,
        "priority_unique": "priority_not_unique" not in errors,
        "condition_keys_valid": condition_keys_valid,
        "english_runtime_keys": True,
        "chinese_semantic_descriptions_present": all(str(r.get("description_zh", "")).strip() for r in rules),
        "catch_all_rules_present": "micro_noise" in events,
        "trading_outputs_excluded": True,
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
        "validation_errors": errors,
    }


def render_micro_pattern_rules_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Micro Pattern Rules Validation",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- rule_version: `{report.get('rule_version')}`",
        f"- rule_count: `{report.get('rule_count')}`",
        f"- enabled_rule_count: `{report.get('enabled_rule_count')}`",
        f"- required_events_covered: `{report.get('required_events_covered')}`",
        f"- priority_unique: `{report.get('priority_unique')}`",
        f"- condition_keys_valid: `{report.get('condition_keys_valid')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        "## Missing Required Events",
        "",
        f"- {report.get('missing_required_events')}",
        "",
        "## Validation Errors",
        "",
    ]
    errs = report.get("validation_errors") or []
    if errs:
        lines.extend([f"- {e}" for e in errs])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
