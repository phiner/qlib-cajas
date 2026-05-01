from __future__ import annotations

import unittest

from cajas.reports.qlib_adapter_contract import validate_qlib_adapter_contract


class QlibAdapterContractTests(unittest.TestCase):
    def test_missing_required_field_yields_issue(self) -> None:
        issues = validate_qlib_adapter_contract({})
        self.assertTrue(any(i.code == "missing_required_field" for i in issues))


if __name__ == "__main__":
    unittest.main()
