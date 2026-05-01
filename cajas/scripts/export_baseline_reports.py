#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.markdown_report_exporter import (
    render_baseline_report_pack_markdown,
    write_markdown_report,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Export baseline JSON reports to markdown summaries.")
    p.add_argument("--report-json", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-name", required=True)
    p.add_argument("--title", default="Baseline Report")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    src = Path(args.report_json).expanduser().resolve()
    payload = json.loads(src.read_text(encoding="utf-8"))

    out_dir = Path(args.output_dir).expanduser().resolve() / args.run_name
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing run directory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)

    markdown = render_baseline_report_pack_markdown(payload)
    md_path = write_markdown_report(
        output_path=out_dir / "baseline_report.md",
        title=args.title,
        sections=[("Summary", markdown)],
    )
    manifest = {
        "source_report_json": str(src),
        "baseline_report_md": md_path,
    }
    manifest_path = out_dir / "export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps({"output_dir": str(out_dir), "manifest": manifest}, ensure_ascii=True, indent=2))
    else:
        print("Report export completed.")
        print(f"output dir: {out_dir}")
        print("notice: no trading/backtest/profit analysis performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
