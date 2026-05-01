from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.markdown_report_exporter import (
    render_baseline_report_pack_markdown,
    write_markdown_report,
)


class MarkdownReportExporterTests(unittest.TestCase):
    def test_write_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.md"
            out = write_markdown_report(output_path=path, title="T", sections=[("S", "Body")])
            self.assertTrue(Path(out).exists())
            text = path.read_text(encoding="utf-8")
            self.assertIn("# T", text)

    def test_render_has_no_raw_rows(self) -> None:
        text = render_baseline_report_pack_markdown(
            {
                "run_name": "r",
                "model_family": "LightGBM",
                "target_label": "future_direction_8",
                "valid_metrics": {"accuracy": 0.5},
                "test_metrics": {"accuracy": 0.4},
            }
        )
        self.assertNotIn("datetime", text)


if __name__ == "__main__":
    unittest.main()
