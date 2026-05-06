"""EURUSD 15m pattern review GUI validation report."""
import importlib.util
from pathlib import Path
from typing import Any, Dict


def build_gui_validation_report(
    app_path: Path,
    clean_view_csv: Path,
    review_batch_csv: Path,
    completed_output_csv: Path
) -> Dict[str, Any]:
    """Build GUI validation report."""
    launcher_path = Path("scripts/run_eurusd_review_gui.sh")
    language_policy_path = Path("cajas/docs/eurusd_review_language_policy.md")
    helper_path = Path("cajas/research/eurusd_pattern_review_gui.py")
    required_zh_fields = [
        "human_rationale_zh",
        "human_counterexample_zh",
        "human_uncertainty_reason_zh",
        "human_context_notes_zh",
    ]
    required_core_handoff_fields = [
        "human_label",
        "human_confidence",
    ]
    run_command = "./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_pattern_review_app.py"
    launcher_command = "./scripts/run_eurusd_review_gui.sh"

    # Check app exists
    if not app_path.exists():
        return {
            "status": "blocked",
            "reason": "app_path_missing",
            "app_path": str(app_path),
            "helper_path": str(helper_path),
            "launcher_path": str(launcher_path),
            "language_policy_path": str(language_policy_path),
            "streamlit_available": False,
            "plotly_available": False,
            "clean_view_path": str(clean_view_csv),
            "review_batch_path": str(review_batch_csv),
            "completed_output_path": str(completed_output_csv),
            "can_import_app": False,
            "can_import_helper": False,
            "forbidden_trading_column_policy": "blocked_on_save",
            "run_command": run_command,
            "launcher_command": launcher_command,
            "recommendation": "create_gui_app"
        }

    # Check helper module
    if not helper_path.exists():
        return {
            "status": "blocked",
            "reason": "helper_path_missing",
            "app_path": str(app_path),
            "helper_path": str(helper_path),
            "launcher_path": str(launcher_path),
            "language_policy_path": str(language_policy_path),
            "streamlit_available": False,
            "plotly_available": False,
            "clean_view_path": str(clean_view_csv),
            "review_batch_path": str(review_batch_csv),
            "completed_output_path": str(completed_output_csv),
            "can_import_app": False,
            "can_import_helper": False,
            "forbidden_trading_column_policy": "blocked_on_save",
            "run_command": run_command,
            "launcher_command": launcher_command,
            "recommendation": "create_gui_helper"
        }
    
    # Check imports
    can_import_app = False
    can_import_helper = False
    
    try:
        spec = importlib.util.spec_from_file_location("app", app_path)
        if spec and spec.loader:
            can_import_app = True
    except Exception:
        pass
    
    layout_contract: Dict[str, Any] | None = None
    try:
        from cajas.research import eurusd_pattern_review_gui
        can_import_helper = True
    except Exception:
        pass

    try:
        from cajas.apps.eurusd_pattern_review_app import get_manual_feedback_layout_contract
        layout_contract = get_manual_feedback_layout_contract()
    except Exception:
        layout_contract = None
    
    if not can_import_helper:
        return {
            "status": "blocked",
            "reason": "cannot_import_helper",
            "app_path": str(app_path),
            "helper_path": str(helper_path),
            "launcher_path": str(launcher_path),
            "language_policy_path": str(language_policy_path),
            "streamlit_available": False,
            "plotly_available": False,
            "clean_view_path": str(clean_view_csv),
            "review_batch_path": str(review_batch_csv),
            "completed_output_path": str(completed_output_csv),
            "can_import_app": can_import_app,
            "can_import_helper": can_import_helper,
            "forbidden_trading_column_policy": "blocked_on_save",
            "run_command": run_command,
            "launcher_command": launcher_command,
            "recommendation": "fix_helper_imports"
        }
    
    # Check dependencies
    streamlit_available = False
    plotly_available = False
    
    try:
        import streamlit
        streamlit_available = True
    except ImportError:
        pass
    
    try:
        import plotly
        plotly_available = True
    except ImportError:
        pass
    
    # Check input artifacts
    if not clean_view_csv.exists():
        return {
            "status": "blocked",
            "reason": "clean_view_missing",
            "app_path": str(app_path),
            "helper_path": str(helper_path),
            "launcher_path": str(launcher_path),
            "language_policy_path": str(language_policy_path),
            "streamlit_available": streamlit_available,
            "plotly_available": plotly_available,
            "clean_view_path": str(clean_view_csv),
            "review_batch_path": str(review_batch_csv),
            "completed_output_path": str(completed_output_csv),
            "can_import_app": can_import_app,
            "can_import_helper": can_import_helper,
            "forbidden_trading_column_policy": "blocked_on_save",
            "run_command": run_command,
            "launcher_command": launcher_command,
            "recommendation": "generate_clean_view"
        }

    if not review_batch_csv.exists():
        return {
            "status": "blocked",
            "reason": "review_batch_missing",
            "app_path": str(app_path),
            "helper_path": str(helper_path),
            "launcher_path": str(launcher_path),
            "language_policy_path": str(language_policy_path),
            "streamlit_available": streamlit_available,
            "plotly_available": plotly_available,
            "clean_view_path": str(clean_view_csv),
            "review_batch_path": str(review_batch_csv),
            "completed_output_path": str(completed_output_csv),
            "can_import_app": can_import_app,
            "can_import_helper": can_import_helper,
            "forbidden_trading_column_policy": "blocked_on_save",
            "run_command": run_command,
            "launcher_command": launcher_command,
            "recommendation": "generate_review_batch"
        }
    
    helper_text = helper_path.read_text(encoding="utf-8")
    app_text = app_path.read_text(encoding="utf-8")
    zh_fields_known_by_helper = all(field in helper_text for field in required_zh_fields)
    zh_fields_exposed_in_gui = all(field in app_text for field in required_zh_fields)
    core_handoff_fields_exposed_in_gui = all(field in app_text for field in required_core_handoff_fields)
    zh_bilingual_labels_present = all(
        token in app_text
        for token in [
            "Overall human label / 总体人工判断",
            "Overall confidence / 总体置信度",
            "Human rationale (ZH) / 人工判断理由",
            "Counterexample notes (ZH) / 反例/否定理由",
            "Uncertainty reason (ZH) / 不确定原因",
            "Context notes (ZH) / 上下文备注",
        ]
    )
    overall_review_section_present = all(
        token in app_text
        for token in [
            "##### Overall Human Review / 总体人工审核",
            "Overall fields are the final sample-level human decision.",
            "Multi-layer evidence below is supporting detail only.",
            "##### Multi-Layer Evidence Review / 多尺度证据审核",
        ]
    )
    active_render_path_checked = bool(layout_contract and layout_contract.get("active_render_path_checked") is True)
    overall_review_section_visible = bool(layout_contract and layout_contract.get("overall_review_section_visible") is True)
    overall_review_before_detail_tabs = bool(layout_contract and layout_contract.get("overall_review_before_detail_tabs") is True)
    overall_fields_outside_detail_tabs = bool(layout_contract and layout_contract.get("overall_fields_outside_detail_tabs") is True)
    overall_field_names = list((layout_contract or {}).get("overall_field_names", []))
    detail_tab_names = list((layout_contract or {}).get("detail_tab_names", []))
    unified_review_gui_enabled = bool(layout_contract and layout_contract.get("unified_review_gui_enabled") is True)
    multi_layer_evidence_section_visible = bool(layout_contract and layout_contract.get("multi_layer_evidence_section_visible") is True)
    p3_layer_visible = bool(layout_contract and layout_contract.get("p3_layer_visible") is True)
    m8_layer_visible = bool(layout_contract and layout_contract.get("m8_layer_visible") is True)
    m24_layer_visible = bool(layout_contract and layout_contract.get("m24_layer_visible") is True)
    m128_layer_visible = bool(layout_contract and layout_contract.get("m128_layer_visible") is True)
    local_layer_visible = bool(layout_contract and layout_contract.get("local_layer_visible") is True)
    overall_fields_before_layer_fields = bool(layout_contract and layout_contract.get("overall_fields_before_layer_fields") is True)
    layer_fields_supporting_evidence_explained = bool(layout_contract and layout_contract.get("layer_fields_supporting_evidence_explained") is True)
    canonical_save_includes_overall_fields = bool(layout_contract and layout_contract.get("canonical_save_includes_overall_fields") is True)
    canonical_save_includes_layer_fields = bool(layout_contract and layout_contract.get("canonical_save_includes_layer_fields") is True)
    jsonl_audit_includes_standard_version = bool(layout_contract and layout_contract.get("jsonl_audit_includes_standard_version") is True)
    trial_approval_status = str((layout_contract or {}).get("trial_approval_status", "not_approved"))
    local_is_detail_only = bool(layout_contract and layout_contract.get("local_is_detail_only") is True)
    pattern_3_is_detail_only = bool(layout_contract and layout_contract.get("pattern_3_is_detail_only") is True)
    launcher_targets_active_app = bool(
        layout_contract
        and str(layout_contract.get("app_path", "")) in app_text
        and str(layout_contract.get("launcher_path", "")).endswith("run_eurusd_review_gui.sh")
    )
    candidate_context_visible = bool(layout_contract and layout_contract.get("candidate_context_visible") is True)
    candidate_type_visible = bool(layout_contract and layout_contract.get("candidate_type_visible") is True)
    candidate_type_source = str((layout_contract or {}).get("candidate_type_source", ""))
    target_candle_context_visible = bool(layout_contract and layout_contract.get("target_candle_context_visible") is True)
    layer_guide_visible = bool(layout_contract and layout_contract.get("layer_guide_visible") is True)
    local_layer_explained = bool(
        "Local：目标K线周围的局部结构质量，用来判断当前候选是否有局部支撑。" in app_text
        and layout_contract
        and layout_contract.get("local_is_detail_only") is True
    )
    human_label_final_decision_explained = bool(
        "human_label 是当前 candidate_type 的最终人工判断。" in app_text
    )
    detail_layers_marked_supporting_only = bool(
        "Local/P3/M8/M24/M128 是证据层，不是最终结论。" in app_text
    )

    # Determine status
    if not streamlit_available or not plotly_available:
        status = "watch"
        missing_deps = []
        if not streamlit_available:
            missing_deps.append("streamlit")
        if not plotly_available:
            missing_deps.append("plotly")
    else:
        status = "unified_review_gui_ready"
        missing_deps = []
    
    return {
        "status": status,
        "app_path": str(app_path),
        "helper_path": str(helper_path),
        "launcher_path": str(launcher_path),
        "language_policy_path": str(language_policy_path),
        "streamlit_available": streamlit_available,
        "plotly_available": plotly_available,
        "missing_dependencies": missing_deps,
        "clean_view_path": str(clean_view_csv),
        "review_batch_path": str(review_batch_csv),
        "completed_output_path": str(completed_output_csv),
        "can_import_app": can_import_app,
        "can_import_helper": can_import_helper,
        "forbidden_trading_column_policy": "blocked_on_save",
        "run_command": run_command,
        "launcher_command": launcher_command,
        "language_boundary_policy_status": "documented" if language_policy_path.exists() else "missing",
        "required_zh_fields": required_zh_fields,
        "required_core_handoff_fields": required_core_handoff_fields,
        "zh_rationale_fields_known_by_helper": zh_fields_known_by_helper,
        "zh_rationale_fields_exposed_in_gui": zh_fields_exposed_in_gui,
        "core_handoff_fields_exposed_in_gui": core_handoff_fields_exposed_in_gui,
        "zh_bilingual_labels_present": zh_bilingual_labels_present,
        "overall_review_section_present": overall_review_section_present,
        "active_render_path_checked": active_render_path_checked,
        "launcher_targets_active_app": launcher_targets_active_app,
        "unified_review_gui_enabled": unified_review_gui_enabled,
        "overall_review_section_visible": overall_review_section_visible,
        "multi_layer_evidence_section_visible": multi_layer_evidence_section_visible,
        "p3_layer_visible": p3_layer_visible,
        "m8_layer_visible": m8_layer_visible,
        "m24_layer_visible": m24_layer_visible,
        "m128_layer_visible": m128_layer_visible,
        "local_layer_visible": local_layer_visible,
        "overall_review_before_detail_tabs": overall_review_before_detail_tabs,
        "overall_fields_outside_detail_tabs": overall_fields_outside_detail_tabs,
        "overall_fields_before_layer_fields": overall_fields_before_layer_fields,
        "overall_field_names": overall_field_names,
        "detail_tab_names": detail_tab_names,
        "local_is_detail_only": local_is_detail_only,
        "pattern_3_is_detail_only": pattern_3_is_detail_only,
        "candidate_context_visible": candidate_context_visible,
        "candidate_type_visible": candidate_type_visible,
        "candidate_type_source": candidate_type_source,
        "target_candle_context_visible": target_candle_context_visible,
        "layer_guide_visible": layer_guide_visible,
        "local_layer_explained": local_layer_explained,
        "human_label_final_decision_explained": human_label_final_decision_explained,
        "layer_fields_supporting_evidence_explained": layer_fields_supporting_evidence_explained,
        "canonical_save_includes_overall_fields": canonical_save_includes_overall_fields,
        "canonical_save_includes_layer_fields": canonical_save_includes_layer_fields,
        "jsonl_audit_includes_standard_version": jsonl_audit_includes_standard_version,
        "detail_layers_marked_supporting_only": detail_layers_marked_supporting_only,
        "trial_approval_status": trial_approval_status,
        "layout_contract": layout_contract or {},
        "recommendation": "run_local_review_app" if status == "unified_review_gui_ready" else "install_gui_dependencies"
    }


def format_gui_validation_markdown(report: Dict[str, Any]) -> str:
    """Format GUI validation report as markdown."""
    lines = [
        "# EURUSD 15m Pattern Review GUI Validation",
        "",
        f"**Status**: `{report['status']}`",
        "",
        "## Paths",
        "",
        f"- App: `{report['app_path']}`",
        f"- Helper: `{report['helper_path']}`",
        f"- Clean view: `{report['clean_view_path']}`",
        f"- Launcher: `{report['launcher_path']}`",
        f"- Language policy: `{report['language_policy_path']}`",
        f"- Review batch: `{report['review_batch_path']}`",
        f"- Completed output: `{report['completed_output_path']}`",
        "",
        "## Dependencies",
        "",
        f"- Streamlit available: {report['streamlit_available']}",
        f"- Plotly available: {report['plotly_available']}",
    ]
    
    if report.get("missing_dependencies"):
        lines.extend([
            "",
            "### Missing Dependencies",
            "",
            "Install with:",
            "```bash",
            f"pip install {' '.join(report['missing_dependencies'])}",
            "```"
        ])
    
    lines.extend([
        "",
        "## Import Status",
        "",
        f"- Can import app: {report['can_import_app']}",
        f"- Can import helper: {report['can_import_helper']}",
        "",
        "## Run Command",
        "",
        "```bash",
        report['run_command'],
        "```",
        "",
        "```bash",
        report["launcher_command"],
        "```",
        "",
        "## Policy",
        "",
        f"- Forbidden trading columns: `{report['forbidden_trading_column_policy']}`",
        f"- Language boundary policy: `{report.get('language_boundary_policy_status', 'unknown')}`",
        f"- ZH rationale fields known by helper: `{report.get('zh_rationale_fields_known_by_helper')}`",
        f"- ZH rationale fields exposed in GUI: `{report.get('zh_rationale_fields_exposed_in_gui')}`",
        f"- Core handoff fields exposed in GUI: `{report.get('core_handoff_fields_exposed_in_gui')}`",
        f"- ZH bilingual labels present: `{report.get('zh_bilingual_labels_present')}`",
        "",
        "## Recommendation",
        "",
        f"`{report['recommendation']}`"
    ])
    
    return "\n".join(lines)
