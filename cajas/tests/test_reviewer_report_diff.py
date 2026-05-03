from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.reviewer_report_diff import (
    build_reviewer_diff_report,
    compare_contract_reports,
    compare_dataset_quality_reports,
    generate_reviewer_diff_markdown,
)
from cajas.scripts.build_reviewer_diff_report import main as build_diff_main


class ReviewerReportDiffTests(unittest.TestCase):
    def test_identical_reports_produce_pass(self) -> None:
        """Test identical reports produce pass status."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # Create identical baseline and current
            for root_name in ["baseline", "current"]:
                root = tmp_path / root_name
                (root / "dataset_quality").mkdir(parents=True)
                (root / "contract").mkdir(parents=True)

                dq_report = {
                    "quality_score": {"score": 85.0},
                    "status": "pass",
                }
                (root / "dataset_quality" / "dataset_quality_report.json").write_text(
                    json.dumps(dq_report), encoding="utf-8"
                )

                contract_report = {
                    "status": "pass",
                    "error_count": 0,
                    "semantic_error_count": 0,
                    "drift_summary": {"breaking_count": 0},
                }
                (root / "contract" / "dataset_quality_contract_report.json").write_text(
                    json.dumps(contract_report), encoding="utf-8"
                )

            result = build_reviewer_diff_report(tmp_path / "baseline", tmp_path / "current")
            self.assertEqual(result.overall_status, "pass")
            self.assertEqual(result.quality_score_delta, 0.0)

    def test_quality_score_decrease_produces_warning(self) -> None:
        """Test quality score decrease produces warning."""
        baseline_report = {"quality_score": {"score": 90.0}, "status": "pass"}
        current_report = {"quality_score": {"score": 80.0}, "status": "pass"}

        diff = compare_dataset_quality_reports(baseline_report, current_report)
        self.assertEqual(diff["score_delta"], -10.0)

    def test_contract_status_fail_produces_fail(self) -> None:
        """Test contract status change to fail produces fail."""
        baseline_report = {"status": "pass", "error_count": 0, "semantic_error_count": 0, "drift_summary": {"breaking_count": 0}}
        current_report = {"status": "fail", "error_count": 1, "semantic_error_count": 0, "drift_summary": {"breaking_count": 0}}

        diff = compare_contract_reports(baseline_report, current_report)
        self.assertIsNotNone(diff["status_change"])
        self.assertEqual(diff["status_change"]["current"], "fail")

    def test_semantic_error_increase_detected(self) -> None:
        """Test semantic error increase is detected."""
        baseline_report = {"status": "pass", "error_count": 0, "semantic_error_count": 0, "drift_summary": {"breaking_count": 0}}
        current_report = {"status": "pass", "error_count": 0, "semantic_error_count": 2, "drift_summary": {"breaking_count": 0}}

        diff = compare_contract_reports(baseline_report, current_report)
        self.assertEqual(diff["semantic_error_delta"], 2)

    def test_missing_optional_artifacts_produce_warn(self) -> None:
        """Test missing optional artifacts produce warn, not crash."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # Create minimal baseline and current
            for root_name in ["baseline", "current"]:
                root = tmp_path / root_name
                (root / "dataset_quality").mkdir(parents=True)
                (root / "contract").mkdir(parents=True)

                dq_report = {"quality_score": {"score": 85.0}, "status": "pass"}
                (root / "dataset_quality" / "dataset_quality_report.json").write_text(
                    json.dumps(dq_report), encoding="utf-8"
                )

                contract_report = {
                    "status": "pass",
                    "error_count": 0,
                    "semantic_error_count": 0,
                    "drift_summary": {"breaking_count": 0},
                }
                (root / "contract" / "dataset_quality_contract_report.json").write_text(
                    json.dumps(contract_report), encoding="utf-8"
                )

            result = build_reviewer_diff_report(tmp_path / "baseline", tmp_path / "current")
            # Should not crash, should note missing optional artifacts
            self.assertTrue(any("Runtime budget" in note for note in result.reviewer_notes))

    def test_markdown_includes_key_sections(self) -> None:
        """Test Markdown includes key sections."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            for root_name in ["baseline", "current"]:
                root = tmp_path / root_name
                (root / "dataset_quality").mkdir(parents=True)
                (root / "contract").mkdir(parents=True)

                dq_report = {"quality_score": {"score": 85.0}, "status": "pass"}
                (root / "dataset_quality" / "dataset_quality_report.json").write_text(
                    json.dumps(dq_report), encoding="utf-8"
                )

                contract_report = {
                    "status": "pass",
                    "error_count": 0,
                    "semantic_error_count": 0,
                    "drift_summary": {"breaking_count": 0},
                }
                (root / "contract" / "dataset_quality_contract_report.json").write_text(
                    json.dumps(contract_report), encoding="utf-8"
                )

            result = build_reviewer_diff_report(tmp_path / "baseline", tmp_path / "current")
            markdown = generate_reviewer_diff_markdown(result)

            self.assertIn("Reviewer Diff Report", markdown)
            self.assertIn("offline Qlib research infrastructure artifacts only", markdown)
            self.assertIn("not a trading, execution, alpha, or model performance report", markdown)
            self.assertIn("Executive Summary", markdown)
            self.assertIn("Artifact Presence", markdown)
            self.assertIn("Reviewer Recommendations", markdown)

    def test_cli_writes_json_and_markdown(self) -> None:
        """Test CLI writes JSON and Markdown."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            for root_name in ["baseline", "current"]:
                root = tmp_path / root_name
                (root / "dataset_quality").mkdir(parents=True)
                (root / "contract").mkdir(parents=True)

                dq_report = {"quality_score": {"score": 85.0}, "status": "pass"}
                (root / "dataset_quality" / "dataset_quality_report.json").write_text(
                    json.dumps(dq_report), encoding="utf-8"
                )

                contract_report = {
                    "status": "pass",
                    "error_count": 0,
                    "semantic_error_count": 0,
                    "drift_summary": {"breaking_count": 0},
                }
                (root / "contract" / "dataset_quality_contract_report.json").write_text(
                    json.dumps(contract_report), encoding="utf-8"
                )

            out_json = tmp_path / "diff.json"
            out_md = tmp_path / "diff.md"

            ret = build_diff_main([
                "--baseline-root", str(tmp_path / "baseline"),
                "--current-root", str(tmp_path / "current"),
                "--out-json", str(out_json),
                "--out-md", str(out_md),
                "--warn-only",
            ])

            self.assertEqual(ret, 0)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())

            # Verify JSON is parseable
            report_data = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn("overall_status", report_data)


if __name__ == "__main__":
    unittest.main()
