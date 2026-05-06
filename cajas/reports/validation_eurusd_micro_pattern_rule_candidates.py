"""Build candidate rule summary from manual micro-pattern labels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_micro_pattern_rule_candidates_report(manual_labels_json: Path, trial_approval_json: Path) -> dict[str, Any]:
    manual = _load_json(manual_labels_json)
    if manual is None:
        return {
            "report_status": "blocked",
            "manual_label_status": "missing",
            "labeled_row_count": 0,
            "create_rule_yes_count": 0,
            "suggested_event_key_distribution": {},
            "candidate_rule_count": 0,
            "candidate_rules": [],
            "samples_by_candidate_rule": {},
            "insufficient_evidence_candidates": [],
            "recommended_next_phase": "manual_label_micro_pattern_packet",
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }

    status = str(manual.get("report_status", "awaiting_manual_micro_pattern_labels"))
    labeled = int(manual.get("labeled_row_count", 0))

    trial_status = "not_approved"
    trial_payload = _load_json(trial_approval_json)
    if trial_payload:
        trial_status = str(trial_payload.get("status", "not_approved"))

    if status == "awaiting_manual_micro_pattern_labels" or labeled == 0:
        return {
            "report_status": "awaiting_manual_labels",
            "manual_label_status": status,
            "labeled_row_count": labeled,
            "create_rule_yes_count": 0,
            "suggested_event_key_distribution": {},
            "candidate_rule_count": 0,
            "candidate_rules": [],
            "samples_by_candidate_rule": {},
            "insufficient_evidence_candidates": [],
            "recommended_next_phase": "manual_label_micro_pattern_packet",
            "real_llm_integration_approved": False,
            "trial_approval_status": trial_status,
        }

    # no direct CSV parse here by design; this phase is report scaffold, waits on manual pipeline completion
    report_status = "rule_candidates_watch" if status != "manual_micro_pattern_labels_ready" else "rule_candidates_ready"
    return {
        "report_status": report_status,
        "manual_label_status": status,
        "labeled_row_count": labeled,
        "create_rule_yes_count": 0,
        "suggested_event_key_distribution": {},
        "candidate_rule_count": 0,
        "candidate_rules": [],
        "samples_by_candidate_rule": {},
        "insufficient_evidence_candidates": [],
        "recommended_next_phase": "manual_label_micro_pattern_packet",
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
    }


def render_micro_pattern_rule_candidates_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Micro Pattern Rule Candidates",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- manual_label_status: `{report.get('manual_label_status')}`",
        f"- labeled_row_count: `{report.get('labeled_row_count')}`",
        f"- candidate_rule_count: `{report.get('candidate_rule_count')}`",
        f"- recommended_next_phase: `{report.get('recommended_next_phase')}`",
    ]
    return "\n".join(lines) + "\n"
