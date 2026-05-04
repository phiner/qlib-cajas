import pandas as pd

from cajas.research.eurusd_pattern_candidates import (
    detect_eurusd_pattern_candidates,
    detect_trend_segments_from_mask,
)


def _trend_fixture() -> pd.DataFrame:
    rows = []
    price = 1.2000
    ts = pd.Timestamp("2025-01-01T00:00:00Z")
    for i in range(40):
        if 0 <= i <= 9:
            delta = -0.0006
        elif 10 <= i <= 12:
            delta = 0.0002
        elif 13 <= i <= 20:
            delta = -0.0005
        elif 21 <= i <= 30:
            delta = 0.00055
        else:
            delta = -0.00025
        o = price
        c = price + delta
        h = max(o, c) + 0.0002
        l = min(o, c) - 0.0002
        rows.append(
            {
                "timestamp": (ts + pd.Timedelta(minutes=15 * i)).isoformat(),
                "open": round(o, 6),
                "high": round(h, 6),
                "low": round(l, 6),
                "close": round(c, 6),
                "source_row_index": i,
            }
        )
        price = c
    return pd.DataFrame(rows)


def test_segment_detection_two_runs() -> None:
    mask = pd.Series([True] * 10 + [False] * 3 + [True] * 8)
    segments = detect_trend_segments_from_mask(mask)
    assert segments == [(0, 9), (13, 20)]


def test_representative_anchor_is_mid_not_last() -> None:
    out = detect_eurusd_pattern_candidates(_trend_fixture(), min_confidence=0.5)
    downs = out[out["candidate_type"] == "short_trend_down_candidate"].copy()
    assert not downs.empty
    assert (downs["segment_position_fraction"] <= 0.75).all()
    assert (downs["segment_position_fraction"] >= 0.3).any()


def test_duplicate_suppression_and_metadata() -> None:
    out = detect_eurusd_pattern_candidates(_trend_fixture(), min_confidence=0.5)
    trend = out[out["candidate_type"].isin(["short_trend_down_candidate", "short_trend_up_candidate"])]
    assert not trend.empty
    assert (trend["representative_anchor"] == True).all()  # noqa: E712
    assert (trend["segment_duplicate_suppressed_count"] >= 0).all()
    grouped = trend.groupby("segment_id").size()
    assert int(grouped.max()) <= 1


def test_late_rebound_exclusion_flags_present() -> None:
    out = detect_eurusd_pattern_candidates(_trend_fixture(), min_confidence=0.5)
    trend = out[out["candidate_type"].isin(["short_trend_down_candidate", "short_trend_up_candidate"])]
    assert "preferred_review_candidate" in trend.columns
    assert "excluded_late_reversal_anchor" in trend.columns
    assert trend["preferred_review_candidate"].isin([True, False]).all()
