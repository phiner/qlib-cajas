from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.qlib_experiment_manifest import (
    build_qlib_experiment_manifest,
    generate_manifest_markdown,
    manifest_to_dict,
    validate_qlib_experiment_manifest,
)
from cajas.scripts.build_qlib_experiment_manifest import main as build_manifest_main


class QlibExperimentManifestTests(unittest.TestCase):
    def test_build_manifest_produces_required_fields(self) -> None:
        """Test manifest builder produces required fields."""
        manifest = build_qlib_experiment_manifest(
            experiment_name="test_experiment",
            created_at="2025-01-01T00:00:00Z",
        )
        self.assertEqual(manifest.manifest_version, "v1")
        self.assertEqual(manifest.experiment_name, "test_experiment")
        self.assertEqual(manifest.created_at, "2025-01-01T00:00:00Z")
        self.assertIsNotNone(manifest.python_version)
        self.assertIsNotNone(manifest.platform_info)

    def test_manifest_to_dict_includes_all_fields(self) -> None:
        """Test manifest to dict includes all fields."""
        manifest = build_qlib_experiment_manifest(
            experiment_name="test_experiment",
            created_at="2025-01-01T00:00:00Z",
        )
        manifest_dict = manifest_to_dict(manifest)
        required_keys = [
            "manifest_version",
            "created_at",
            "experiment_name",
            "python_version",
            "platform_info",
        ]
        for key in required_keys:
            self.assertIn(key, manifest_dict)

    def test_validate_manifest_fails_on_missing_experiment_name(self) -> None:
        """Test validation fails on missing experiment name."""
        manifest = build_qlib_experiment_manifest(
            experiment_name="",
            created_at="2025-01-01T00:00:00Z",
        )
        errors = validate_qlib_experiment_manifest(manifest)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("experiment_name" in e for e in errors))

    def test_validate_manifest_fails_on_nonexistent_path(self) -> None:
        """Test validation fails on nonexistent path."""
        manifest = build_qlib_experiment_manifest(
            experiment_name="test_experiment",
            dataset_path="/nonexistent/path.csv",
            created_at="2025-01-01T00:00:00Z",
        )
        errors = validate_qlib_experiment_manifest(manifest)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("does not exist" in e for e in errors))

    def test_validate_manifest_passes_with_valid_paths(self) -> None:
        """Test validation passes with valid paths."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dataset = tmp_path / "dataset.csv"
            dataset.write_text("col1,col2\n1,2\n", encoding="utf-8")

            manifest = build_qlib_experiment_manifest(
                experiment_name="test_experiment",
                dataset_path=str(dataset),
                created_at="2025-01-01T00:00:00Z",
            )
            errors = validate_qlib_experiment_manifest(manifest)
            self.assertEqual(len(errors), 0)

    def test_markdown_includes_key_sections(self) -> None:
        """Test Markdown report includes key sections."""
        manifest = build_qlib_experiment_manifest(
            experiment_name="test_experiment",
            created_at="2025-01-01T00:00:00Z",
        )
        manifest_dict = manifest_to_dict(manifest)
        markdown = generate_manifest_markdown(manifest, manifest_dict)

        self.assertIn("Qlib Experiment Reproducibility Manifest", markdown)
        self.assertIn("offline Qlib research reproducibility only", markdown)
        self.assertIn("not a trading execution artifact", markdown)
        self.assertIn("Reproducibility Status", markdown)
        self.assertIn("Source Information", markdown)
        self.assertIn("Referenced Artifacts", markdown)
        self.assertIn("Reviewer Notes", markdown)

    def test_cli_exits_nonzero_on_missing_required_path(self) -> None:
        """Test CLI exits non-zero on missing required path."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out_json = tmp_path / "manifest.json"
            out_md = tmp_path / "manifest.md"

            ret = build_manifest_main([
                "--experiment-name", "test",
                "--dataset-path", "/nonexistent/path.csv",
                "--out-json", str(out_json),
                "--out-md", str(out_md),
            ])
            self.assertNotEqual(ret, 0)

    def test_cli_succeeds_with_allow_missing_optional(self) -> None:
        """Test CLI succeeds with allow-missing-optional flag."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out_json = tmp_path / "manifest.json"
            out_md = tmp_path / "manifest.md"

            ret = build_manifest_main([
                "--experiment-name", "test",
                "--dataset-path", "/nonexistent/path.csv",
                "--out-json", str(out_json),
                "--out-md", str(out_md),
                "--allow-missing-optional",
            ])
            self.assertEqual(ret, 0)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())

    def test_cli_writes_valid_json_and_markdown(self) -> None:
        """Test CLI writes valid JSON and Markdown."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dataset = tmp_path / "dataset.csv"
            dataset.write_text("col1,col2\n1,2\n", encoding="utf-8")

            out_json = tmp_path / "manifest.json"
            out_md = tmp_path / "manifest.md"

            ret = build_manifest_main([
                "--experiment-name", "test_experiment",
                "--dataset-path", str(dataset),
                "--out-json", str(out_json),
                "--out-md", str(out_md),
            ])
            self.assertEqual(ret, 0)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())

            # Verify JSON is parseable
            manifest_data = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(manifest_data["experiment_name"], "test_experiment")

            # Verify Markdown contains key content
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("test_experiment", markdown)


if __name__ == "__main__":
    unittest.main()
