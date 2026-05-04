from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_pattern_candidate_pack import (
    build_validation_eurusd_pattern_candidate_pack,
    render_validation_eurusd_pattern_candidate_pack_markdown,
)
from cajas.research.eurusd_pattern_candidates import detect_eurusd_pattern_candidates


def _write_clean(path: Path) -> Path:
    rows = []
    base = 1.1
    for i in range(80):
        o = base
        c = o + (0.0002 if i % 2 == 0 else -0.00015)
        h = max(o, c) + 0.0004
        l = min(o, c) - 0.0003
        rows.append(
            {
                "timestamp": f"2025-01-01 {i//4:02d}:{(i%4)*15:02d}:00",
                "open": round(o, 5),
                "high": round(h, 5),
                "low": round(l, 5),
                "close": round(c, 5),
                "source_row_index": i,
            }
        )
        base += 0.00002
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_report_ready_when_candidates_exist(tmp_path: Path) -> None:
    clean = _write_clean(tmp_path / "clean.csv")
    clean_df = pd.read_csv(clean)
    candidates = detect_eurusd_pattern_candidates(clean_df, min_confidence=0.5)
    samples = candidates.groupby("candidate_type", sort=True).head(5).reset_index(drop=True) if not candidates.empty else candidates

    payload = build_validation_eurusd_pattern_candidate_pack(
        clean_view_csv=clean,
        candidates_df=candidates,
        samples_df=samples,
        output_candidates_csv=tmp_path / "candidates.csv",
        output_samples_csv=tmp_path / "samples.csv",
        output_samples_jsonl=tmp_path / "samples.jsonl",
    )
    assert payload["status"] in {"ready", "watch"}
    assert payload["candidate_count"] >= 0


def test_report_blocked_when_clean_view_missing(tmp_path: Path) -> None:
    payload = build_validation_eurusd_pattern_candidate_pack(
        clean_view_csv=tmp_path / "missing.csv",
        candidates_df=pd.DataFrame(),
        samples_df=pd.DataFrame(),
        output_candidates_csv=tmp_path / "candidates.csv",
        output_samples_csv=tmp_path / "samples.csv",
        output_samples_jsonl=tmp_path / "samples.jsonl",
    )
    assert payload["status"] == "blocked"


def test_markdown_policy_line() -> None:
    md = render_validation_eurusd_pattern_candidate_pack_markdown(
        {
            "status": "ready",
            "candidate_count": 3,
            "input_clean_view_path": "tmp/x.csv",
            "candidate_count_by_type": {"compression_candidate": 2},
            "sample_count_by_type": {"compression_candidate": 1},
        }
    ).lower()
    assert "review only" in md
    assert "not trading signals" in md
