from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.qlib_model_run_registry import load_qlib_model_registry, register_qlib_model_run


class QlibModelRunRegistryTests(unittest.TestCase):
    def test_register_and_load(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "registry.jsonl"
            register_qlib_model_run(registry_path=p, record={"run_id": "r1", "metrics": {"macro_f1": 0.1}})
            rows = load_qlib_model_registry(registry_path=p)
            self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
