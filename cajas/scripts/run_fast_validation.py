#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import time


def _run(cmd: list[str]) -> float:
    start = time.time()
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, check=True)
    return time.time() - start


def _build_pytest_cmd(py: str, durations: int | None, extra_args: str | None) -> list[str]:
    cmd = [
        py,
        "-m",
        "pytest",
        "cajas/tests",
        "-m",
        "not smoke and not slow and not closure and not full",
    ]
    if durations is not None:
        cmd.append(f"--durations={durations}")
    if extra_args:
        cmd.extend(shlex.split(extra_args))
    return cmd


def main() -> int:
    p = argparse.ArgumentParser(description="Run fast validation only (no smoke/slow/closure/full tiers).")
    p.add_argument("--skip-compileall", action="store_true")
    p.add_argument("--durations", type=int, default=None)
    p.add_argument("--pytest-extra-args", default=None)
    args = p.parse_args()

    py = sys.executable
    steps: list[list[str]] = []
    if not args.skip_compileall:
        steps.append([py, "-m", "compileall", "cajas"])
    steps += [
        [py, "cajas/scripts/check_path_hygiene.py"],
        ["find", "cajas", "-path", "*/init.py", "-print"],
        ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"],
        _build_pytest_cmd(py, args.durations, args.pytest_extra_args),
    ]

    total = 0.0
    for step in steps:
        elapsed = _run(step)
        total += elapsed
        print(f"elapsed: {elapsed:.2f}s")
    print(f"total_runtime: {total:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
