from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.normalized_artifact_diff import build_normalized_artifact_diff


class NormalizedArtifactDiffTests(unittest.TestCase):
    def test_reports_json_path_changes(self) -> None:
        with TemporaryDirectory() as tmp:
            l = Path(tmp) / "l.json"
            r = Path(tmp) / "r.json"
            l.write_text(json.dumps({"status": "ok", "items": [1, 2]}), encoding="utf-8")
            r.write_text(json.dumps({"status": "blocked", "items": [2, 1]}), encoding="utf-8")
            rep = build_normalized_artifact_diff(left_path=l, right_path=r)
            paths = {c["path"] for c in rep["changes"]}
            self.assertIn("$.status", paths)


if __name__ == "__main__":
    unittest.main()

