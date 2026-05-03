import pandas as pd

from cajas.research.eurusd_pattern_features import (
    compute_eurusd_pattern_features,
    validate_feature_scaffold_contract,
)


def test_feature_columns_and_no_mutation() -> None:
    src = pd.DataFrame(
        {
            "open": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
            "high": [1.2, 1.3, 1.4, 1.5, 1.6, 1.7],
            "low": [0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
            "close": [1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
        }
    )
    snapshot = src.copy(deep=True)
    out = compute_eurusd_pattern_features(src, horizons=(3, 5))
    assert src.equals(snapshot)
    assert "body" in out.columns
    assert "upper_wick" in out.columns
    assert "close_pct_change_3" in out.columns
    assert "rolling_range_position_5" in out.columns
    assert "vol_norm_move_5" in out.columns


def test_known_values() -> None:
    src = pd.DataFrame(
        {
            "open": [1.00, 1.02, 1.01],
            "high": [1.03, 1.04, 1.05],
            "low": [0.99, 1.00, 1.00],
            "close": [1.02, 1.01, 1.04],
        }
    )
    out = compute_eurusd_pattern_features(src, horizons=(3,))
    assert round(float(out.loc[0, "body"]), 6) == 0.02
    assert round(float(out.loc[1, "body"]), 6) == -0.01
    assert round(float(out.loc[0, "upper_wick"]), 6) == 0.01
    assert round(float(out.loc[0, "lower_wick"]), 6) == 0.01


def test_short_dataset_graceful() -> None:
    src = pd.DataFrame(
        {
            "open": [1.0],
            "high": [1.1],
            "low": [0.9],
            "close": [1.0],
        }
    )
    out = compute_eurusd_pattern_features(src, horizons=(55,))
    assert out.shape[0] == 1
    assert "close_pct_change_55" in out.columns


def test_feature_scaffold_contract_passes() -> None:
    payload = validate_feature_scaffold_contract()
    assert payload["status"] == "pass"
