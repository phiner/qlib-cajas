#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.final_readiness_summary import render_final_readiness_summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build final readiness markdown summary.")
    p.add_argument("--packet", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args(argv)

    packet = json.loads(Path(args.packet).expanduser().read_text(encoding="utf-8"))
    md = render_final_readiness_summary(packet=packet)
    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print("Final readiness summary completed.")
    print(f"output: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
