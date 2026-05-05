"""Tests for EURUSD zh rationale fields validation report."""

from pathlib import Path

from cajas.reports.validation_eurusd_zh_rationale_fields import build_zh_rationale_fields_report


def test_zh_rationale_fields_report_ready(tmp_path: Path) -> None:
    policy = tmp_path / "policy.md"
    app = tmp_path / "app.py"
    helper = tmp_path / "helper.py"
    policy.write_text(
        "\n".join(
            [
                "human_rationale_zh",
                "human_counterexample_zh",
                "human_uncertainty_reason_zh",
                "human_context_notes_zh",
            ]
        ),
        encoding="utf-8",
    )
    app.write_text(
        "\n".join(
            [
                "human_rationale_zh",
                "human_counterexample_zh",
                "human_uncertainty_reason_zh",
                "human_context_notes_zh",
                "Human rationale (ZH) / 人工判断理由",
                "Counterexample notes (ZH) / 反例/否定理由",
                "Uncertainty reason (ZH) / 不确定原因",
                "Context notes (ZH) / 上下文备注",
            ]
        ),
        encoding="utf-8",
    )
    helper.write_text(
        "\n".join(
            [
                "human_rationale_zh",
                "human_counterexample_zh",
                "human_uncertainty_reason_zh",
                "human_context_notes_zh",
            ]
        ),
        encoding="utf-8",
    )
    report = build_zh_rationale_fields_report(policy_doc_path=policy, app_path=app, helper_path=helper)
    assert report["status"] == "zh_rationale_fields_ready"


def test_zh_rationale_fields_report_blocked_on_missing_path(tmp_path: Path) -> None:
    report = build_zh_rationale_fields_report(
        policy_doc_path=tmp_path / "missing_policy.md",
        app_path=tmp_path / "missing_app.py",
        helper_path=tmp_path / "missing_helper.py",
    )
    assert report["status"] == "blocked"
    assert report["reason"] == "missing_required_paths"
