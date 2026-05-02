#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.io_runtime_audit import build_io_runtime_audit, render_io_runtime_audit_md
from cajas.reports.runtime_io_summary import safe_json_write


def main() -> int:
    p = argparse.ArgumentParser(description="Audit IO-heavy patterns and tmp filesystem footprint.")
    p.add_argument("--project-root", default="cajas")
    p.add_argument("--tmp-root", default=None)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args()

    report = build_io_runtime_audit(project_root=args.project_root, tmp_root=args.tmp_root)
    safe_json_write(args.out_json, report)
    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(render_io_runtime_audit_md(report=report))

    print(f"output json: {args.out_json}")
    print(f"output md: {args.out_md}")
    print(f"recursive_scan_scripts: {len(report['recursive_scan_scripts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
