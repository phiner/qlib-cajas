"""Tests for EURUSD language boundary validation report."""

from __future__ import annotations

from pathlib import Path

from cajas.reports.validation_eurusd_language_boundary import build_language_boundary_report


def test_language_boundary_ready_with_required_docs(tmp_path: Path):
    policy = tmp_path / "policy.md"
    kickoff = tmp_path / "kickoff.md"
    roadmap = tmp_path / "roadmap.md"
    policy.write_text(
        "\n".join(
            [
                "English runtime: schema keys, CLI flags, status enums.",
                "Chinese semantic: human rationale, counterexample, future LLM guidance.",
                "Use _zh names like human_rationale_zh and supporting_observations_zh.",
                "Prohibited: Chinese schema keys, Chinese CLI flags, Chinese enum values.",
            ]
        ),
        encoding="utf-8",
    )
    kickoff.write_text("See cajas/docs/eurusd_review_language_policy.md", encoding="utf-8")
    roadmap.write_text("See cajas/docs/eurusd_review_language_policy.md", encoding="utf-8")

    report = build_language_boundary_report(policy_doc=policy, kickoff_doc=kickoff, roadmap_doc=roadmap)
    assert report["status"] == "language_boundary_ready"
    assert report["checks"]["machine_identifiers_english"] is True


def test_language_boundary_blocked_on_missing_docs(tmp_path: Path):
    report = build_language_boundary_report(
        policy_doc=tmp_path / "missing_policy.md",
        kickoff_doc=tmp_path / "missing_kickoff.md",
        roadmap_doc=tmp_path / "missing_roadmap.md",
    )
    assert report["status"] == "blocked"
    assert report["reason"] == "missing_required_docs"
