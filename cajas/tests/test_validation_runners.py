from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.scripts.run_fast_validation import (
    DEFAULT_FAST_EXPRESSION,
    build_validation_plan,
    parse_args,
    run_validation,
)
from cajas.scripts.run_smoke_validation import build_tier_commands


class DeterministicTimer:
    def __init__(self, step: float = 0.25) -> None:
        self.current = 0.0
        self.step = step

    def __call__(self) -> float:
        self.current += self.step
        return self.current


class ValidationRunnersTests(unittest.TestCase):
    def test_fast_validation_uses_exclusion_markers(self) -> None:
        args = parse_args(["--tier", "fast"])
        plan = build_validation_plan(args, py="python")
        pytest_steps = [step for step in plan if step.name == "pytest_fast"]
        self.assertEqual(len(pytest_steps), 1)
        marker_index = max(i for i, value in enumerate(pytest_steps[0].command) if value == "-m")
        self.assertEqual(pytest_steps[0].command[marker_index + 1], DEFAULT_FAST_EXPRESSION)
        for excluded in ["smoke", "slow", "closure", "full", "integration"]:
            self.assertIn(f"not {excluded}", pytest_steps[0].command[marker_index + 1])

    def test_smoke_validation_default_is_micro(self) -> None:
        txt = Path("cajas/scripts/run_smoke_validation.py").read_text(encoding="utf-8")
        self.assertIn('default="micro"', txt)

    def test_micro_tier_does_not_invoke_closure_or_full(self) -> None:
        cmds = build_tier_commands(py="python", out_root=Path("tmp/smoke"), tier="micro")
        joined = "\n".join(" ".join(cmd) for cmd in cmds)
        self.assertNotIn("run_governance_review_closure_smoke.py", joined)
        self.assertNotIn("run_full_research_stack_smoke.py", joined)

    def test_quick_tier_avoids_full_pytest_sweep(self) -> None:
        args = parse_args(["--tier", "quick"])
        plan = build_validation_plan(args, py="python")
        names = [step.name for step in plan]
        self.assertIn("pytest_quick_policy", names)
        pytest_steps = [step for step in plan if step.name.startswith("pytest")]
        self.assertEqual([step.name for step in pytest_steps], ["pytest_quick_policy"])
        self.assertFalse(any(step.command == ["python", "-m", "pytest", "cajas/tests"] for step in pytest_steps))

    def test_only_and_skip_flags_build_expected_plans(self) -> None:
        only_pytest = build_validation_plan(parse_args(["--only-pytest"]), py="python")
        self.assertEqual([step.name for step in only_pytest], ["pytest_fast"])

        only_hygiene = build_validation_plan(parse_args(["--only-hygiene"]), py="python")
        self.assertEqual([step.name for step in only_hygiene], ["path_hygiene", "init_py_find", "git_init_py_check"])

        skip_pytest = build_validation_plan(parse_args(["--tier", "fast", "--skip-pytest"]), py="python")
        self.assertNotIn("pytest_fast", [step.name for step in skip_pytest])

        quick = build_validation_plan(parse_args(["--tier", "quick"]), py="python")
        self.assertIn("pytest_quick_policy", [step.name for step in quick])

    def test_fast_validation_writes_timing_json(self) -> None:
        calls: list[list[str]] = []

        def fake_runner(cmd: list[str], check: bool) -> object:
            calls.append(cmd)
            return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "timing.json"
            code, payload = run_validation(
                parse_args(["--tier", "quick", "--timing-json", str(out)]),
                runner=fake_runner,
                timer=DeterministicTimer(),
                echo=False,
            )
            self.assertEqual(code, 0)
            self.assertEqual(len(calls), 4)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["tier"], "quick")
            self.assertIn("total_seconds", payload)
            self.assertEqual(payload["overall_status"], "pass")
            self.assertEqual(len(payload["results"]), 4)

    def test_fail_on_budget_returns_nonzero(self) -> None:
        def fake_runner(cmd: list[str], check: bool) -> object:
            return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "timing.json"
            code, payload = run_validation(
                parse_args(["--tier", "quick", "--max-seconds", "0", "--fail-on-budget", "--timing-json", str(out)]),
                runner=fake_runner,
                timer=DeterministicTimer(),
                echo=False,
            )
            self.assertEqual(code, 2)
            self.assertTrue(payload["budget"]["exceeded"])

    def test_validation_runner_tests_do_not_call_subprocess_run(self) -> None:
        text = Path(__file__).read_text(encoding="utf-8")
        token = "subprocess" + ".run("
        self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
