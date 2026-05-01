from __future__ import annotations

import unittest

from cajas.reports.reproducibility_check import build_reproducibility_report


class ReproducibilityCheckTests(unittest.TestCase):
    def test_matching_manifests(self) -> None:
        m = {"root": "a", "artifact_inventory": [{"relative_path": "a.json", "sha256": "x"}]}
        rep = build_reproducibility_report(left_manifest=m, right_manifest=m)
        self.assertEqual(rep["final_status"], "reproducible")

    def test_checksum_mismatch(self) -> None:
        l = {"root": "a", "artifact_inventory": [{"relative_path": "a.json", "sha256": "x"}]}
        r = {"root": "b", "artifact_inventory": [{"relative_path": "a.json", "sha256": "y"}]}
        rep = build_reproducibility_report(left_manifest=l, right_manifest=r)
        self.assertEqual(rep["final_status"], "not_reproducible")


if __name__ == "__main__":
    unittest.main()
