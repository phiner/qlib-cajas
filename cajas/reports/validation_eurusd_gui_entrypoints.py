"""Validate EURUSD pattern-review vs market-state GUI entrypoint separation."""

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


def build_eurusd_gui_entrypoints_report(
    *,
    pattern_launcher: Path,
    pattern_app: Path,
    market_state_launcher: Path,
    market_state_app: Path,
    kickoff_doc: Path,
    roadmap_doc: Path,
    trial_approval_json: Path,
) -> dict[str, Any]:
    blocking_reasons: list[str] = []

    pattern_launcher_text = pattern_launcher.read_text(encoding="utf-8") if pattern_launcher.exists() else ""
    pattern_app_text = pattern_app.read_text(encoding="utf-8") if pattern_app.exists() else ""
    market_state_launcher_text = market_state_launcher.read_text(encoding="utf-8") if market_state_launcher.exists() else ""
    market_state_app_text = market_state_app.read_text(encoding="utf-8") if market_state_app.exists() else ""
    kickoff_text = kickoff_doc.read_text(encoding="utf-8") if kickoff_doc.exists() else ""
    roadmap_text = roadmap_doc.read_text(encoding="utf-8") if roadmap_doc.exists() else ""

    pattern_review_command = "./scripts/run_eurusd_review_gui.sh"
    pattern_review_app_path = "cajas/apps/eurusd_pattern_review_app.py"
    pattern_review_purpose = "final sample-level human review"
    pattern_review_has_final_human_label = all(
        token in pattern_app_text
        for token in [
            "EURUSD Pattern Review / EURUSD 形态审核",
            "final sample-level labels",
            "Overall Human Review / 总体人工审核",
            "human_label",
            "human_confidence",
        ]
    )

    market_state_command = "./scripts/run_eurusd_market_state_inspection_gui.sh"
    market_state_app_path = "cajas/apps/eurusd_market_state_inspection_app.py"
    market_state_purpose = "layer/state inspection"
    market_state_has_layer_tabs = 'st.tabs(["P3", "M8", "M24", "M128", "Local", "Notes"])' in market_state_app_text
    market_state_local_explained = all(
        token in market_state_app_text
        for token in [
            "layer feedback only unless explicitly wired to final review",
            "P3/M8/M24/M128/Local are layer evidence fields.",
            "Local = immediate local structure around the target candle.",
            "do not replace the final sample-level human_label in the Pattern Review GUI.",
        ]
    )

    apps_have_distinct_titles = all(
        token in pattern_app_text
        for token in [
            "EURUSD Pattern Review / EURUSD 形态审核",
            "final sample-level labels · CSV/JSONL persistence · no LLM · no trading",
        ]
    ) and all(
        token in market_state_app_text
        for token in [
            "EURUSD 四层市场状态图表审阅",
            "layer feedback only unless explicitly wired to final review",
        ]
    )

    docs_disambiguate_apps = all(
        token in (kickoff_text + "\n" + roadmap_text)
        for token in [
            "./scripts/run_eurusd_review_gui.sh",
            "./scripts/run_eurusd_market_state_inspection_gui.sh",
            "Use Pattern Review GUI for final human sample review.",
            "Use Market-State Inspection GUI only for layer/state inspection unless explicitly stated.",
            "human_label belongs to final sample-level review.",
            "P3/M8/M24/M128/Local are evidence layers.",
        ]
    )

    if pattern_review_app_path not in pattern_launcher_text:
        blocking_reasons.append("pattern_review_launcher_mismatch")
    if market_state_app_path not in market_state_launcher_text:
        blocking_reasons.append("market_state_launcher_mismatch")
    if not pattern_review_has_final_human_label:
        blocking_reasons.append("pattern_review_final_label_copy_missing")
    if not market_state_has_layer_tabs:
        blocking_reasons.append("market_state_layer_tabs_missing")
    if not market_state_local_explained:
        blocking_reasons.append("market_state_local_explanation_missing")
    if not apps_have_distinct_titles:
        blocking_reasons.append("gui_titles_not_distinct")
    if not docs_disambiguate_apps:
        blocking_reasons.append("docs_do_not_disambiguate_apps")

    trial_payload = _load_json(trial_approval_json) or {}
    trial_status = str(trial_payload.get("status", "not_approved"))
    if trial_status != "not_approved":
        blocking_reasons.append(f"trial_approval_must_be_not_approved:{trial_status}")

    report_status = "gui_entrypoints_clear" if not blocking_reasons else "blocked"
    return {
        "report_status": report_status,
        "pattern_review_command": pattern_review_command,
        "pattern_review_app_path": pattern_review_app_path,
        "pattern_review_purpose": pattern_review_purpose,
        "pattern_review_has_final_human_label": pattern_review_has_final_human_label,
        "market_state_command": market_state_command,
        "market_state_app_path": market_state_app_path,
        "market_state_purpose": market_state_purpose,
        "market_state_has_layer_tabs": market_state_has_layer_tabs,
        "market_state_local_explained": market_state_local_explained,
        "apps_have_distinct_titles": apps_have_distinct_titles,
        "docs_disambiguate_apps": docs_disambiguate_apps,
        "trial_approval_status": trial_status,
        "blocking_reasons": blocking_reasons,
    }


def render_eurusd_gui_entrypoints_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD GUI Entrypoints",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- pattern_review_command: `{report.get('pattern_review_command')}`",
        f"- pattern_review_app_path: `{report.get('pattern_review_app_path')}`",
        f"- pattern_review_purpose: `{report.get('pattern_review_purpose')}`",
        f"- pattern_review_has_final_human_label: `{report.get('pattern_review_has_final_human_label')}`",
        f"- market_state_command: `{report.get('market_state_command')}`",
        f"- market_state_app_path: `{report.get('market_state_app_path')}`",
        f"- market_state_purpose: `{report.get('market_state_purpose')}`",
        f"- market_state_has_layer_tabs: `{report.get('market_state_has_layer_tabs')}`",
        f"- market_state_local_explained: `{report.get('market_state_local_explained')}`",
        f"- apps_have_distinct_titles: `{report.get('apps_have_distinct_titles')}`",
        f"- docs_disambiguate_apps: `{report.get('docs_disambiguate_apps')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        "## Blocking Reasons",
        "",
    ]
    reasons = report.get("blocking_reasons") or []
    if reasons:
        lines.extend([f"- {item}" for item in reasons])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
