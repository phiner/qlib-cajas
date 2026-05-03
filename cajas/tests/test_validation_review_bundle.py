"""Tests for validation review bundle orchestration."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


class ValidationReviewBundleTests(unittest.TestCase):
    """Test validation review bundle orchestration."""

    def _mock_run_command(self, cmd: list[str], description: str) -> tuple[bool, str]:
        """Mock command runner that returns success without running."""
        return True, json.dumps({"status": "ok"})

    def _write_packet_manifest(self, out_root: Path, fast_total: float = 90.0) -> None:
        packet_dir = out_root / "delivery_packet"
        packet_dir.mkdir(parents=True, exist_ok=True)
        packet_manifest = {
            "overall_status": "pass",
            "runtime_budget_status": "pass",
            "reviewer_diff_status": "pass",
            "dataset_quality_status": "pass",
            "dataset_quality_score": 88.0,
            "contract_status": "pass",
            "contract_error_count": 0,
            "semantic_error_count": 0,
            "drift_breaking_count": 0,
            "data_source_audit_read_count": 29,
            "artifact_index": [{"status": "present", "role": "critical"}],
        }
        (packet_dir / "packet_manifest.json").write_text(json.dumps(packet_manifest), encoding="utf-8")

        budget_json = {
            "overall_status": "pass",
            "results": [
                {"component": "fast_total", "observed_seconds": fast_total},
                {"component": "pytest_fast", "observed_seconds": max(fast_total - 3.5, 0.1)},
            ],
        }
        (out_root / "validation_runtime_budget_report.json").write_text(json.dumps(budget_json), encoding="utf-8")

    def test_bundle_manifest_structure(self) -> None:
        """Test bundle manifest has required fields."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )

            out_root = tmp_path / "bundle"

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=False,
                    history_jsonl=None,
                    history_last_n=10,
                    warn_only=True,
                )

            self.assertIn("bundle_name", manifest)
            self.assertIn("created_at", manifest)
            self.assertIn("git_branch", manifest)
            self.assertIn("git_commit", manifest)
            self.assertIn("commands_executed", manifest)
            self.assertIn("commands_skipped", manifest)
            self.assertIn("artifacts", manifest)

    def test_skip_fast_validation_adds_to_skipped(self) -> None:
        """Test skip fast validation adds command to skipped list."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )

            out_root = tmp_path / "bundle"

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=False,
                    history_jsonl=None,
                    history_last_n=10,
                    warn_only=True,
                )

            skipped_commands = [cmd["command"] for cmd in manifest["commands_skipped"]]
            self.assertIn("run_fast_validation.py", skipped_commands)

    def test_baseline_from_current_creates_baseline(self) -> None:
        """Test create baseline from current creates baseline directory."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            contract_file = smoke_root / "contract" / "dataset_quality_contract_report.json"
            contract_file.write_text(json.dumps({"status": "pass"}), encoding="utf-8")

            out_root = tmp_path / "bundle"

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=True,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=False,
                    history_jsonl=None,
                    history_last_n=10,
                    warn_only=True,
                )

            self.assertIn("baseline_root", manifest["artifacts"])
            baseline_root = Path(manifest["artifacts"]["baseline_root"])
            self.assertTrue(baseline_root.exists())
            self.assertTrue((baseline_root / "contract").exists())

    def test_bundle_index_created(self) -> None:
        """Test bundle index markdown is created."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )

            out_root = tmp_path / "bundle"

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=False,
                    history_jsonl=None,
                    history_last_n=10,
                    warn_only=True,
                )

            index_path = out_root / "review_bundle_index.md"
            self.assertTrue(index_path.exists())

            index_content = index_path.read_text(encoding="utf-8")
            self.assertIn("Validation Review Bundle", index_content)
            self.assertIn("Commands Executed", index_content)
            self.assertIn("Commands Skipped", index_content)
            self.assertIn("Generated Artifacts", index_content)
            self.assertIn("Reviewer Next Action", index_content)

    def test_existing_timing_json_triggers_budget_check(self) -> None:
        """Test existing timing JSON triggers runtime budget check."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )

            timing_json = tmp_path / "timing.json"
            timing_json.write_text(
                json.dumps({"total_seconds": 85.0, "results": []}), encoding="utf-8"
            )

            budgets_json = tmp_path / "budgets.json"
            budgets_json.write_text(
                json.dumps({
                    "budgets_seconds": {"fast_total": 100.0},
                    "required_components": ["fast_total"],
                    "optional_components": [],
                }), encoding="utf-8"
            )

            out_root = tmp_path / "bundle"

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=timing_json,
                    budgets=budgets_json,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=False,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=False,
                    history_jsonl=None,
                    history_last_n=10,
                    warn_only=True,
                )

            executed_commands = [cmd["command"] for cmd in manifest["commands_executed"]]
            self.assertTrue(any("check_validation_runtime_budget.py" in cmd for cmd in executed_commands))

    def test_build_experiment_manifest_option(self) -> None:
        """Test build experiment manifest option adds manifest step."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )

            out_root = tmp_path / "bundle"

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=True,
                    copy_artifacts=False,
                    update_history=False,
                    history_jsonl=None,
                    history_last_n=10,
                    warn_only=True,
                )

            executed_commands = [cmd["command"] for cmd in manifest["commands_executed"]]
            self.assertTrue(any("build_qlib_experiment_manifest.py" in cmd for cmd in executed_commands))

    def test_default_bundle_does_not_update_history(self) -> None:
        """Default bundle should not update history artifacts."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )
            out_root = tmp_path / "bundle"
            self._write_packet_manifest(out_root)

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=False,
                    history_jsonl=tmp_path / "history" / "history.jsonl",
                    history_last_n=10,
                    warn_only=True,
                )

            self.assertEqual(manifest["history_update"]["status"], "not_requested")
            self.assertFalse((tmp_path / "history" / "history.jsonl").exists())

    def test_update_history_writes_manifest_and_index_paths(self) -> None:
        """History-enabled run should write history artifacts and index section."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )
            out_root = tmp_path / "bundle"
            self._write_packet_manifest(out_root)
            history_jsonl = tmp_path / "history" / "review_bundle_history.jsonl"

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=True,
                    history_jsonl=history_jsonl,
                    history_last_n=10,
                    warn_only=True,
                )

            self.assertEqual(manifest["history_update"]["status"], "ok")
            self.assertTrue(history_jsonl.exists())
            self.assertIn("history_jsonl", manifest["artifacts"])
            index_text = (out_root / "review_bundle_index.md").read_text(encoding="utf-8")
            self.assertIn("history_jsonl", index_text)
            self.assertIn("reviewer_recommendation", index_text)

    def test_second_history_run_computes_delta(self) -> None:
        """Second history-enabled run should include runtime delta."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )
            out_root = tmp_path / "bundle"
            history_jsonl = tmp_path / "history" / "review_bundle_history.jsonl"

            self._write_packet_manifest(out_root, fast_total=92.0)
            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=True,
                    history_jsonl=history_jsonl,
                    history_last_n=10,
                    warn_only=True,
                )

            self._write_packet_manifest(out_root, fast_total=89.0)
            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=True,
                    history_jsonl=history_jsonl,
                    history_last_n=10,
                    warn_only=True,
                )

            delta = manifest["history_update"]["delta_from_previous"]
            self.assertIn("fast_total_delta", delta)
            self.assertLess(delta["fast_total_delta"], 0)

    def test_history_failure_respects_warn_only(self) -> None:
        """History failures should warn with warn_only and fail without it."""
        from cajas.scripts.build_validation_review_bundle import build_review_bundle

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            smoke_root.mkdir()
            (smoke_root / "contract").mkdir()
            (smoke_root / "contract" / "dataset_quality_contract_report.json").write_text(
                json.dumps({"status": "pass"}), encoding="utf-8"
            )
            out_root = tmp_path / "bundle"
            self._write_packet_manifest(out_root)

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                warn_manifest = build_review_bundle(
                    bundle_name="test_bundle",
                    out_root=out_root,
                    smoke_root=smoke_root,
                    fast_timing_json=None,
                    budgets=None,
                    baseline_root=None,
                    create_baseline_from_current=False,
                    run_fast_validation=False,
                    skip_fast_validation=True,
                    run_data_source_audit=False,
                    skip_data_source_audit=True,
                    data_root=None,
                    build_experiment_manifest=False,
                    copy_artifacts=False,
                    update_history=True,
                    history_jsonl=None,
                    history_last_n=10,
                    warn_only=True,
                )

            self.assertEqual(warn_manifest["history_update"]["status"], "error")
            self.assertTrue(warn_manifest["warnings"])

            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command):
                with self.assertRaises(RuntimeError):
                    build_review_bundle(
                        bundle_name="test_bundle",
                        out_root=out_root,
                        smoke_root=smoke_root,
                        fast_timing_json=None,
                        budgets=None,
                        baseline_root=None,
                        create_baseline_from_current=False,
                        run_fast_validation=False,
                        skip_fast_validation=True,
                        run_data_source_audit=False,
                        skip_data_source_audit=True,
                        data_root=None,
                        build_experiment_manifest=False,
                        copy_artifacts=False,
                        update_history=True,
                        history_jsonl=None,
                        history_last_n=10,
                        warn_only=False,
                    )


if __name__ == "__main__":
    unittest.main()
