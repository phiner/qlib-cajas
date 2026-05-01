#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Run end-to-end Qlib dataset/handler offline ingestion smoke.")
    p.add_argument("--out-root", default="tmp/qlib-dataset-handler-smoke")
    args = p.parse_args()

    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    fixture_dir = out_root / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    fixture_csv = fixture_dir / "sample.csv"
    fixture_csv.write_text(
        "instrument,datetime,open,high,low,close,volume,future_direction_8\n"
        "EURUSD,2025-01-01 00:00:00,1.1,1.2,1.0,1.15,100,up\n"
        "EURUSD,2025-01-01 00:15:00,1.15,1.21,1.12,1.20,110,down\n",
        encoding="utf-8",
    )
    fixture_csv.write_text(
        "instrument,datetime,open,high,low,close,volume,future_direction_8\n"
        "EURUSD,2025-01-01 00:00:00,1.1,1.2,1.0,1.15,100,up\n"
        "EURUSD,2025-01-01 00:15:00,1.15,1.21,1.12,1.20,110,down\n"
        "EURUSD,2025-01-01 00:30:00,1.20,1.24,1.18,1.22,120,up\n"
        "EURUSD,2025-01-01 00:45:00,1.22,1.26,1.19,1.21,130,down\n"
        "EURUSD,2025-01-01 01:00:00,1.21,1.27,1.20,1.26,125,up\n"
        "EURUSD,2025-01-01 01:15:00,1.26,1.28,1.23,1.24,128,down\n",
        encoding="utf-8",
    )

    py = sys.executable
    contract_path = out_root / "dataset_contract" / "qlib_dataset_contract.json"
    handler_dir = out_root / "handler_input"
    validation_path = out_root / "validation" / "qlib_handler_smoke_report.json"

    _run([py, "cajas/scripts/build_qlib_dataset_contract.py", "--input-csv", str(fixture_csv), "--out", str(contract_path), "--dataset-id", "phase76_smoke_dataset", "--label-col", "future_direction_8"])
    _run([py, "cajas/scripts/build_qlib_handler_input.py", "--input-csv", str(fixture_csv), "--out-dir", str(handler_dir), "--label-col", "future_direction_8"])
    _run([py, "cajas/scripts/validate_qlib_handler_input.py", "--handler-dir", str(handler_dir), "--out", str(validation_path)])

    rep = json.loads(validation_path.read_text(encoding="utf-8"))
    if rep.get("status") == "fail":
        print("Qlib dataset/handler smoke failed: blocking issues present.")
        return 2

    print("Qlib dataset/handler smoke completed.")
    print(f"dataset contract: {contract_path}")
    print(f"handler input dir: {handler_dir}")
    print(f"validation report: {validation_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
