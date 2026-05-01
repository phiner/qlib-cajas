from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.artifact_normalizer import normalize_json_artifact


class ArtifactNormalizerTests(unittest.TestCase):
    def test_json_normalizer_preserves_semantics(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.json"
            p.write_text(json.dumps({"created_at_utc": "2026-01-01T00:00:00+00:00", "final_status": "blocked", "metric": 1}), encoding="utf-8")
            rep = normalize_json_artifact(input_path=p)
            self.assertEqual(rep["normalized_payload"]["final_status"], "blocked")


if __name__ == "__main__":
    unittest.main()
