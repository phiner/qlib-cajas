#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_FAST_EXPRESSION = "not smoke and not slow and not closure and not full and not integration"
DEFAULT_INTEGRATION_EXPRESSION = "integration and not slow and not smoke"


def _run_step(name: str, cmd: list[str]) -> dict:
    start = time.time()
    print("$ " + " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
        status = "pass"
    except subprocess.CalledProcessError:
        status = "fail"
        raise
    finally:
        elapsed = time.time() - start
    return {"step": name, "status": status, "seconds": round(elapsed, 3), "command": cmd}


def _build_pytest_cmd(py: str, expression: str, durations: int | None, extra_args: str | None) -> list[str]:
    cmd = [py, "-m", "pytest", "cajas/tests", "-m", expression]
    if durations is not None:
        cmd.append(f"--durations={durations}")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    return cmd


def _build_steps(args: argparse.Namespace, py: str) -> list[tuple[str, list[str]]]:
    tier = args.tier
    if args.only_pytest:
        return [("pytest_fast", _build_pytest_cmd(py, args.pytest_expression, args.durations, args.pytest_extra_args))]

    if args.only_hygiene:
        return [
            ("path_hygiene", [py, "cajas/scripts/check_path_hygiene.py"]),
            ("init_py_find", ["find", "cajas", "-path", "*/init.py", "-print"]),
            ("git_init_py_check", ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"]),
        ]

    steps: list[tuple[str, list[str]]] = []

    if tier == "quick":
        steps.extend(
            [
                ("path_hygiene", [py, "cajas/scripts/check_path_hygiene.py"]),
                ("init_py_find", ["find", "cajas", "-path", "*/init.py", "-print"]),
                ("git_init_py_check", ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"]),
                (
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
            steps.append(("compileall", [py, "-m", "compileall", "cajas"]))
        steps.extend(
            [
                ("path_hygiene", [py, "cajas/scripts/check_path_hygiene.py"]),
                ("init_py_find", ["find", "cajas", "-path", "*/init.py", "-print"]),
                ("git_init_py_check", ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"]),
                ("pytest_full", [py, "-m", "pytest", "cajas/tests"]),
            ]
        )
        return steps

    # tier == fast
    if not args.skip_compileall:
        steps.append(("compileall", [py, "-m", "compileall", "cajas"]))
    steps.extend(
        [
            ("path_hygiene", [py, "cajas/scripts/check_path_hygiene.py"]),
            ("init_py_find", ["find", "cajas", "-path", "*/init.py", "-print"]),
            ("git_init_py_check", ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"]),
        ]
    )
    if not args.skip_pytest:
        steps.append(("pytest_fast", _build_pytest_cmd(py, args.pytest_expression, args.durations, args.pytest_extra_args)))
    return steps


def _print_timing_table(results: list[dict], total_seconds: float, status: str) -> None:
    print("step                                      status   seconds")
    for item in results:
        print(f"{item['step']:<41} {item['status']:<7} {item['seconds']:.2f}")
    print(f"{'total':<41} {status:<7} {total_seconds:.2f}")


def main() -> int:
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
    args = p.parse_args()

    if args.only_pytest and args.only_hygiene:
        raise SystemExit("--only-pytest and --only-hygiene are mutually exclusive")
    if args.include_real_data:
        print(f"warning: --include-real-data is set for data root {args.data_root}; fast validation does not read real data by default.")
    if args.allow_large_data:
        print("warning: --allow-large-data is acknowledged but not used by default fast validation steps.")

    py = sys.executable
    steps = _build_steps(args, py)
    results: list[dict] = []
    start = time.time()
    overall_status = "pass"

    try:
        for name, cmd in steps:
            results.append(_run_step(name, cmd))
    except subprocess.CalledProcessError:
        overall_status = "fail"
    total_seconds = round(time.time() - start, 3)

    budget_exceeded = False
    if args.max_seconds is not None and total_seconds > args.max_seconds:
        budget_exceeded = True
        print(f"warning: runtime budget exceeded ({total_seconds:.2f}s > {args.max_seconds:.2f}s)")

    _print_timing_table(results, total_seconds, overall_status)

    payload = {
        "schema_version": "v1",
        "tier": args.tier,
        "pytest_expression": args.pytest_expression,
        "results": results,
        "total_seconds": total_seconds,
        "overall_status": overall_status,
        "budget": {
            "max_seconds": args.max_seconds,
            "exceeded": budget_exceeded,
            "fail_on_budget": args.fail_on_budget,
        },
    }

    if args.timing_json:
        out = Path(args.timing_json).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"timing_json: {out}")

    if overall_status == "fail":
        return 1
    if budget_exceeded and args.fail_on_budget:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
