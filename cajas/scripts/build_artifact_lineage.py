#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.artifact_lineage import build_artifact_lineage, render_artifact_lineage_md


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build artifact lineage graph reports.")
    p.add_argument("--root", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args(argv)
    rep = build_artifact_lineage(root=args.root)
    out_j = Path(args.out_json).expanduser().resolve()
    out_m = Path(args.out_md).expanduser().resolve()
    out_j.parent.mkdir(parents=True, exist_ok=True)
    out_m.parent.mkdir(parents=True, exist_ok=True)
    out_j.write_text(json.dumps(rep, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_m.write_text(render_artifact_lineage_md(lineage=rep), encoding="utf-8")
    print(f"artifact lineage json: {out_j}")
    print(f"artifact lineage md: {out_m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
