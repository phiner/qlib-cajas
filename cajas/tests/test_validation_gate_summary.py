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
            ValidationGate("a", True, "pass", "ok", "none", "ok"),
            ValidationGate("b", False, "not_run", "not_requested", "none", "optional"),
        ]
        self.assertEqual(aggregate_gate_status(gates, profile="local"), "pass")

    def test_aggregate_warn(self) -> None:
        gates = [ValidationGate("a", True, "warn", "required_warn", "review", "warn")]
        self.assertEqual(aggregate_gate_status(gates, profile="local"), "warn")

    def test_aggregate_fail(self) -> None:
        gates = [ValidationGate("a", True, "fail", "required_fail", "fix", "fail")]
        self.assertEqual(aggregate_gate_status(gates, profile="local"), "fail")

    def test_optional_warn_profile_behavior(self) -> None:
        gates = [
            ValidationGate("required", True, "pass", "ok", "none", "ok"),
            ValidationGate("optional", False, "warn", "optional_warn", "review", "warn"),
        ]
        self.assertEqual(aggregate_gate_status(gates, profile="local"), "pass")
        self.assertEqual(aggregate_gate_status(gates, profile="ci"), "warn")

    def test_render_markdown(self) -> None:
        payload = build_final_status_payload(
            gates=[ValidationGate("runtime_budget", True, "pass", "within_budget", "none", "ok", "a.json", "a.md")],
            bundle_name="bundle",
            created_at="2026-05-03T00:00:00+00:00",
            git_branch="x",
            git_commit="y",
            profile="ci",
        )
        md = render_final_status_markdown(payload)
        self.assertIn("Validation Final Status", md)
        self.assertIn("CI Gate Summary", md)
        self.assertIn("runtime_budget", md)
        self.assertIn("Primary reason", md)
        self.assertIn("Reason", md)

    def test_payload_contract_fields(self) -> None:
        payload = build_final_status_payload(
            gates=[ValidationGate("runtime_budget", True, "warn", "over_budget", "review", "warn", "a.json", "a.md")],
            bundle_name="bundle",
            created_at=None,
            git_branch="x",
            git_commit="y",
            profile="strict",
        )
        self.assertEqual(payload["schema_version"], "v1")
        self.assertIn("run_id", payload)
        self.assertEqual(payload["profile"], "strict")
        self.assertIn("overall_reason", payload)
        self.assertIn("reviewer_next_action", payload)


if __name__ == "__main__":
    unittest.main()
