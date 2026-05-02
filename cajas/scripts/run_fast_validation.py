#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_FAST_EXPRESSION = "not smoke and not slow and not closure and not full and not integration"
DEFAULT_INTEGRATION_EXPRESSION = "integration and not slow and not smoke"


@dataclass(frozen=True)
class ValidationStep:
    name: str
    command: list[str]
    enabled: bool = True


@dataclass(frozen=True)
class ValidationStepResult:
    name: str
    command: list[str]
    returncode: int
    elapsed_seconds: float
    stdout: str = ""
    stderr: str = ""

    @property
    def status(self) -> str:
        return "pass" if self.returncode == 0 else "fail"

    def to_json_dict(self) -> dict:
        payload = asdict(self)
        payload["status"] = self.status
        payload["seconds"] = round(self.elapsed_seconds, 3)
        return payload


def run_validation_step(
    step: ValidationStep,
    *,
    runner=subprocess.run,
    timer=time.perf_counter,
    echo: bool = True,
) -> ValidationStepResult:
    start = timer()
    if echo:
        print("$ " + " ".join(step.command))
    try:
        completed = runner(step.command, check=True)
        returncode = int(getattr(completed, "returncode", 0))
        stdout = str(getattr(completed, "stdout", "") or "")
        stderr = str(getattr(completed, "stderr", "") or "")
    except subprocess.CalledProcessError as exc:
        returncode = int(exc.returncode)
        stdout = str(getattr(exc, "stdout", "") or "")
        stderr = str(getattr(exc, "stderr", "") or "")
        raise
    finally:
        elapsed = timer() - start
    return ValidationStepResult(
        name=step.name,
        command=step.command,
        returncode=returncode,
        elapsed_seconds=elapsed,
        stdout=stdout,
        stderr=stderr,
    )


def _build_pytest_cmd(py: str, expression: str, durations: int | None, extra_args: str | None) -> list[str]:
    cmd = [py, "-m", "pytest", "cajas/tests", "-m", expression]
    if durations is not None:
        cmd.append(f"--durations={durations}")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    return cmd


def build_validation_plan(args: argparse.Namespace, py: str | None = None) -> list[ValidationStep]:
    py = py or sys.executable
    tier = args.tier
    if args.only_pytest:
        return [ValidationStep("pytest_fast", _build_pytest_cmd(py, args.pytest_expression, args.durations, args.pytest_extra_args))]

    if args.only_hygiene:
        return [
            ValidationStep("path_hygiene", [py, "cajas/scripts/check_path_hygiene.py"]),
            ValidationStep("init_py_find", ["find", "cajas", "-path", "*/init.py", "-print"]),
            ValidationStep("git_init_py_check", ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"]),
        ]

    steps: list[ValidationStep] = []

    if tier == "quick":
        steps.extend(
            [
                ValidationStep("path_hygiene", [py, "cajas/scripts/check_path_hygiene.py"]),
                ValidationStep("init_py_find", ["find", "cajas", "-path", "*/init.py", "-print"]),
                ValidationStep("git_init_py_check", ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"]),
                ValidationStep(
                    "pytest_quick_policy",
                    [
                        py,
                        "-m",
                        "pytest",
                        "cajas/tests/test_validation_marker_policy.py",
                        "cajas/tests/test_validation_runtime_audit.py",
                    ],
                ),
            ]
        )
        return steps

    if tier == "full-pytest":
        if not args.skip_compileall:
            steps.append(ValidationStep("compileall", [py, "-m", "compileall", "cajas"]))
        steps.extend(
            [
                ValidationStep("path_hygiene", [py, "cajas/scripts/check_path_hygiene.py"]),
                ValidationStep("init_py_find", ["find", "cajas", "-path", "*/init.py", "-print"]),
                ValidationStep("git_init_py_check", ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"]),
                ValidationStep("pytest_full", [py, "-m", "pytest", "cajas/tests"]),
            ]
        )
        return steps

    # tier == fast
    if not args.skip_compileall:
        steps.append(ValidationStep("compileall", [py, "-m", "compileall", "cajas"]))
    steps.extend(
        [
            ValidationStep("path_hygiene", [py, "cajas/scripts/check_path_hygiene.py"]),
            ValidationStep("init_py_find", ["find", "cajas", "-path", "*/init.py", "-print"]),
            ValidationStep("git_init_py_check", ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"]),
        ]
    )
    if not args.skip_pytest:
        steps.append(ValidationStep("pytest_fast", _build_pytest_cmd(py, args.pytest_expression, args.durations, args.pytest_extra_args)))
    return steps


def _build_steps(args: argparse.Namespace, py: str) -> list[tuple[str, list[str]]]:
    return [(step.name, step.command) for step in build_validation_plan(args, py)]


def evaluate_budget(results: list[ValidationStepResult], max_seconds: float | None, fail_on_budget: bool) -> tuple[bool, list[str]]:
    total_seconds = sum(result.elapsed_seconds for result in results)
    if max_seconds is None or total_seconds <= max_seconds:
        return False, []
    message = f"runtime budget exceeded ({total_seconds:.2f}s > {max_seconds:.2f}s)"
    if fail_on_budget:
        message += "; failing because --fail-on-budget is set"
    return True, [message]


def build_timing_payload(
    *,
    args: argparse.Namespace,
    results: list[ValidationStepResult],
    total_seconds: float,
    overall_status: str,
    budget_exceeded: bool,
) -> dict:
    return {
        "schema_version": "v1",
        "tier": args.tier,
        "pytest_expression": args.pytest_expression,
        "results": [result.to_json_dict() for result in results],
        "total_seconds": round(total_seconds, 3),
        "overall_status": overall_status,
        "budget": {
            "max_seconds": args.max_seconds,
            "exceeded": budget_exceeded,
            "fail_on_budget": args.fail_on_budget,
        },
    }


def write_timing_json(path: str | Path, payload: dict) -> Path:
    out = Path(path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def _print_timing_table(results: list[ValidationStepResult], total_seconds: float, status: str) -> None:
    print("step                                      status   seconds")
    for item in results:
        print(f"{item.name:<41} {item.status:<7} {item.elapsed_seconds:.2f}")
    print(f"{'total':<41} {status:<7} {total_seconds:.2f}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run fast validation tiers with runtime profiling.")
    p.add_argument("--tier", choices=["quick", "fast", "full-pytest"], default="fast")
    p.add_argument("--skip-compileall", action="store_true")
    p.add_argument("--skip-pytest", action="store_true")
    p.add_argument("--only-pytest", action="store_true")
    p.add_argument("--only-hygiene", action="store_true")
    p.add_argument("--durations", type=int, default=None)
    p.add_argument("--pytest-extra-args", default=None)
    p.add_argument("--pytest-expression", default=DEFAULT_FAST_EXPRESSION)
    p.add_argument("--max-seconds", type=float, default=None)
    p.add_argument("--fail-on-budget", action="store_true")
    p.add_argument("--timing-json", default=None)
    p.add_argument("--include-real-data", action="store_true")
    p.add_argument("--data-root", default="/home/phiner/projects/research/data")
    p.add_argument("--allow-large-data", action="store_true")
    return p.parse_args(argv)


def run_validation(
    args: argparse.Namespace,
    *,
    runner=subprocess.run,
    timer=time.perf_counter,
    echo: bool = True,
) -> tuple[int, dict]:
    if args.only_pytest and args.only_hygiene:
        raise ValueError("--only-pytest and --only-hygiene are mutually exclusive")

    if args.include_real_data:
        print(f"warning: --include-real-data is set for data root {args.data_root}; fast validation does not read real data by default.")
    if args.allow_large_data:
        print("warning: --allow-large-data is acknowledged but not used by default fast validation steps.")

    steps = [step for step in build_validation_plan(args, sys.executable) if step.enabled]
    results: list[ValidationStepResult] = []
    start = timer()
    overall_status = "pass"

    try:
        for step in steps:
            results.append(run_validation_step(step, runner=runner, timer=timer, echo=echo))
    except subprocess.CalledProcessError as exc:
        failed_step = next(step for step in steps if step.name not in {r.name for r in results})
        results.append(
            ValidationStepResult(
                name=failed_step.name,
                command=failed_step.command,
                returncode=int(exc.returncode),
                elapsed_seconds=0.0,
                stdout=str(getattr(exc, "stdout", "") or ""),
                stderr=str(getattr(exc, "stderr", "") or ""),
            )
        )
        overall_status = "fail"
    total_seconds = timer() - start

    budget_exceeded, budget_messages = evaluate_budget(results, args.max_seconds, args.fail_on_budget)
    for message in budget_messages:
        print(f"warning: {message}")

    _print_timing_table(results, total_seconds, overall_status)
    payload = build_timing_payload(
        args=args,
        results=results,
        total_seconds=total_seconds,
        overall_status=overall_status,
        budget_exceeded=budget_exceeded,
    )

    if args.timing_json:
        out = write_timing_json(args.timing_json, payload)
        print(f"timing_json: {out}")

    if overall_status == "fail":
        return 1, payload
    if budget_exceeded and args.fail_on_budget:
        return 2, payload
    return 0, payload


def main(argv: list[str] | None = None, *, runner=subprocess.run, timer=time.perf_counter, echo: bool = True) -> int:
    try:
        args = parse_args(argv)
        code, _payload = run_validation(args, runner=runner, timer=timer, echo=echo)
        return code
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
