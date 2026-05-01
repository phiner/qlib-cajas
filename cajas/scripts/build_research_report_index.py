#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.research_report_index import build_research_report_index


def _render_md(idx: dict) -> str:
    lines = ["# Research Report Index", "", f"- root_dir: `{idx['root_dir']}`", f"- total_files: `{idx['total_files']}`", ""]
    for cat, files in idx["groups"].items():
        lines.append(f"## {cat}")
        if not files:
            lines.append("- none")
        else:
            for f in files:
                lines.append(f"- `{f}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Build a grouped index for research output artifacts.")
    p.add_argument("--root-dir", required=True)
    p.add_argument("--out-dir", required=True)
    args = p.parse_args()
    idx = build_research_report_index(root_dir=args.root_dir)
    out = Path(args.out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "research_report_index.json").write_text(json.dumps(idx, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "research_report_index.md").write_text(_render_md(idx), encoding="utf-8")
    print("Research report index completed.")
    print(f"output dir: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

