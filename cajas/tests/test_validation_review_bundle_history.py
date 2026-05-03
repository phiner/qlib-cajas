"""Tests for validation review bundle history tracking."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.validation_review_bundle_history import (
    BundleHistorySnapshot,
    create_snapshot_from_bundle,
    append_snapshot,
    read_snapshots,
    compute_delta,
    detect_regressions,
    generate_history_summary_markdown,
)


class ValidationReviewBundleHistoryTests(unittest.TestCase):
    """Test validation review bundle history tracking."""

    def test_snapshot_includes_required_fields(self) -> None:
        """Test snapshot includes all required fields."""
        snapshot = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T00:00:00Z",
            branch="test-branch",
            commit="abc123",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="pass",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=90.0,
            pytest_fast_seconds=87.0,
            dataset_quality_status="pass",
            dataset_quality_score=85.0,
            contract_status="pass",
            contract_error_count=0,
            semantic_error_count=0,
            drift_breaking_count=0,
            data_source_read_csv_count=29,
            present_artifact_count=5,
            missing_required_count=0,
            missing_optional_count=2,
            reviewer_notes=[],
        )

        self.assertEqual(snapshot.snapshot_version, "v1")
        self.assertEqual(snapshot.branch, "test-branch")
        self.assertEqual(snapshot.fast_total_seconds, 90.0)
        self.assertEqual(snapshot.data_source_read_csv_count, 29)

    def test_append_and_read_jsonl(self) -> None:
        """Test append and read JSONL works."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            history_jsonl = tmp_path / "history.jsonl"

            snapshot1 = BundleHistorySnapshot(
                snapshot_version="v1",
                created_at="2026-05-02T00:00:00Z",
                branch="test-branch",
                commit="abc123",
                bundle_name="test_bundle",
                bundle_status=None,
                delivery_packet_status="pass",
                runtime_budget_status="pass",
                reviewer_diff_status=None,
                fast_total_seconds=90.0,
                pytest_fast_seconds=87.0,
                dataset_quality_status=None,
                dataset_quality_score=None,
                contract_status=None,
                contract_error_count=None,
                semantic_error_count=None,
                drift_breaking_count=None,
                data_source_read_csv_count=29,
                present_artifact_count=None,
                missing_required_count=None,
                missing_optional_count=None,
                reviewer_notes=[],
            )

            append_snapshot(history_jsonl, snapshot1)
            snapshots = read_snapshots(history_jsonl)

            self.assertEqual(len(snapshots), 1)
            self.assertEqual(snapshots[0].branch, "test-branch")
            self.assertEqual(snapshots[0].fast_total_seconds, 90.0)

    def test_summary_with_one_snapshot_has_no_delta(self) -> None:
        """Test summary with one snapshot has no previous delta."""
        snapshot = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T00:00:00Z",
            branch="test-branch",
            commit="abc123",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="pass",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=90.0,
            pytest_fast_seconds=87.0,
            dataset_quality_status=None,
            dataset_quality_score=None,
            contract_status=None,
            contract_error_count=None,
            semantic_error_count=None,
            drift_breaking_count=None,
            data_source_read_csv_count=29,
            present_artifact_count=None,
            missing_required_count=None,
            missing_optional_count=None,
            reviewer_notes=[],
        )

        markdown = generate_history_summary_markdown([snapshot], last_n=10)

        self.assertIn("Latest Bundle Status", markdown)
        self.assertNotIn("Delta from Previous", markdown)
        self.assertIn("First snapshot", markdown)

    def test_summary_with_two_snapshots_computes_delta(self) -> None:
        """Test summary with two snapshots computes runtime delta."""
        snapshot1 = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T00:00:00Z",
            branch="test-branch",
            commit="abc123",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="pass",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=100.0,
            pytest_fast_seconds=97.0,
            dataset_quality_status=None,
            dataset_quality_score=None,
            contract_status=None,
            contract_error_count=None,
            semantic_error_count=None,
            drift_breaking_count=None,
            data_source_read_csv_count=29,
            present_artifact_count=None,
            missing_required_count=None,
            missing_optional_count=None,
            reviewer_notes=[],
        )

        snapshot2 = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T01:00:00Z",
            branch="test-branch",
            commit="def456",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="pass",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=90.0,
            pytest_fast_seconds=87.0,
            dataset_quality_status=None,
            dataset_quality_score=None,
            contract_status=None,
            contract_error_count=None,
            semantic_error_count=None,
            drift_breaking_count=None,
            data_source_read_csv_count=29,
            present_artifact_count=None,
            missing_required_count=None,
            missing_optional_count=None,
            reviewer_notes=[],
        )

        delta = compute_delta(snapshot2, snapshot1)

        self.assertIn("fast_total_delta", delta)
        self.assertEqual(delta["fast_total_delta"], -10.0)

        markdown = generate_history_summary_markdown([snapshot1, snapshot2], last_n=10)

        self.assertIn("Delta from Previous", markdown)
        self.assertIn("fast_total_delta", markdown)

    def test_pass_to_warn_regression_detected(self) -> None:
        """Test pass → warn regression is detected."""
        snapshot1 = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T00:00:00Z",
            branch="test-branch",
            commit="abc123",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="pass",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=90.0,
            pytest_fast_seconds=87.0,
            dataset_quality_status=None,
            dataset_quality_score=None,
            contract_status=None,
            contract_error_count=None,
            semantic_error_count=None,
            drift_breaking_count=None,
            data_source_read_csv_count=29,
            present_artifact_count=None,
            missing_required_count=None,
            missing_optional_count=None,
            reviewer_notes=[],
        )

        snapshot2 = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T01:00:00Z",
            branch="test-branch",
            commit="def456",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="warn",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=90.0,
            pytest_fast_seconds=87.0,
            dataset_quality_status=None,
            dataset_quality_score=None,
            contract_status=None,
            contract_error_count=None,
            semantic_error_count=None,
            drift_breaking_count=None,
            data_source_read_csv_count=29,
            present_artifact_count=None,
            missing_required_count=None,
            missing_optional_count=None,
            reviewer_notes=[],
        )

        regressions = detect_regressions(snapshot2, snapshot1)

        self.assertEqual(len(regressions), 1)
        self.assertIn("delivery_packet_status", regressions[0])
        self.assertIn("pass → warn", regressions[0])

    def test_read_csv_count_increase_detected(self) -> None:
        """Test read_csv_count increase is detected."""
        snapshot1 = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T00:00:00Z",
            branch="test-branch",
            commit="abc123",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="pass",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=90.0,
            pytest_fast_seconds=87.0,
            dataset_quality_status=None,
            dataset_quality_score=None,
            contract_status=None,
            contract_error_count=None,
            semantic_error_count=None,
            drift_breaking_count=None,
            data_source_read_csv_count=29,
            present_artifact_count=None,
            missing_required_count=None,
            missing_optional_count=None,
            reviewer_notes=[],
        )

        snapshot2 = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T01:00:00Z",
            branch="test-branch",
            commit="def456",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="pass",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=90.0,
            pytest_fast_seconds=87.0,
            dataset_quality_status=None,
            dataset_quality_score=None,
            contract_status=None,
            contract_error_count=None,
            semantic_error_count=None,
            drift_breaking_count=None,
            data_source_read_csv_count=35,
            present_artifact_count=None,
            missing_required_count=None,
            missing_optional_count=None,
            reviewer_notes=[],
        )

        regressions = detect_regressions(snapshot2, snapshot1)

        self.assertEqual(len(regressions), 1)
        self.assertIn("read_csv_count increased by 6", regressions[0])

    def test_markdown_includes_scope_note(self) -> None:
        """Test Markdown includes scope note."""
        snapshot = BundleHistorySnapshot(
            snapshot_version="v1",
            created_at="2026-05-02T00:00:00Z",
            branch="test-branch",
            commit="abc123",
            bundle_name="test_bundle",
            bundle_status=None,
            delivery_packet_status="pass",
            runtime_budget_status="pass",
            reviewer_diff_status=None,
            fast_total_seconds=90.0,
            pytest_fast_seconds=87.0,
            dataset_quality_status=None,
            dataset_quality_score=None,
            contract_status=None,
            contract_error_count=None,
            semantic_error_count=None,
            drift_breaking_count=None,
            data_source_read_csv_count=29,
            present_artifact_count=None,
            missing_required_count=None,
            missing_optional_count=None,
            reviewer_notes=[],
        )

        markdown = generate_history_summary_markdown([snapshot], last_n=10)

        self.assertIn("offline Qlib research infrastructure", markdown)
        self.assertIn("not a trading", markdown)
        self.assertIn("Last 1 Snapshots", markdown)

    def test_create_snapshot_from_bundle(self) -> None:
        """Test create snapshot from bundle artifacts."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bundle_root = tmp_path / "bundle"
            bundle_root.mkdir()

            # Create minimal bundle manifest
            manifest = {
                "bundle_name": "test_bundle",
                "git_branch": "test-branch",
                "git_commit": "abc123",
                "delivery_packet_status": "pass",
                "runtime_budget_status": "pass",
            }
            (bundle_root / "review_bundle_manifest.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            snapshot = create_snapshot_from_bundle(bundle_root)

            self.assertEqual(snapshot.bundle_name, "test_bundle")
            self.assertEqual(snapshot.branch, "test-branch")
            self.assertEqual(snapshot.delivery_packet_status, "pass")


if __name__ == "__main__":
    unittest.main()
