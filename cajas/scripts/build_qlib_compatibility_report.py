#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.qlib_adapter_contract import validate_qlib_adapter_contract
from cajas.reports.qlib_compatibility_report import build_qlib_compatibility_report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build Qlib compatibility report from adapter contract.")
    p.add_argument("--adapter-contract", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--strict", action="store_true")
    p.add_argument("--strict-paths", action="store_true")
    args = p.parse_args(argv)

    contract = json.loads(Path(args.adapter_contract).expanduser().read_text(encoding="utf-8"))
    issues = validate_qlib_adapter_contract(contract, strict_paths=args.strict_paths)
    report = build_qlib_compatibility_report(contract=contract, issues=issues, strict=args.strict)

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "qlib_compatibility_report.json").write_text(
        json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "qlib_compatibility_report.md").write_text(
        "# Qlib Compatibility Report\n\n"
        f"- compatibility_decision: `{report['compatibility_decision']}`\n"
        f"- blocking_issues: `{len(report['blocking_issues'])}`\n"
        f"- warnings: `{len(report['non_blocking_warnings'])}`\n",
        encoding="utf-8",
    )
    print("Qlib compatibility report completed.")
    print(f"output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
