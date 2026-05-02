#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import time


def _run(cmd: list[str]) -> float:
    start = time.time()
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, check=True)
    return time.time() - start


def main() -> int:
    py = sys.executable
    steps = [
        [py, "-m", "compileall", "cajas"],
        [py, "cajas/scripts/check_path_hygiene.py"],
        ["find", "cajas", "-path", "*/init.py", "-print"],
        ["bash", "-lc", "git ls-files | grep -E '(^|/)init\\.py$' || true"],
        [py, "-m", "pytest", "cajas/tests", "-m", "not slow and not smoke"],
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

