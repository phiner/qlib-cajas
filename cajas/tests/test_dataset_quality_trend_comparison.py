from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.compare_dataset_quality_trends import main as compare_trends_main


class DatasetQualityTrendComparisonTests(unittest.TestCase):
    def test_no_changes_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = {
                "generated_at": "2025-01-01T00:00:00Z",
                "quality_score": 85.0,
                "quality_grade": "A",
                "status": "pass",
                "contract_status": "pass",
                "error_count": 0,
                "warning_count": 0,
                "semantic_error_count": 0,
                "semantic_warning_count": 0,
                "drift_breaking_count": 0,
                "drift_additive_count": 0,
                "files_checked": 3,
                "row_count": 100,
                "column_count": 5,
            }
            current = root / "current.json"
            previous = root / "previous.json"
            current.write_text(json.dumps(snapshot), encoding="utf-8")
            previous.write_text(json.dumps(snapshot), encoding="utf-8")

            out_json = root / "compare.json"
            out_md = root / "compare.md"
            ret = compare_trends_main(
                ["--current", str(current), "--previous", str(previous), "--out-json", str(out_json), "--out-md", str(out_md)]
            )
            self.assertEqual(ret, 0)
            result = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(result["regression_count"], 0)
            self.assertEqual(len(result["changes"]), 0)

    def test_quality_score_delta_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous_snapshot = {
                "generated_at": "2025-01-01T00:00:00Z",
                "quality_score": 85.0,
                "quality_grade": "A",
                "status": "pass",
                "contract_status": "pass",
                "error_count": 0,
                "warning_count": 0,
                "semantic_error_count": 0,
                "semantic_warning_count": 0,
                "drift_breaking_count": 0,
                "drift_additive_count": 0,
                "files_checked": 3,
                "row_count": 100,
                "column_count": 5,
            }
            current_snapshot = previous_snapshot.copy()
            current_snapshot["quality_score"] = 90.0
            current_snapshot["generated_at"] = "2025-01-02T00:00:00Z"

            current = root / "current.json"
            previous = root / "previous.json"
            current.write_text(json.dumps(current_snapshot), encoding="utf-8")
            previous.write_text(json.dumps(previous_snapshot), encoding="utf-8")

            out_json = root / "compare.json"
            out_md = root / "compare.md"
            ret = compare_trends_main(
                ["--current", str(current), "--previous", str(previous), "--out-json", str(out_json), "--out-md", str(out_md)]
            )
            self.assertEqual(ret, 0)
            result = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn("quality_score", result["changes"])
            self.assertEqual(result["changes"]["quality_score"]["delta"], 5.0)

    def test_regression_detected_quality_drop(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous_snapshot = {
                "generated_at": "2025-01-01T00:00:00Z",
                "quality_score": 85.0,
                "quality_grade": "A",
                "status": "pass",
                "contract_status": "pass",
                "error_count": 0,
                "warning_count": 0,
                "semantic_error_count": 0,
                "semantic_warning_count": 0,
                "drift_breaking_count": 0,
                "drift_additive_count": 0,
                "files_checked": 3,
                "row_count": 100,
                "column_count": 5,
            }
            current_snapshot = previous_snapshot.copy()
            current_snapshot["quality_score"] = 70.0  # Drop by 15
            current_snapshot["generated_at"] = "2025-01-02T00:00:00Z"

            current = root / "current.json"
            previous = root / "previous.json"
            current.write_text(json.dumps(current_snapshot), encoding="utf-8")
            previous.write_text(json.dumps(previous_snapshot), encoding="utf-8")

            out_json = root / "compare.json"
            out_md = root / "compare.md"
            ret = compare_trends_main(
                ["--current", str(current), "--previous", str(previous), "--out-json", str(out_json), "--out-md", str(out_md)]
            )
            self.assertEqual(ret, 0)
            result = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertGreater(result["regression_count"], 0)
            self.assertTrue(any("quality_score dropped" in r for r in result["regressions"]))

    def test_fail_on_regression_exits_nonzero(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous_snapshot = {
                "generated_at": "2025-01-01T00:00:00Z",
                "quality_score": 85.0,
                "quality_grade": "A",
                "status": "pass",
                "contract_status": "pass",
                "error_count": 0,
                "warning_count": 0,
                "semantic_error_count": 0,
                "semantic_warning_count": 0,
                "drift_breaking_count": 0,
                "drift_additive_count": 0,
                "files_checked": 3,
                "row_count": 100,
                "column_count": 5,
            }
            current_snapshot = previous_snapshot.copy()
            current_snapshot["semantic_error_count"] = 2
            current_snapshot["generated_at"] = "2025-01-02T00:00:00Z"

            current = root / "current.json"
            previous = root / "previous.json"
            current.write_text(json.dumps(current_snapshot), encoding="utf-8")
            previous.write_text(json.dumps(previous_snapshot), encoding="utf-8")

            out_json = root / "compare.json"
            out_md = root / "compare.md"
            ret = compare_trends_main(
                [
                    "--current",
                    str(current),
                    "--previous",
                    str(previous),
                    "--out-json",
                    str(out_json),
                    "--out-md",
                    str(out_md),
                    "--fail-on-regression",
                ]
            )
            self.assertNotEqual(ret, 0)

    def test_contract_status_regression_detected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous_snapshot = {
                "generated_at": "2025-01-01T00:00:00Z",
                "quality_score": 85.0,
                "quality_grade": "A",
                "status": "pass",
                "contract_status": "pass",
                "error_count": 0,
                "warning_count": 0,
                "semantic_error_count": 0,
                "semantic_warning_count": 0,
                "drift_breaking_count": 0,
                "drift_additive_count": 0,
                "files_checked": 3,
                "row_count": 100,
                "column_count": 5,
            }
            current_snapshot = previous_snapshot.copy()
            current_snapshot["contract_status"] = "fail"
            current_snapshot["generated_at"] = "2025-01-02T00:00:00Z"

            current = root / "current.json"
            previous = root / "previous.json"
            current.write_text(json.dumps(current_snapshot), encoding="utf-8")
            previous.write_text(json.dumps(previous_snapshot), encoding="utf-8")

            out_json = root / "compare.json"
            out_md = root / "compare.md"
            ret = compare_trends_main(
                ["--current", str(current), "--previous", str(previous), "--out-json", str(out_json), "--out-md", str(out_md)]
            )
            self.assertEqual(ret, 0)
            result = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertGreater(result["regression_count"], 0)
            self.assertTrue(any("contract_status changed from pass to fail" in r for r in result["regressions"]))


if __name__ == "__main__":
    unittest.main()
