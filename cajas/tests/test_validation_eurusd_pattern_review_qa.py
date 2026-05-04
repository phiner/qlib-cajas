import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_pattern_review_qa import build_validation_eurusd_pattern_review_qa


def _mk_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    candidates = pd.DataFrame(
        [
            {
                "timestamp": "2025-01-01T00:00:00+00:00",
                "candidate_type": "compression_candidate",
                "confidence_score": 0.8,
                "reason_codes": "low_short_vs_long_range",
                "review_priority": "high",
                "source_row_index": 1,
            },
            {
                "timestamp": "2025-01-01T00:15:00+00:00",
                "candidate_type": "expansion_candidate",
                "confidence_score": 0.7,
                "reason_codes": "current_range_vs_recent_atr",
                "review_priority": "medium",
                "source_row_index": 2,
            },
        ]
    )
    samples = candidates.copy()
    clean = pd.DataFrame({"timestamp": ["2025-01-01T00:00:00+00:00", "2025-01-01T00:15:00+00:00"]})

    cp = tmp_path / "candidates.csv"
    sp = tmp_path / "samples.csv"
    cl = tmp_path / "clean.csv"
    rp = tmp_path / "pack.json"
    candidates.to_csv(cp, index=False)
    samples.to_csv(sp, index=False)
    clean.to_csv(cl, index=False)
    rp.write_text(json.dumps({"status": "ready"}), encoding="utf-8")
    return cp, sp, rp, cl


def test_qa_ready_on_valid_fixture(tmp_path: Path) -> None:
    cp, sp, rp, cl = _mk_fixture(tmp_path)
    payload = build_validation_eurusd_pattern_review_qa(
        candidates_csv=cp,
        samples_path=sp,
        candidate_pack_report=rp,
        clean_view_csv=cl,
    )
    assert payload["status"] in {"ready", "watch"}


def test_qa_blocked_for_forbidden_columns(tmp_path: Path) -> None:
    cp, sp, rp, cl = _mk_fixture(tmp_path)
    df = pd.read_csv(sp)
    df["signal"] = 1
    df.to_csv(sp, index=False)
    payload = build_validation_eurusd_pattern_review_qa(candidates_csv=cp, samples_path=sp, candidate_pack_report=rp, clean_view_csv=cl)
    assert payload["status"] == "blocked"


def test_qa_blocked_for_invalid_confidence(tmp_path: Path) -> None:
    cp, sp, rp, cl = _mk_fixture(tmp_path)
    df = pd.read_csv(sp)
    df.loc[0, "confidence_score"] = 1.2
    df.to_csv(sp, index=False)
    payload = build_validation_eurusd_pattern_review_qa(candidates_csv=cp, samples_path=sp, candidate_pack_report=rp, clean_view_csv=cl)
    assert payload["status"] == "blocked"


def test_qa_duplicate_detection(tmp_path: Path) -> None:
    cp, sp, rp, cl = _mk_fixture(tmp_path)
    df = pd.read_csv(sp)
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    df.to_csv(sp, index=False)
    payload = build_validation_eurusd_pattern_review_qa(candidates_csv=cp, samples_path=sp, candidate_pack_report=rp, clean_view_csv=cl)
    assert payload["duplicate_sample_count"] >= 1
