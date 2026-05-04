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
    helper_path = Path("cajas/research/eurusd_pattern_review_gui.py")
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
        "",
        "## Recommendation",
        "",
        f"`{report['recommendation']}`"
    ])
    
    return "\n".join(lines)
