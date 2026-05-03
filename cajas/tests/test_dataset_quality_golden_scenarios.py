from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.dataset_quality_research import build_dataset_quality_research_artifacts
from cajas.reports.dataset_quality_schema_contract import (
    compute_drift_summary,
    detect_drift_against_golden,
    extract_schema_shape,
)


class DatasetQualityGoldenScenariosTests(unittest.TestCase):
    """Test golden scenario shape regression."""

    def _load_scenario_manifest(self) -> dict:
        """Load scenario manifest."""
        manifest_path = Path("cajas/data_examples/golden/dataset_quality_scenarios/scenario_manifest.json")
        if not manifest_path.exists():
            self.skipTest("Scenario manifest not found")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def _generate_fixture_content(self, generator_name: str) -> str:
        """Generate fixture content by generator name."""
        from cajas.scripts.build_dataset_quality_golden_scenarios import SCENARIOS

        for scenario_info in SCENARIOS.values():
            if scenario_info["generator"].__name__ == generator_name:
                return scenario_info["generator"]()
        raise ValueError(f"Unknown generator: {generator_name}")

    def test_all_scenarios_have_golden_shapes(self) -> None:
        """Verify all scenarios have golden shapes."""
        manifest = self._load_scenario_manifest()
        scenarios_dir = Path("cajas/data_examples/golden/dataset_quality_scenarios")

        for scenario in manifest["scenarios"]:
            scenario_name = scenario["name"]
            scenario_dir = scenarios_dir / scenario_name
            self.assertTrue(scenario_dir.exists(), f"Scenario directory missing: {scenario_name}")

            for report_type in scenario["expected_reports"]:
                shape_file = scenario_dir / f"{report_type}_shape.json"
                self.assertTrue(shape_file.exists(), f"Shape file missing: {scenario_name}/{report_type}")

    def test_tiny_balanced_no_drift(self) -> None:
        """Test tiny_balanced scenario has no drift."""
        self._test_scenario_no_drift("tiny_balanced", ["Open", "High", "Low", "Close", "Volume"])

    def test_missing_label_values_no_drift(self) -> None:
        """Test missing_label_values scenario has no drift."""
        self._test_scenario_no_drift("missing_label_values", ["Open", "High", "Low", "Close", "Volume"])

    def test_single_class_label_no_drift(self) -> None:
        """Test single_class_label scenario has no drift."""
        self._test_scenario_no_drift("single_class_label", ["Open", "High", "Low", "Close", "Volume"])

    def test_time_gap_no_drift(self) -> None:
        """Test time_gap scenario has no drift."""
        self._test_scenario_no_drift("time_gap", ["Open", "High", "Low", "Close", "Volume"])

    def test_minimal_columns_no_drift(self) -> None:
        """Test minimal_columns scenario has no drift."""
        self._test_scenario_no_drift("minimal_columns", ["Close"])

    def _test_scenario_no_drift(self, scenario_name: str, feature_cols: list[str]) -> None:
        """Test a scenario has no drift against its golden shapes."""
        manifest = self._load_scenario_manifest()
        scenario = next((s for s in manifest["scenarios"] if s["name"] == scenario_name), None)
        if not scenario:
            self.skipTest(f"Scenario not found: {scenario_name}")

        scenarios_dir = Path("cajas/data_examples/golden/dataset_quality_scenarios")
        scenario_dir = scenarios_dir / scenario_name

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "fixture.csv"
            fixture_content = self._generate_fixture_content(scenario["fixture_generator"])
            csv_path.write_text(fixture_content, encoding="utf-8")

            bundle = build_dataset_quality_research_artifacts(
                input_csv=csv_path,
                label_columns=["future_direction_8"],
                feature_columns=feature_cols,
                chunk_size=10,
            )

            drift_items = []
            for report_type in scenario["expected_reports"]:
                golden_path = scenario_dir / f"{report_type}_shape.json"
                if golden_path.exists() and report_type in bundle:
                    golden_shape = json.loads(golden_path.read_text(encoding="utf-8"))
                    current_shape = extract_schema_shape(bundle[report_type], max_depth=4)
                    drift_items.extend(
                        detect_drift_against_golden(current_shape, golden_shape, f"{report_type}_shape.json", set())
                    )

            summary = compute_drift_summary(drift_items, len(scenario["expected_reports"]))
            self.assertEqual(
                summary.breaking_count,
                0,
                f"Breaking drift detected in {scenario_name}: {[d for d in drift_items if d.kind in ('missing_required', 'removed', 'type_change')]}",
            )


if __name__ == "__main__":
    unittest.main()
