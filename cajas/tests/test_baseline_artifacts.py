from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.baseline.baseline_artifacts import write_baseline_reports


class BaselineArtifactsTests(unittest.TestCase):
    def test_writes_reports_and_rejects_overwrite(self) -> None:
        with TemporaryDirectory() as tmp:
            out = write_baseline_reports(
                output_dir=tmp,
                run_name="r1",
                reports={"one": {"a": 1}, "two": {"b": 2}},
            )
            self.assertTrue(Path(out["one"]).exists())
            self.assertTrue(Path(out["two"]).exists())
            with self.assertRaises(FileExistsError):
                write_baseline_reports(
                    output_dir=tmp,
                    run_name="r1",
                    reports={"x": {"y": 1}},
                )


if __name__ == "__main__":
    unittest.main()
