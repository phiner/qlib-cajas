"""Test EURUSD pattern review GUI validation."""
import pandas as pd
import pytest
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_gui import build_gui_validation_report


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def mock_clean_view(temp_dir):
    df = pd.DataFrame({
        "timestamp": pd.date_range("2020-01-01", periods=10, freq="15min"),
        "open": [1.1] * 10,
        "high": [1.11] * 10,
        "low": [1.09] * 10,
        "close": [1.1] * 10
    })
    path = temp_dir / "clean_view.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def mock_batch(temp_dir):
    df = pd.DataFrame({
        "sample_id": ["s1"],
        "timestamp": pd.to_datetime(["2020-01-01"]),
        "candidate_type": ["test"],
        "review_status": ["pending"]
    })
    path = temp_dir / "batch.csv"
    df.to_csv(path, index=False)
    return path


def test_gui_validation_ready_or_watch(mock_clean_view, mock_batch, temp_dir):
    app_path = Path("cajas/apps/eurusd_pattern_review_app.py")
    completed_path = temp_dir / "completed.csv"
    
    report = build_gui_validation_report(
        app_path=app_path,
        clean_view_csv=mock_clean_view,
        review_batch_csv=mock_batch,
        completed_output_csv=completed_path
    )
    
    # Should be ready or watch depending on streamlit/plotly availability
    assert report["status"] in ["ready", "watch"]
    assert report["can_import_helper"] is True
    assert "run_command" in report
    assert "launcher_path" in report
    assert report["launcher_command"] == "./scripts/run_eurusd_review_gui.sh"
    assert "language_policy_path" in report
    assert report["language_boundary_policy_status"] in {"documented", "missing"}
    assert report["zh_rationale_fields_known_by_helper"] is True
    assert report["zh_rationale_fields_exposed_in_gui"] is True
    assert report["core_handoff_fields_exposed_in_gui"] is True
    assert report["zh_bilingual_labels_present"] is True


def test_gui_validation_blocked_missing_app(mock_clean_view, mock_batch, temp_dir):
    app_path = temp_dir / "missing_app.py"
    completed_path = temp_dir / "completed.csv"
    
    report = build_gui_validation_report(
        app_path=app_path,
        clean_view_csv=mock_clean_view,
        review_batch_csv=mock_batch,
        completed_output_csv=completed_path
    )
    
    assert report["status"] == "blocked"
    assert "app_path_missing" in report["reason"]


def test_gui_validation_blocked_missing_clean_view(mock_batch, temp_dir):
    app_path = Path("cajas/apps/eurusd_pattern_review_app.py")
    clean_view_path = temp_dir / "missing_clean_view.csv"
    completed_path = temp_dir / "completed.csv"
    
    report = build_gui_validation_report(
        app_path=app_path,
        clean_view_csv=clean_view_path,
        review_batch_csv=mock_batch,
        completed_output_csv=completed_path
    )
    
    assert report["status"] == "blocked"
    assert "clean_view_missing" in report["reason"]


def test_gui_validation_blocked_missing_batch(mock_clean_view, temp_dir):
    app_path = Path("cajas/apps/eurusd_pattern_review_app.py")
    batch_path = temp_dir / "missing_batch.csv"
    completed_path = temp_dir / "completed.csv"
    
    report = build_gui_validation_report(
        app_path=app_path,
        clean_view_csv=mock_clean_view,
        review_batch_csv=batch_path,
        completed_output_csv=completed_path
    )
    
    assert report["status"] == "blocked"
    assert "review_batch_missing" in report["reason"]
