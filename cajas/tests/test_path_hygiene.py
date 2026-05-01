from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.quality.path_hygiene import check_path_hygiene


class PathHygieneTests(unittest.TestCase):
    def test_clean_files_pass(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cajas").mkdir()
            (root / "cajas" / "a.py").write_text("print('ok')\n", encoding="utf-8")
            report = check_path_hygiene(root=root, include_globs=("cajas/**/*.py",))
            self.assertTrue(report.passed)

    def test_detects_caixas_typo(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks").mkdir()
            (root / "tasks" / "t.md").write_text(
                "python caixas/scripts/do.py\n", encoding="utf-8"
            )
            report = check_path_hygiene(root=root)
            self.assertFalse(report.passed)
            self.assertTrue(any(i.pattern == "caixas/" for i in report.issues))

    def test_ignored_dirs_skipped(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tmp" / "x").mkdir(parents=True)
            (root / "tmp" / "x" / "bad.md").write_text("python caixas/x.py\n", encoding="utf-8")
            report = check_path_hygiene(root=root)
            self.assertTrue(report.passed)

    def test_json_shape_stable(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "cajas").mkdir()
            (root / "cajas" / "a.py").write_text("print('ok')\n", encoding="utf-8")
            report = check_path_hygiene(root=root, include_globs=("cajas/**/*.py",))
            payload = report.to_dict()
            json.dumps(payload)
            self.assertIn("checked_files", payload)


if __name__ == "__main__":
    unittest.main()
