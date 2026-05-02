#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.validation_delivery_packet import (  # noqa: E402
    build_validation_delivery_packet,
    render_validation_delivery_packet_md,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Build validation delivery packet json+md.")
    p.add_argument("--fast-timing", default=None)
    p.add_argument("--data-source-audit", default=None)
    p.add_argument("--runtime-audit", default=None)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    p.add_argument("--allow-missing-inputs", action="store_true")
    args = p.parse_args()

    packet = build_validation_delivery_packet(
        fast_timing=args.fast_timing,
        data_source_audit=args.data_source_audit,
        runtime_audit=args.runtime_audit,
        allow_missing_inputs=args.allow_missing_inputs,
    )

    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(packet, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_validation_delivery_packet_md(packet), encoding="utf-8")
    print("Validation delivery packet completed.")
    print(f"output json: {out_json}")
    print(f"output md: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
