"""Tests for review bundle manifest compatibility check CLI and helpers."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.validation_review_bundle_metadata import (
    normalize_history_metadata,
    summarize_compatibility_issues,
    validate_history_metadata_compatibility,
)
from cajas.scripts.check_review_bundle_manifest_compatibility import (
    build_compatibility_report,
    main as compat_main,
    render_compatibility_markdown,
)


class ReviewBundleManifestCompatibilityTests(unittest.TestCase):
    """Validate canonical/legacy compatibility behavior."""

    def test_legacy_only_manifest_emits_warning(self) -> None:
        manifest = {
            "runtime_budget_status": "pass",
            "history_update": {
                "requested": True,
                "status": "ok",
                "history_jsonl": "legacy.jsonl",
                "summary_json": "legacy.json",
                "summary_md": "legacy.md",
                "regression_count": 0,
            },
        }
        normalized = normalize_history_metadata(manifest)
        self.assertEqual(normalized["source"], "history_update")

        issues = validate_history_metadata_compatibility(manifest)
        self.assertTrue(any(issue["severity"] == "warning" for issue in issues))
        summary = summarize_compatibility_issues(issues)
        self.assertEqual(summary["status"], "warn")

    def test_cli_outputs_reports(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            manifest_path = tmp_path / "review_bundle_manifest.json"
            out_json = tmp_path / "compatibility.json"
            out_md = tmp_path / "compatibility.md"
            manifest_path.write_text(
                json.dumps(
                    {
                        "history": {
                            "enabled": False,
                            "status": "not_requested",
                            "note": "History update was not requested for this bundle.",
                        },
                        "history_update": {
                            "deprecated": True,
                            "use": "history",
                            "requested": False,
                            "status": "not_requested",
                        },
                    }
                ),
                encoding="utf-8",
            )

            code = compat_main(
                [
                    "--manifest",
                    str(manifest_path),
                    "--out-json",
                    str(out_json),
                    "--out-md",
                    str(out_md),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(out_json.exists())
            self.assertTrue(out_md.exists())
            report = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn(report["status"], ("pass", "warn"))
            self.assertIn("error_count", report)
            self.assertIn("warning_count", report)
            self.assertIn("issues", report)

    def test_report_builder_and_markdown_renderer(self) -> None:
        manifest = {
            "history": {
                "enabled": True,
                "status": "pass",
                "history_jsonl": "h.jsonl",
                "summary_json": "h.json",
                "summary_md": "h.md",
            },
            "history_update": {"deprecated": True, "use": "history", "requested": True, "status": "ok"},
        }
        report = build_compatibility_report(manifest, "dummy.json")
        self.assertEqual(report["manifest_path"], "dummy.json")
        self.assertIn(report["status"], ("pass", "warn"))
        markdown = render_compatibility_markdown(report)
        self.assertIn("Review Bundle Manifest Compatibility", markdown)

    def test_fail_status_for_canonical_legacy_disagreement(self) -> None:
        manifest = {
            "history": {
                "enabled": True,
                "status": "pass",
                "history_jsonl": "a.jsonl",
                "summary_json": "a.json",
                "summary_md": "a.md",
            },
            "history_update": {
                "deprecated": True,
                "use": "history",
                "requested": False,
                "status": "warn",
                "history_jsonl": "b.jsonl",
                "summary_json": "b.json",
                "summary_md": "b.md",
            },
        }
        report = build_compatibility_report(manifest, "dummy.json")
        self.assertEqual(report["status"], "fail")
        self.assertGreater(report["error_count"], 0)

    def test_cli_nonzero_on_fail_and_fail_on_warn(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fail_manifest = tmp_path / "fail_manifest.json"
            fail_manifest.write_text(
                json.dumps(
                    {
                        "history": {"enabled": True, "status": "pass", "history_jsonl": "a", "summary_json": "b", "summary_md": "c"},
                        "history_update": {"deprecated": True, "use": "legacy", "requested": True, "status": "pass"},
                    }
                ),
                encoding="utf-8",
            )
            out_json = tmp_path / "fail.json"
            out_md = tmp_path / "fail.md"
            fail_code = compat_main(["--manifest", str(fail_manifest), "--out-json", str(out_json), "--out-md", str(out_md)])
            self.assertEqual(fail_code, 1)

            warn_manifest = tmp_path / "warn_manifest.json"
            warn_manifest.write_text(
                json.dumps(
                    {
                        "runtime_budget_status": "pass",
                        "history_update": {
                            "requested": True,
                            "status": "ok",
                            "history_jsonl": "legacy.jsonl",
                            "summary_json": "legacy.json",
                            "summary_md": "legacy.md",
                            "regression_count": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )
            warn_json = tmp_path / "warn.json"
            warn_md = tmp_path / "warn.md"
            warn_code = compat_main(
                [
                    "--manifest",
                    str(warn_manifest),
                    "--out-json",
                    str(warn_json),
                    "--out-md",
                    str(warn_md),
                    "--fail-on-warn",
                ]
            )
            self.assertEqual(warn_code, 1)


if __name__ == "__main__":
    unittest.main()
