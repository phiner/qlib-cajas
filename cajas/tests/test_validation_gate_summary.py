from __future__ import annotations

import unittest

from cajas.reports.validation_gate_summary import (
    ValidationGate,
    aggregate_gate_status,
    build_final_status_payload,
    render_final_status_markdown,
)


class ValidationGateSummaryTests(unittest.TestCase):
    def test_aggregate_pass(self) -> None:
        gates = [
            ValidationGate("a", True, "pass", "ok"),
            ValidationGate("b", False, "not_run", "optional"),
        ]
        self.assertEqual(aggregate_gate_status(gates), "pass")

    def test_aggregate_warn(self) -> None:
        gates = [ValidationGate("a", True, "warn", "warn")]
        self.assertEqual(aggregate_gate_status(gates), "warn")

    def test_aggregate_fail(self) -> None:
        gates = [ValidationGate("a", True, "fail", "fail")]
        self.assertEqual(aggregate_gate_status(gates), "fail")

    def test_render_markdown(self) -> None:
        payload = build_final_status_payload(
            gates=[ValidationGate("runtime_budget", True, "pass", "ok", "a.json", "a.md")],
            bundle_name="bundle",
            created_at="2026-05-03T00:00:00+00:00",
            git_branch="x",
            git_commit="y",
        )
        md = render_final_status_markdown(payload)
        self.assertIn("Validation Final Status", md)
        self.assertIn("CI Gate Summary", md)
        self.assertIn("runtime_budget", md)


if __name__ == "__main__":
    unittest.main()
