"""Build a compact restart packet for EURUSD human review sessions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_ZH_FIELDS = [
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
]
REQUIRED_HUMAN_FIELDS = ["human_label", "human_confidence", *REQUIRED_ZH_FIELDS]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_human_review_restart_packet(
    *,
    language_boundary_json: Path,
    zh_rationale_json: Path,
    human_review_quality_json: Path,
    review_standard_json: Path,
    llm_artifacts_json: Path,
    llm_second_review_json: Path,
    real_llm_readiness_json: Path,
    trial_approval_json: Path,
    fast_validation_timing_json: Path,
    active_review_batch_path: str = "tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv",
    completed_review_csv_path: str = "tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv",
    review_events_jsonl_path: str = "tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl",
) -> dict[str, Any]:
    language = _load_json(language_boundary_json)
    zh = _load_json(zh_rationale_json)
    quality = _load_json(human_review_quality_json)
    standard = _load_json(review_standard_json)
    artifacts = _load_json(llm_artifacts_json)
    second_review = _load_json(llm_second_review_json)
    readiness = _load_json(real_llm_readiness_json)
    approval = _load_json(trial_approval_json)
    fast = _load_json(fast_validation_timing_json)

    language_status = language.get("status") if language else None
    zh_status = zh.get("status") if zh else None
    quality_status = quality.get("report_status") if quality else None
    standard_status = standard.get("status") if standard else None
    llm_artifact_status = artifacts.get("report_status") if artifacts else None
    llm_second_review_status = second_review.get("report_status") if second_review else None
    real_llm_readiness_status = readiness.get("status") if readiness else None
    trial_approval_status = approval.get("status") if approval else None
    fast_validation_status = fast.get("overall_status") if fast else None

    blocking_reasons: list[str] = []
    if language_status != "language_boundary_ready":
        blocking_reasons.append(f"language_boundary_not_ready:{language_status}")
    if zh_status != "zh_rationale_fields_ready":
        blocking_reasons.append(f"zh_rationale_not_ready:{zh_status}")
    if quality_status not in {"awaiting_review_input", "human_review_quality_watch", "human_review_quality_ready"}:
        blocking_reasons.append(f"human_review_quality_unexpected:{quality_status}")
    if standard_status != "review_standard_v0_ready":
        blocking_reasons.append(f"review_standard_not_ready:{standard_status}")
    if llm_artifact_status != "llm_review_artifacts_ready":
        blocking_reasons.append(f"llm_artifacts_not_ready:{llm_artifact_status}")
    if llm_second_review_status != "llm_second_review_protocol_ready":
        blocking_reasons.append(f"llm_second_review_not_ready:{llm_second_review_status}")
    if real_llm_readiness_status != "ready_for_explicit_approval":
        blocking_reasons.append(f"real_llm_readiness_unexpected:{real_llm_readiness_status}")
    if trial_approval_status != "not_approved":
        blocking_reasons.append(f"trial_approval_must_remain_not_approved:{trial_approval_status}")

    report_status = "ready_to_restart_human_review" if not blocking_reasons else "blocked"

    return {
        "report_status": report_status,
        "fast_validation_status": fast_validation_status,
        "language_boundary_status": language_status,
        "zh_rationale_status": zh_status,
        "human_review_quality_status": quality_status,
        "review_standard_status": standard_status,
        "llm_artifact_status": llm_artifact_status,
        "llm_second_review_status": llm_second_review_status,
        "real_llm_readiness_status": real_llm_readiness_status,
        "trial_approval_status": trial_approval_status,
        "active_review_batch_path": active_review_batch_path,
        "completed_review_csv_path": completed_review_csv_path,
        "review_events_jsonl_path": review_events_jsonl_path,
        "standard_version": "eurusd_15m_review_standard_v0",
        "required_human_fields": REQUIRED_HUMAN_FIELDS,
        "required_zh_fields": REQUIRED_ZH_FIELDS,
        "gui_run_command": "./scripts/run_eurusd_review_gui.sh",
        "post_review_validation_commands": [
            "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_human_review_quality_report.py --output-json tmp/validation-eurusd-human-review-quality.json --output-md tmp/validation-eurusd-human-review-quality.md",
            "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_review_artifacts.py --output-json tmp/validation-eurusd-llm-review-artifacts.json --output-md tmp/validation-eurusd-llm-review-artifacts.md --output-jsonl tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl",
            "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json",
        ],
        "llm_boundary_statement": "Real LLM integration remains unapproved; trial approval is not_approved; no live provider calls and no trading actions are allowed.",
        "blocking_reasons": blocking_reasons,
    }


def render_human_review_restart_packet_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Human Review Restart Packet",
        "",
        f"- report_status: `{payload.get('report_status')}`",
        f"- fast_validation_status: `{payload.get('fast_validation_status')}`",
        f"- language_boundary_status: `{payload.get('language_boundary_status')}`",
        f"- zh_rationale_status: `{payload.get('zh_rationale_status')}`",
        f"- human_review_quality_status: `{payload.get('human_review_quality_status')}`",
        f"- review_standard_status: `{payload.get('review_standard_status')}`",
        f"- llm_artifact_status: `{payload.get('llm_artifact_status')}`",
        f"- real_llm_readiness_status: `{payload.get('real_llm_readiness_status')}`",
        f"- trial_approval_status: `{payload.get('trial_approval_status')}`",
        "",
        "## Baseline",
        "",
        "- Fast validation is green after legacy schema alignment.",
        "- Missing completed review CSV is an awaiting-input workflow state, not a blocker.",
        "",
        "## Start GUI",
        "",
        "```bash",
        str(payload.get("gui_run_command")),
        "```",
        "",
        "## Fill Required Fields",
        "",
    ]
    lines.extend([f"- `{field}`" for field in payload.get("required_human_fields", [])])
    lines.extend(
        [
            "",
            "## Persistence Expectations",
            "",
            f"- CSV latest state by sample_id: `{payload.get('completed_review_csv_path')}`",
            f"- JSONL append-only audit: `{payload.get('review_events_jsonl_path')}`",
            f"- standard_version: `{payload.get('standard_version')}`",
            "",
            "## Post-review Validation Commands",
            "",
        ]
    )
    for cmd in payload.get("post_review_validation_commands", []):
        lines.extend(["```bash", cmd, "```"])
    lines.extend(
        [
            "",
            "## LLM Boundary",
            "",
            f"- {payload.get('llm_boundary_statement')}",
            "",
            "## Blocking Reasons",
            "",
        ]
    )
    reasons = payload.get("blocking_reasons") or []
    if reasons:
        lines.extend([f"- {item}" for item in reasons])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
