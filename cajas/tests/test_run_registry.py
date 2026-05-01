from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.registry.run_registry import (
    RunRegistryRecord,
    append_run_registry_record,
    build_run_id,
    read_run_registry,
)


class RunRegistryTests(unittest.TestCase):
    def test_append_and_read_records(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            registry = Path(tmp_dir) / "runs.jsonl"
            rec = RunRegistryRecord(
                run_id=build_run_id("r1", "dry_run"),
                run_name="r1",
                run_type="dry_run",
                phase="phase19",
                status="completed",
                output_dir="tmp/out/r1",
                artifact_files=["a.json"],
                created_by="test",
                training_executed=False,
                model_artifact_created=False,
                notes=["ok"],
            )
            result = append_run_registry_record(registry_path=registry, record=rec)
            self.assertEqual(result.total_records, 1)

            rows = read_run_registry(registry)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["run_name"], "r1")

    def test_jsonl_valid_and_total_count(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            registry = Path(tmp_dir) / "runs.jsonl"
            for idx in range(2):
                rec = RunRegistryRecord(
                    run_id=build_run_id(f"r{idx}", "baseline"),
                    run_name=f"r{idx}",
                    run_type="baseline",
                    phase="phase20",
                    status="completed",
                    output_dir=f"tmp/out/r{idx}",
                    artifact_files=[],
                    created_by="test",
                    training_executed=True,
                    model_artifact_created=True,
                    notes=[],
                )
                append_run_registry_record(registry_path=registry, record=rec)

            lines = registry.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            for line in lines:
                payload = json.loads(line)
                self.assertIn("run_id", payload)

    def test_malformed_record_rejected(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            registry = Path(tmp_dir) / "runs.jsonl"
            with self.assertRaises(ValueError):
                append_run_registry_record(
                    registry_path=registry,
                    record=RunRegistryRecord(
                        run_id="",
                        run_name="x",
                        run_type="baseline",
                        phase="phase20",
                        status="completed",
                        output_dir="tmp/out",
                        artifact_files=[],
                        created_by="test",
                        training_executed=True,
                        model_artifact_created=True,
                        notes=[],
                    ),
                )


if __name__ == "__main__":
    unittest.main()
