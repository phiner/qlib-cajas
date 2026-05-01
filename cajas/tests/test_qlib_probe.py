from __future__ import annotations

import unittest

from cajas.qlib_compat.qlib_probe import probe_qlib_dataset_api


class QlibProbeTests(unittest.TestCase):
    def test_probe_serializes(self) -> None:
        status = probe_qlib_dataset_api()
        payload = status.to_dict()
        self.assertIn("qlib_available", payload)
        self.assertIn("imports", payload)

    def test_probe_no_exception_when_qlib_unavailable(self) -> None:
        status = probe_qlib_dataset_api()
        self.assertIsInstance(status.qlib_available, bool)

    def test_no_init_side_effect_note(self) -> None:
        status = probe_qlib_dataset_api()
        self.assertTrue(any("qlib.init() is not called" in n for n in status.notes))


if __name__ == "__main__":
    unittest.main()
