#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.registry.registry_cleanup import classify_run_registry_records, write_filtered_registry_copy


def main() -> int:
    p = argparse.ArgumentParser(description="Classify run registry records and optionally write filtered copy.")
    p.add_argument("--registry", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--write-artifacts", action="store_true")
    p.add_argument("--write-filtered-copy", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    rep = classify_run_registry_records(registry_path=args.registry)
    payload = rep.to_dict()
    filtered = None

    if args.write_artifacts:
        out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
        if out_dir.exists():
            raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
        out_dir.mkdir(parents=True, exist_ok=False)
        (out_dir / "registry_cleanup_report.json").write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        pd.DataFrame([c for c in payload["classifications"]]).to_csv(out_dir / "registry_record_classifications.csv", index=False)
        if args.write_filtered_copy:
            filtered = write_filtered_registry_copy(
                registry_path=args.registry,
                output_path=out_dir / "runs_filtered.jsonl",
                exclude_temp_test=True,
            )

    out = {"report": payload, "filtered_copy": filtered}
    if args.json:
        print(json.dumps(out, ensure_ascii=True, indent=2))
    else:
        print("Registry cleanup classification completed.")
        print(f"total records: {payload['total_records']}")
        print(f"active: {payload['active_records']}")
        print(f"temp test: {payload['temp_test_records']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
