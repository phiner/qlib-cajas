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
            self.assertIn("Timing Consistency", index_content)

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

    def test_review_bundle_records_timing_consistency_from_budget_report(self) -> None:
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
            timing_json.write_text(json.dumps({"total_seconds": 85.0, "results": []}), encoding="utf-8")
            budgets_json = tmp_path / "budgets.json"
            budgets_json.write_text(
                json.dumps(
                    {
                        "budgets_seconds": {"fast_total": 100.0},
                        "required_components": ["fast_total"],
                        "optional_components": [],
                    }
                ),
                encoding="utf-8",
            )
            out_root = tmp_path / "bundle"

            def _mock_with_budget_report(cmd: list[str], description: str) -> tuple[bool, str]:
                if "check_validation_runtime_budget.py" in " ".join(cmd):
                    report_path = out_root / "validation_runtime_budget_report.json"
                    report_path.write_text(
                        json.dumps(
                            {
                                "overall_status": "warn",
                                "budget_status": "pass",
                                "timing_consistency": {
                                    "status": "warn",
                                    "issues": [
                                        {"severity": "warning", "code": "legacy_missing_metadata", "message": "missing created_at"}
                                    ],
                                },
                                "results": [],
                            }
                        ),
                        encoding="utf-8",
                    )
                return True, json.dumps({"status": "ok"})

            with patch("cajas.scripts.build_validation_review_bundle.run_command", _mock_with_budget_report):
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

            self.assertIn("timing_consistency", manifest)
            self.assertEqual(manifest["timing_consistency"]["status"], "warn")
            index_text = (out_root / "review_bundle_index.md").read_text(encoding="utf-8")
            self.assertIn("Timing Consistency", index_text)

    def test_review_bundle_fails_when_timing_consistency_fails_without_warn_only(self) -> None:
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
            timing_json.write_text(json.dumps({"total_seconds": 85.0, "results": []}), encoding="utf-8")
            budgets_json = tmp_path / "budgets.json"
            budgets_json.write_text(
                json.dumps(
                    {
                        "budgets_seconds": {"fast_total": 100.0},
                        "required_components": ["fast_total"],
                        "optional_components": [],
                    }
                ),
                encoding="utf-8",
            )
            out_root = tmp_path / "bundle"

            def _mock_with_budget_fail(cmd: list[str], description: str) -> tuple[bool, str]:
                if "check_validation_runtime_budget.py" in " ".join(cmd):
                    report_path = out_root / "validation_runtime_budget_report.json"
                    report_path.write_text(
                        json.dumps(
                            {
                                "overall_status": "fail",
                                "budget_status": "pass",
                                "timing_consistency": {
                                    "status": "fail",
                                    "issues": [
                                        {"severity": "fail", "code": "required_timing_missing", "message": "missing pytest_fast"}
                                    ],
                                },
                                "results": [],
                            }
                        ),
                        encoding="utf-8",
                    )
                return True, json.dumps({"status": "ok"})

            with patch("cajas.scripts.build_validation_review_bundle.run_command", _mock_with_budget_fail):
                with self.assertRaises(RuntimeError):
                    build_review_bundle(
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
                        warn_only=False,
                    )

    def test_ci_mode_writes_final_status_artifacts(self) -> None:
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
            timing_json.write_text(json.dumps({"total_seconds": 85.0, "results": []}), encoding="utf-8")
            budgets_json = tmp_path / "budgets.json"
            budgets_json.write_text(
                json.dumps({"budgets_seconds": {"fast_total": 100.0}, "required_components": ["fast_total"], "optional_components": []}),
                encoding="utf-8",
            )
            out_root = tmp_path / "bundle"
            self._write_packet_manifest(out_root)

            def _mock_with_budget_pass(cmd: list[str], description: str) -> tuple[bool, str]:
                if "check_validation_runtime_budget.py" in " ".join(cmd):
                    (out_root / "validation_runtime_budget_report.json").write_text(
                        json.dumps(
                            {
                                "overall_status": "pass",
                                "budget_status": "pass",
                                "timing_consistency": {"status": "pass", "issues": []},
                                "results": [],
                            }
                        ),
                        encoding="utf-8",
                    )
                return True, json.dumps({"status": "ok"})

            with patch("cajas.scripts.build_validation_review_bundle.run_command", _mock_with_budget_pass):
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
                    update_history=True,
                    history_jsonl=tmp_path / "history" / "review_bundle_history.jsonl",
                    history_last_n=10,
                    check_manifest_compatibility=True,
                    warn_only=True,
                    ci=True,
                )

            self.assertIn("final_status", manifest)
            self.assertEqual(manifest["final_status"]["overall_status"], "pass")
            self.assertTrue((out_root / "final_status.json").exists())
            self.assertTrue((out_root / "final_status.md").exists())
            index_text = (out_root / "review_bundle_index.md").read_text(encoding="utf-8")
            self.assertIn("CI Gate Summary", index_text)

    def test_ci_mode_requires_timing_or_run_fast_validation(self) -> None:
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
                with self.assertRaises(RuntimeError):
                    build_review_bundle(
                        bundle_name="test_bundle",
                        out_root=out_root,
                        smoke_root=smoke_root,
                        fast_timing_json=None,
                        budgets=tmp_path / "budgets.json",
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
                        warn_only=False,
                        ci=True,
                    )

    def test_main_fail_on_warn_returns_nonzero(self) -> None:
        from cajas.scripts import build_validation_review_bundle as mod

        with patch.object(
            mod,
            "build_review_bundle",
            return_value={
                "commands_executed": [],
                "final_status": {"overall_status": "warn"},
            },
        ):
            ret = mod.main(
                [
                    "--bundle-name",
                    "bundle",
                    "--out-root",
                    "tmp/x-bundle",
                    "--smoke-root",
                    "tmp/x-smoke",
                    "--fail-on-warn",
                ]
            )
            self.assertNotEqual(ret, 0)

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
            self.assertTrue(manifest["history_update"]["deprecated"])
            self.assertEqual(manifest["history_update"]["use"], "history")
            self.assertFalse(manifest["history"]["enabled"])
            self.assertEqual(manifest["history"]["status"], "not_requested")
            self.assertIn("note", manifest["history"])
            self.assertIn("manifest_compatibility", manifest)
            self.assertFalse(manifest["manifest_compatibility"]["enabled"])
            self.assertEqual(manifest["manifest_compatibility"]["status"], "not_requested")
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
            self.assertIn("history", manifest)
            self.assertTrue(manifest["history"]["enabled"])
            self.assertEqual(manifest["history"]["status"], "pass")
            self.assertIn("latest_bundle_status", manifest["history"])
            self.assertIn("runtime_budget_status", manifest["history"])
            self.assertIn("regression_count", manifest["history"])
            index_text = (out_root / "review_bundle_index.md").read_text(encoding="utf-8")
            self.assertIn("History Summary", index_text)
            self.assertIn("History status", index_text)
            self.assertIn("History summary", index_text)
            self.assertNotIn("runtime_delta_from_previous: `{'", index_text)

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

            delta = manifest["history"]["delta_from_previous"]
            self.assertIn("fast_total_delta", delta)
            self.assertLess(delta["fast_total_delta"], 0)
            index_text = (out_root / "review_bundle_index.md").read_text(encoding="utf-8")
            self.assertIn("| Metric | Previous | Current | Delta |", index_text)
            self.assertIn("| fast_total |", index_text)
            self.assertIn("| pytest_fast |", index_text)
            self.assertNotIn("{'fast_total_delta'", index_text)

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
            self.assertEqual(warn_manifest["history"]["status"], "fail")

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

    def test_no_history_mode_has_clean_note(self) -> None:
        """No-history mode should render clean explicit note."""
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

            self.assertFalse(manifest["history"]["enabled"])
            self.assertEqual(manifest["history"]["status"], "not_requested")
            index_text = (out_root / "review_bundle_index.md").read_text(encoding="utf-8")
            self.assertIn("History update was not requested for this bundle.", index_text)

    def test_normalize_history_metadata_falls_back_to_legacy_shape(self) -> None:
        """Normalization should support old manifests with only history_update."""
        from cajas.reports.validation_review_bundle_metadata import normalize_history_metadata

        legacy_manifest = {
            "runtime_budget_status": "pass",
            "history_update": {
                "requested": True,
                "status": "ok",
                "history_jsonl": "tmp/history.jsonl",
                "summary_json": "tmp/history_summary.json",
                "summary_md": "tmp/history_summary.md",
                "latest_bundle_status": "warn",
                "delta_from_previous": {"fast_total_delta": -1.25},
                "regression_count": 0,
                "regressions": [],
                "reviewer_recommendation": "stable_or_improved",
                "latest_snapshot": {"fast_total_seconds": 87.0, "pytest_fast_seconds": 84.0},
            },
        }

        normalized = normalize_history_metadata(legacy_manifest)
        self.assertTrue(normalized["enabled"])
        self.assertEqual(normalized["status"], "pass")
        self.assertEqual(normalized["history_jsonl"], "tmp/history.jsonl")
        self.assertEqual(normalized["runtime_budget_status"], "pass")

    def test_normalize_history_metadata_prefers_canonical_history(self) -> None:
        """Normalization should prioritize canonical history when both exist."""
        from cajas.reports.validation_review_bundle_metadata import normalize_history_metadata

        manifest = {
            "history": {
                "enabled": True,
                "status": "warn",
                "history_jsonl": "canonical.jsonl",
                "summary_json": "canonical.json",
                "summary_md": "canonical.md",
                "snapshot_count": 3,
                "latest_bundle_status": "warn",
                "runtime_budget_status": "pass",
                "regression_count": 1,
            },
            "history_update": {
                "requested": True,
                "status": "ok",
                "history_jsonl": "legacy.jsonl",
            },
        }

        normalized = normalize_history_metadata(manifest)
        self.assertEqual(normalized["history_jsonl"], "canonical.jsonl")
        self.assertEqual(normalized["status"], "warn")
        self.assertEqual(normalized["snapshot_count"], 3)

    def test_validate_history_metadata_compatibility_reports_error_on_disagreement(self) -> None:
        """Compatibility check should detect canonical/legacy disagreement as error."""
        from cajas.reports.validation_review_bundle_metadata import validate_history_metadata_compatibility

        manifest = {
            "history": {"enabled": True, "status": "pass", "history_jsonl": "a.jsonl"},
            "history_update": {
                "requested": False,
                "status": "error",
                "history_jsonl": "b.jsonl",
                "deprecated": False,
                "use": "legacy",
            },
        }

        issues = validate_history_metadata_compatibility(manifest)
        self.assertTrue(any(issue["severity"] == "warning" for issue in issues))
        self.assertTrue(any(issue["severity"] == "error" for issue in issues))
        self.assertTrue(any("deprecated flag" in issue["message"] for issue in issues))
        self.assertTrue(any("use should be 'history'" in issue["message"] for issue in issues))
        self.assertTrue(any("disagrees" in issue["message"] for issue in issues))

    def test_manifest_contains_compatibility_warnings_field(self) -> None:
        """Generated manifest should expose compatibility warnings field when present."""
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
            history_jsonl = tmp_path / "history" / "history.jsonl"

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

            self.assertIn("history_update", manifest)
            self.assertTrue(manifest["history_update"]["deprecated"])

    def test_manifest_compatibility_report_enabled(self) -> None:
        """Compatibility check should write report metadata and index section."""
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
            history_jsonl = tmp_path / "history" / "history.jsonl"

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
                    check_manifest_compatibility=True,
                    warn_only=True,
                )

            compat = manifest["manifest_compatibility"]
            self.assertTrue(compat["enabled"])
            self.assertIn(compat["status"], ("pass", "warn"))
            self.assertIn("error_count", compat)
            self.assertIn("report_json", compat)
            self.assertIn("report_md", compat)
            self.assertTrue(Path(compat["report_json"]).exists())
            self.assertTrue(Path(compat["report_md"]).exists())
            index_text = (out_root / "review_bundle_index.md").read_text(encoding="utf-8")
            self.assertIn("Manifest Compatibility", index_text)
            self.assertIn("Report JSON", index_text)

    def test_manifest_compatibility_not_requested_note(self) -> None:
        """Index should contain clean note when compatibility check is not requested."""
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
                    history_jsonl=None,
                    history_last_n=10,
                    warn_only=True,
                )

            self.assertEqual(manifest["manifest_compatibility"]["status"], "not_requested")
            index_text = (out_root / "review_bundle_index.md").read_text(encoding="utf-8")
            self.assertIn("Manifest compatibility check was not requested for this bundle.", index_text)

    def test_review_bundle_fails_on_manifest_compatibility_fail_without_warn_only(self) -> None:
        """Compatibility fail should raise unless warn_only is enabled."""
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

            fail_report = {
                "status": "fail",
                "manifest_path": "dummy.json",
                "history_source": "history",
                "history_enabled": True,
                "history_status": "pass",
                "error_count": 1,
                "warning_count": 0,
                "info_count": 0,
                "deprecated_alias_present": "yes",
                "issues": [{"severity": "error", "code": "mock_fail", "message": "mock fail"}],
                "reviewer_recommendation": "block_until_manifest_compatibility_fixed",
            }
            with patch("cajas.scripts.build_validation_review_bundle.run_command", self._mock_run_command), patch(
                "cajas.scripts.build_validation_review_bundle.build_compatibility_report",
                return_value=fail_report,
            ):
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
                        update_history=False,
                        history_jsonl=None,
                        history_last_n=10,
                        check_manifest_compatibility=True,
                        manifest_compatibility_out_json=tmp_path / "compat.json",
                        manifest_compatibility_out_md=tmp_path / "compat.md",
                        warn_only=False,
                    )


if __name__ == "__main__":
    unittest.main()
