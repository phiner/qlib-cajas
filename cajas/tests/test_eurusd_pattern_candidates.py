import pandas as pd

from cajas.research.eurusd_pattern_candidates import detect_eurusd_pattern_candidates


def _fixture() -> pd.DataFrame:
    rows = []
    base = 1.1000
    for i in range(120):
        o = base + (i % 5) * 0.00005
        c = o + (0.0002 if i % 2 == 0 else -0.00015)
        h = max(o, c) + 0.0003
        l = min(o, c) - 0.00025
        if i % 20 == 5:
            h = max(o, c) + 0.0007
        if i % 20 == 10:
            l = min(o, c) - 0.0007
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
        base += 0.00003
    return pd.DataFrame(rows)


def test_candidates_expected_columns_and_determinism() -> None:
    src = _fixture()
    out1 = detect_eurusd_pattern_candidates(src, min_confidence=0.55)
    out2 = detect_eurusd_pattern_candidates(src, min_confidence=0.55)
    assert list(out1.columns) == list(out2.columns)
    assert out1.equals(out2)
    for col in ["timestamp", "candidate_type", "confidence_score", "reason_codes", "review_priority"]:
        assert col in out1.columns


def test_detects_wick_and_expansion_patterns() -> None:
    src = _fixture()
    # Inject one explicit expansion bar to ensure deterministic expansion detection.
    src.loc[60, "high"] = src.loc[60, "high"] + 0.002
    src.loc[60, "low"] = src.loc[60, "low"] - 0.0015
    out = detect_eurusd_pattern_candidates(src, min_confidence=0.5)
    types = set(out["candidate_type"].tolist())
    assert "upper_wick_rejection_candidate" in types or "lower_wick_rejection_candidate" in types
    assert "expansion_candidate" in types or "compression_candidate" in types


def test_no_trading_action_columns() -> None:
    out = detect_eurusd_pattern_candidates(_fixture(), min_confidence=0.5)
    forbidden = {"buy", "sell", "long", "short", "order", "position", "target_position"}
    assert forbidden.isdisjoint({c.lower() for c in out.columns})
