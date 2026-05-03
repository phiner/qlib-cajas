import json

from cajas.reports.validation_pytest_runtime_profile import (
    build_validation_pytest_runtime_profile_report,
    render_validation_pytest_runtime_profile_markdown,
)


def test_runtime_profile_parses_summary_and_slowest_entries() -> None:
    sample = """
======================== slowest durations ========================
3.21s call     cajas/tests/test_alpha.py::test_a
2.00s call     cajas/tests/test_alpha.py::test_b
1.50s call     cajas/tests/test_beta.py::test_c
================ 488 passed, 16 deselected in 109.78s =================
"""
    payload = build_validation_pytest_runtime_profile_report(pytest_output=sample, total_seconds=109.788, top_n=25)
    assert payload["test_summary"]["passed"] == 488
    assert payload["test_summary"]["deselected"] == 16
    assert payload["test_summary"]["failed"] is None
    assert payload["slowest_tests"][0]["nodeid"].endswith("test_alpha.py::test_a")
    assert payload["slowest_files"][0]["file"].endswith("test_alpha.py")
    assert payload["slowest_files"][0]["test_count"] == 2
    md = render_validation_pytest_runtime_profile_markdown(payload)
    assert "Slowest Tests" in md
    assert "Scope Boundary" in md


def test_runtime_profile_handles_failed_summary_variant() -> None:
    sample = "=== 1 failed, 487 passed, 16 deselected in 100.00s ==="
    payload = build_validation_pytest_runtime_profile_report(pytest_output=sample, total_seconds=100.0, top_n=5)
    assert payload["test_summary"]["failed"] == 1
    assert payload["test_summary"]["passed"] == 487
    assert payload["test_summary"]["total_reported"] == 504


def test_runtime_profile_handles_minimal_summary_variant() -> None:
    sample = "=== 10 passed in 0.50s ==="
    payload = build_validation_pytest_runtime_profile_report(pytest_output=sample, total_seconds=0.5, top_n=3)
    assert payload["test_summary"]["passed"] == 10
    assert payload["test_summary"]["deselected"] is None
    assert payload["test_summary"]["total_reported"] == 10


def test_runtime_profile_missing_output_is_compatible() -> None:
    payload = build_validation_pytest_runtime_profile_report(pytest_output="", total_seconds=0.1, top_n=3)
    assert payload["test_summary"]["passed"] is None
    assert payload["slowest_tests"] == []
    assert payload["slowest_files"] == []
    assert json.dumps(payload)
