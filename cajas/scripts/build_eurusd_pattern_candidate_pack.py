#!/usr/bin/env python3
"""Build EURUSD 15m pattern candidate pack artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_pattern_candidate_pack import (
    build_validation_eurusd_pattern_candidate_pack,
    render_validation_eurusd_pattern_candidate_pack_markdown,
)
from cajas.research.eurusd_pattern_candidates import detect_eurusd_pattern_candidates

FORBIDDEN = {"buy", "sell", "long", "short", "order", "position", "target_position"}


def _balanced_samples(candidates: pd.DataFrame, max_samples_per_type: int) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
    trend_types = {"short_trend_down_candidate", "short_trend_up_candidate"}
    chunks = []
    for ctype, part in candidates.groupby("candidate_type", sort=True):
        ordered = part.sort_values("timestamp").reset_index(drop=True)
        if ctype in trend_types and "preferred_review_candidate" in ordered.columns:
            preferred = ordered[ordered["preferred_review_candidate"].fillna(True).astype(bool)].copy()
            if not preferred.empty:
                ordered = preferred
        take = min(int(max_samples_per_type), len(ordered))
        if take <= 0:
            continue
        if take == len(ordered):
            chunks.append(ordered)
            continue
        if take == 1:
            idx = [len(ordered) // 2]
        else:
            span = len(ordered) - 1
            idx = [round(i * span / (take - 1)) for i in range(take)]
        chunks.append(ordered.iloc[idx].copy())
    return pd.concat(chunks, ignore_index=True).sort_values(["candidate_type", "timestamp"]).reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD 15m pattern candidate pack")
    parser.add_argument("--clean-view-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"))
    parser.add_argument("--output-candidates-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_candidates.csv"))
    parser.add_argument("--output-samples-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_samples.csv"))
    parser.add_argument("--output-samples-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-pattern-candidate-pack.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-pattern-candidate-pack.md"))
    parser.add_argument("--max-samples-per-type", type=int, default=50)
    parser.add_argument("--min-confidence", type=float, default=0.6)
    args = parser.parse_args(argv)

    if not args.clean_view_csv.exists():
        payload = {
            "schema_version": 1,
            "status": "blocked",
            "input_clean_view_path": str(args.clean_view_csv),
            "blocking_reasons": ["clean_view_missing"],
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        args.output_md.write_text(render_validation_eurusd_pattern_candidate_pack_markdown(payload), encoding="utf-8")
        print(json.dumps({"status": "blocked", "reason": "clean_view_missing"}))
        return 1

    clean_df = pd.read_csv(args.clean_view_csv)
    candidates = detect_eurusd_pattern_candidates(clean_df, min_confidence=args.min_confidence)

    for col in candidates.columns:
        low = col.lower()
        if any(token == low for token in FORBIDDEN):
            raise ValueError(f"forbidden output column: {col}")

    samples = _balanced_samples(candidates, args.max_samples_per_type)

    args.output_candidates_csv.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(args.output_candidates_csv, index=False)
    samples.to_csv(args.output_samples_csv, index=False)
    with args.output_samples_jsonl.open("w", encoding="utf-8") as f:
        for row in samples.to_dict(orient="records"):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    payload = build_validation_eurusd_pattern_candidate_pack(
        clean_view_csv=args.clean_view_csv,
        candidates_df=candidates,
        samples_df=samples,
        output_candidates_csv=args.output_candidates_csv,
        output_samples_csv=args.output_samples_csv,
        output_samples_jsonl=args.output_samples_jsonl,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_pattern_candidate_pack_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.output_json), "out_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
