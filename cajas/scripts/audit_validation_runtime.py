#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.validation_runtime_audit import build_validation_runtime_audit, render_validation_runtime_audit_md


def _run_duration_probe(*, tests_root: str, expression: str, durations: int) -> str:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        tests_root,
        "-m",
        expression,
        f"--durations={durations}",
        "-q",
    ]
    print("$ " + " ".join(cmd))
    out = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out.stdout


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Audit validation runtime architecture.")
    p.add_argument("--tests-root", default="cajas/tests")
    p.add_argument("--fast-expression", default="not smoke and not slow and not closure and not full and not integration")
    p.add_argument("--timing-json", default=None)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    p.add_argument("--run-durations", action="store_true")
    p.add_argument("--durations", type=int, default=30)
    args = p.parse_args(argv)

    report = build_validation_runtime_audit(
        tests_root=args.tests_root,
        fast_expression=args.fast_expression,
        timing_json=args.timing_json,
    )
    if args.run_durations:
        try:
            report["duration_probe"] = _run_duration_probe(
                tests_root=args.tests_root,
                expression=args.fast_expression,
                durations=args.durations,
            )
        except subprocess.CalledProcessError as exc:
            report["duration_probe_error"] = exc.stdout or str(exc)

    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_validation_runtime_audit_md(report=report), encoding="utf-8")

    print(f"output json: {out_json}")
    print(f"output md: {out_md}")
    print(f"pytest_collection_count: {report['pytest_collection_count']}")
    print(f"fast_subset_test_count: {report['fast_subset_test_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
