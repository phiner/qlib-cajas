#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.data_io.chunked_csv_reader import iter_csv_chunks
from cajas.reports.runtime_io_summary import safe_json_write


def _parse_columns(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [x.strip() for x in raw.split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="Convert CSV to optional columnar cache with fallback CSV shards.")
    p.add_argument("--input", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--chunk-size", type=int, default=100000)
    p.add_argument("--columns", default=None)
    p.add_argument("--row-limit", type=int, default=None)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = _parse_columns(args.columns)

    manifest = {
        "schema_version": "v1",
        "input": str(Path(args.input).expanduser().resolve()),
        "out_dir": out_dir.as_posix(),
        "mode": "csv_shards_fallback",
        "chunks": [],
        "warnings": [],
    }

    try:
        import pandas as pd  # type: ignore

        have_pandas = True
    except Exception:
        have_pandas = False

    if not have_pandas:
        manifest["warnings"].append("pandas unavailable; fallback mode used")

    idx = 0
    for chunk in iter_csv_chunks(args.input, columns=cols, chunk_size=args.chunk_size, row_limit=args.row_limit):
        shard = out_dir / f"shard_{idx:04d}.csv"
        if shard.exists() and not args.force:
            raise FileExistsError(f"refusing to overwrite existing shard: {shard}")
        if hasattr(chunk, "to_csv"):
            chunk.to_csv(shard, index=False)
            rows = len(chunk)
        else:
            # stdlib fallback chunk is list[dict]
            import csv

            rows = len(chunk)
            if rows == 0:
                continue
            with shard.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(chunk[0].keys()))
                writer.writeheader()
                writer.writerows(chunk)

        manifest["chunks"].append({"path": shard.as_posix(), "rows": rows})
        idx += 1

    safe_json_write(out_dir / "columnar_cache_manifest.json", manifest)
    print(f"output dir: {out_dir}")
    print(f"chunks: {len(manifest['chunks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
