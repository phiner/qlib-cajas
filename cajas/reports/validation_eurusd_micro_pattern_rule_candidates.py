"""Build candidate rule summary from manual micro-pattern labels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_micro_pattern_rule_candidates_report(
    manual_labels_json: Path,
    trial_approval_json: Path,
    completed_labels_csv: Path | None = None,
) -> dict[str, Any]:
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

    candidate_rules: list[str] = []
    suggested_dist: dict[str, int] = {}
    samples_by_candidate_rule: dict[str, list[str]] = {}
    create_rule_yes_count = 0
    insufficient: list[str] = []
    if completed_labels_csv and completed_labels_csv.exists():
        completed = pd.read_csv(completed_labels_csv)
        if not completed.empty and "human_micro_pattern_label" in completed.columns:
            label_mask = completed["human_micro_pattern_label"].fillna("").astype(str).str.strip() != ""
            labeled_df = completed[label_mask].copy()
            if "human_should_create_rule" in labeled_df.columns:
                create_mask = labeled_df["human_should_create_rule"].fillna("").astype(str).str.strip() == "yes"
                create_rule_yes_count = int(create_mask.sum())
                created_df = labeled_df[create_mask].copy()
                if "suggested_event_key" in created_df.columns:
                    created_df["suggested_event_key"] = (
                        created_df["suggested_event_key"].fillna("").astype(str).str.strip()
                    )
                    created_df = created_df[created_df["suggested_event_key"] != ""]
                    if not created_df.empty:
                        suggested_dist = {
                            str(k): int(v)
                            for k, v in created_df["suggested_event_key"].value_counts().to_dict().items()
                        }
                        candidate_rules = sorted(suggested_dist.keys())
                        if "sample_id" in created_df.columns:
                            samples_by_candidate_rule = {
                                key: created_df.loc[
                                    created_df["suggested_event_key"] == key, "sample_id"
                                ]
                                .astype(str)
                                .head(10)
                                .tolist()
                                for key in candidate_rules
                            }
                        insufficient = [key for key, cnt in suggested_dist.items() if cnt < 2]

    report_status = "rule_candidates_watch" if status != "manual_micro_pattern_labels_ready" else "rule_candidates_ready"
    return {
        "report_status": report_status,
        "manual_label_status": status,
        "labeled_row_count": labeled,
        "create_rule_yes_count": create_rule_yes_count,
        "suggested_event_key_distribution": suggested_dist,
        "candidate_rule_count": len(candidate_rules),
        "candidate_rules": candidate_rules,
        "samples_by_candidate_rule": samples_by_candidate_rule,
        "insufficient_evidence_candidates": insufficient,
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
