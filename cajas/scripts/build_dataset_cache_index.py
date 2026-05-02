#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.data_io.dataset_cache_index import build_dataset_cache_index, load_manifest
from cajas.reports.runtime_io_summary import safe_json_write


def main() -> int:
    p = argparse.ArgumentParser(description="Build dataset cache index from dataset manifest.")
    p.add_argument("--manifest", required=True)
    p.add_argument("--cache-root", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    manifest = load_manifest(args.manifest)
    report = build_dataset_cache_index(manifest=manifest, cache_root=args.cache_root)
    safe_json_write(args.out, report)
    print(f"output: {args.out}")
    print(f"entries: {len(report['entries'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
