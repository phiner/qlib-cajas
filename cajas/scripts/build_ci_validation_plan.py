#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.ci_validation_plan import build_ci_validation_plan


def main() -> int:
    p = argparse.ArgumentParser(description="Build CI validation plan artifacts.")
    p.add_argument("--out-dir", required=True)
    args = p.parse_args()

    out = Path(args.out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    plan = build_ci_validation_plan()
    (out / "ci_validation_plan.json").write_text(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_lines = ["# CI Validation Plan", ""]
    for tier in plan["tiers"]:
        md_lines.append(f"## {tier['tier']}")
        md_lines.append(f"- intent: {tier['intent']}")
        for cmd in tier["commands"]:
            md_lines.append(f"- `{cmd}`")
        md_lines.append("")
    (out / "ci_validation_plan.md").write_text("\n".join(md_lines), encoding="utf-8")
    print("CI validation plan completed.")
    print(f"output dir: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
