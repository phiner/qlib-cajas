from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.validation_gate_summary import (
    DEFAULT_CI_PROFILES,
    ValidationGate,
    aggregate_gate_status,
    build_final_status_payload,
    load_ci_profile_policy,
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
        self.assertIn("overall_reason_code", payload)
        self.assertIn("overall_reason", payload)
        self.assertIn("reviewer_next_action", payload)

    def test_profile_config_loading_fallback_defaults(self) -> None:
        profile_cfg, policy = load_ci_profile_policy("ci", None)
        self.assertEqual(profile_cfg["optional_warn_affects_status"], DEFAULT_CI_PROFILES["ci"]["optional_warn_affects_status"])
        self.assertEqual(policy["source"], "built-in defaults")

    def test_profile_config_loading_from_file(self) -> None:
        with TemporaryDirectory() as tmp:
            profile_path = Path(tmp) / "profiles.json"
            profile_path.write_text(
                '{"profiles":{"local":{"optional_not_run_affects_status":false,"optional_warn_affects_status":false,"required_warn_affects_status":true}}}',
                encoding="utf-8",
            )
            profile_cfg, policy = load_ci_profile_policy("local", profile_path)
            self.assertFalse(profile_cfg["optional_warn_affects_status"])
            self.assertEqual(policy["source"], str(profile_path))

    def test_strict_profile_escalates_optional_not_run(self) -> None:
        gates = [
            ValidationGate("required", True, "pass", "ok", "none", "ok"),
            ValidationGate("optional_nr", False, "not_run", "not_requested", "none", "optional missing"),
        ]
        payload = build_final_status_payload(
            gates=gates,
            bundle_name="bundle",
            created_at="2026-05-03T00:00:00+00:00",
            git_branch="x",
            git_commit="y",
            profile="strict",
        )
        self.assertEqual(payload["overall_status"], "warn")
        optional_gate = [g for g in payload["gates"] if g["name"] == "optional_nr"][0]
        self.assertTrue(optional_gate["escalated"])
        self.assertIn("optional_not_run_escalated_under_strict", optional_gate["profile_effect"])


if __name__ == "__main__":
    unittest.main()
