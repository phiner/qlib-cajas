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
    
    try:
        from cajas.research import eurusd_pattern_review_gui
        can_import_helper = True
    except Exception:
        pass
    
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
            "##### Overall Human Review",
            "Overall Human Review is the final sample-level decision.",
            "Detailed review fields below are supporting context, not a substitute for the final human label.",
        ]
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
        status = "ready"
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
        "recommendation": "run_local_review_app" if status == "ready" else "install_gui_dependencies"
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
