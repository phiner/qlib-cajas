from __future__ import annotations

import unittest

from cajas.environment.dependency_probe import probe_dependencies


class DependencyProbeTests(unittest.TestCase):
    def test_known_and_fake_modules(self) -> None:
        report = probe_dependencies(names=("json", "definitely_missing_module_xyz"))
        self.assertEqual(len(report.dependencies), 2)
        self.assertTrue(report.dependencies[0].available)
        self.assertFalse(report.dependencies[1].available)

    def test_to_dict_and_missing(self) -> None:
        report = probe_dependencies(names=("json", "definitely_missing_module_xyz"))
        as_dict = report.to_dict()
        self.assertIn("dependencies", as_dict)
        self.assertIn("definitely_missing_module_xyz", report.missing)


if __name__ == "__main__":
    unittest.main()
