#!/usr/bin/env python3
"""Guarded canonical evidence apply command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_canonical_evidence_apply import (
    build_canonical_evidence_apply_report,
    render_canonical_evidence_apply_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply canonical evidence update with safety guards")
    parser.add_argument("--real-evidence", required=True, type=Path)
    parser.add_argument("--candidate-evidence", required=True, type=Path)
    parser.add_argument("--canonical-evidence-update-plan", required=True, type=Path)
    parser.add_argument("--approval-file", required=True, type=Path)
    parser.add_argument("--backup-out", required=True, type=Path)
    parser.add_argument("--out-evidence", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply-in-place", action="store_true")
    args = parser.parse_args(argv)

    dry_run = args.dry_run or (not args.apply_in_place)

    payload, _ = build_canonical_evidence_apply_report(
        real_evidence=args.real_evidence,
        candidate_evidence=args.candidate_evidence,
        canonical_evidence_update_plan=args.canonical_evidence_update_plan,
        approval_file=args.approval_file,
        backup_out=args.backup_out,
        out_evidence=args.out_evidence,
        dry_run=dry_run,
        apply_in_place=args.apply_in_place,
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_canonical_evidence_apply_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
