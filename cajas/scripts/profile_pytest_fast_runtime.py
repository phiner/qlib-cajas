#!/usr/bin/env python3
"""Profile pytest fast runtime and emit JSON/Markdown report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from cajas.reports.validation_pytest_runtime_profile import (
    build_validation_pytest_runtime_profile_report,
    render_validation_pytest_runtime_profile_markdown,
)


DEFAULT_FAST_EXPRESSION = "not smoke and not slow and not closure and not full and not integration"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile pytest fast runtime")
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--top-n", type=int, default=25)
    parser.add_argument("--durations", type=int, default=25)
    parser.add_argument("--pytest-expression", default=DEFAULT_FAST_EXPRESSION)
    parser.add_argument("--pytest-extra-args", default=None)
    args = parser.parse_args(argv)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "cajas/tests",
        "-m",
        args.pytest_expression,
        f"--durations={args.durations}",
        "--durations-min=0.1",
        "-q",
    ]
    if args.pytest_extra_args:
        cmd.extend(args.pytest_extra_args.split())

    start = time.perf_counter()
    completed = subprocess.run(cmd, capture_output=True, text=True)
    total = round(time.perf_counter() - start, 3)
    output = "\n".join([completed.stdout or "", completed.stderr or ""])

    payload = build_validation_pytest_runtime_profile_report(
        pytest_output=output,
        total_seconds=total,
        top_n=args.top_n,
    )
    if completed.returncode != 0:
        payload["status"] = "fail"
    payload["pytest_returncode"] = int(completed.returncode)
    payload["command"] = cmd

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_validation_pytest_runtime_profile_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0 if completed.returncode == 0 else completed.returncode


if __name__ == "__main__":
    sys.exit(main())
