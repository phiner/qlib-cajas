from cajas.reports.validation_eurusd_pattern_label_schema import build_validation_eurusd_pattern_label_schema


def test_label_schema_ready_and_version() -> None:
    payload = build_validation_eurusd_pattern_label_schema()
    assert payload["status"] == "ready"
    assert payload["schema_version"] == "eurusd_15m_pattern_review_v2"
    assert "eurusd_15m_pattern_review_v1" in payload["compatible_schema_versions"]


def test_label_schema_allowed_values_and_ranges() -> None:
    payload = build_validation_eurusd_pattern_label_schema()
    allowed = payload["allowed_values"]
    assert "human_pattern_label" in allowed
    assert "pullback" in allowed["market_context"]
    assert "breakout" in allowed["market_context"]
    assert "reversal_attempt" in allowed["market_context"]
    assert "unclear" in allowed["market_context"]
    assert "up_pullback" in allowed["direction_context"]
    assert "down_pullback" in allowed["direction_context"]
    assert "reversal_up" in allowed["direction_context"]
    assert "reversal_down" in allowed["direction_context"]
    assert "mixed" in allowed["direction_context"]
    assert "unclear" in allowed["direction_context"]
    assert "trend" in allowed["market_context"]
    assert "range" in allowed["market_context"]
    assert "transition" in allowed["market_context"]
    assert "up" in allowed["direction_context"]
    assert "down" in allowed["direction_context"]
    assert "neutral" in allowed["direction_context"]
    assert "needs_recheck" in allowed["review_status"]
    assert "skip" in allowed["review_status"]
    assert "sideways" in payload["legacy_allowed_values"]["direction_context"]
    assert payload["numeric_ranges"]["structure_quality"]["min"] == 1
    assert payload["numeric_ranges"]["review_confidence"]["max"] == 5
