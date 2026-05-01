from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.qlib_readiness_report import build_qlib_readiness_report


class QlibReadinessReportTests(unittest.TestCase):
    def test_report_flags_disabled_execution(self) -> None:
        with TemporaryDirectory() as tmp:
            rep = build_qlib_readiness_report(output_dir=Path(tmp), run_name="r")
            self.assertFalse(rep["qlib_initialized"])
            self.assertFalse(rep["qlib_workflow_executed"])


if __name__ == "__main__":
    unittest.main()
