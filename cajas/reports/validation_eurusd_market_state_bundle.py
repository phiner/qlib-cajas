"""Consolidated bundle status for EURUSD market-state artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _status(path: Path, key: str = "report_status", default: str = "missing") -> str:
    if not path.exists():
        return default
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get(key, default))
    except Exception:
        return "invalid"


def build_market_state_bundle_report(output_json: Path) -> dict[str, Any]:
    base = output_json.parent
    market = _status(base / "validation-eurusd-market-state.json")
    cal = _status(base / "validation-eurusd-market-state-calibration.json")
    rules = _status(base / "validation-eurusd-micro-pattern-rules.json")
    noise = _status(base / "validation-eurusd-micro-noise-profile.json")
    packet = _status(base / "validation-eurusd-micro-pattern-review-packet.json")
    manual = _status(base / "validation-eurusd-micro-pattern-manual-labels.json")
    candidates = _status(base / "validation-eurusd-micro-pattern-rule-candidates.json")
    qlib_contract = _status(base / "validation-eurusd-market-state-qlib-adapter-contract.json")
    quality = _status(base / "validation-eurusd-market-state-dataset-quality.json")
    inspection_packet = _status(base / "validation-eurusd-market-state-inspection-packet.json")
    cleanup_plan = _status(base / "validation-tmp-artifact-cleanup-plan.json")
    readiness = _status(base / "validation-eurusd-real-llm-integration-readiness.json", key="status")
    trial = _status(base / "validation-eurusd-llm-trial-approval.json", key="approval_status")

    blocking = []
    watch = []
    for name, s in [
        ("market_state", market),
        ("calibration", cal),
        ("micro_pattern_rules", rules),
        ("micro_noise_profile", noise),
        ("review_packet", packet),
        ("inspection_packet", inspection_packet),
        ("qlib_adapter_contract", qlib_contract),
        ("dataset_quality", quality),
    ]:
        if s in {"blocked", "missing", "invalid"}:
            blocking.append(f"{name}:{s}")
        elif s.endswith("_watch"):
            watch.append(f"{name}:{s}")
    if cleanup_plan in {"blocked", "missing", "invalid"}:
        watch.append(f"tmp_cleanup_plan:{cleanup_plan}")
    if manual in {"awaiting_manual_micro_pattern_labels", "manual_micro_pattern_labels_watch", "missing"}:
        watch.append(f"manual_labels:{manual}")
    if candidates in {"awaiting_manual_labels", "rule_candidates_watch", "missing"}:
        watch.append(f"rule_candidates:{candidates}")
    if trial != "not_approved":
        blocking.append(f"trial_approval_status:{trial}")

    if blocking:
        status = "blocked"
    elif watch:
        status = "market_state_bundle_watch"
    else:
        status = "market_state_bundle_ready"

    return {
        "report_status": status,
        "market_state_status": market,
        "calibration_status": cal,
        "micro_pattern_rules_status": rules,
        "micro_noise_profile_status": noise,
        "review_packet_status": packet,
        "manual_labels_status": manual,
        "rule_candidates_status": candidates,
        "qlib_adapter_contract_status": qlib_contract,
        "dataset_quality_status": quality,
        "inspection_packet_status": inspection_packet,
        "tmp_cleanup_plan_status": cleanup_plan,
        "real_llm_readiness_status": readiness,
        "trial_approval_status": trial,
        "tmp_cleanup_plan_dry_run_only": True,
        "blocking_reasons": blocking,
        "watch_reasons": watch,
        "recommended_next_phase": "manual_label_micro_pattern_packet" if watch else "review_market_state_bundle_then_wire_gui",
    }


def render_market_state_bundle_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# EURUSD Market-state Bundle",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- recommended_next_phase: `{report.get('recommended_next_phase')}`",
        f"- watch_reasons: {report.get('watch_reasons')}",
        f"- blocking_reasons: {report.get('blocking_reasons')}",
    ]) + "\n"
