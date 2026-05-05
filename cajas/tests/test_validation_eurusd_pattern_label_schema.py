from cajas.reports.validation_eurusd_pattern_label_schema import build_validation_eurusd_pattern_label_schema
from cajas.research.eurusd_review_schema import ALLOWED_VALUES, FIVE_LAYER_ENUM_FIELDS


def test_label_schema_ready_and_version() -> None:
    payload = build_validation_eurusd_pattern_label_schema()
    assert payload["status"] == "ready"
    assert payload["schema_version"] == "eurusd_15m_pattern_review_v3"
    assert "eurusd_15m_pattern_review_v1" in payload["compatible_schema_versions"]
    assert "eurusd_15m_pattern_review_v2" in payload["compatible_schema_versions"]


def test_label_schema_allowed_values_and_ranges() -> None:
    payload = build_validation_eurusd_pattern_label_schema()
    allowed = payload["allowed_values"]
    assert "human_pattern_label" in allowed
    assert "uptrend" in allowed["market_context"]
    assert "choppy" in allowed["market_context"]
    assert "downtrend" in allowed["market_context"]
    assert "not_reviewed" in allowed["market_context"]
    assert "unclear" in allowed["market_context"]
    assert "up_pullback" in allowed["direction_context"]
    assert "down_pullback" in allowed["direction_context"]
    assert "reversal_up" in allowed["direction_context"]
    assert "reversal_down" in allowed["direction_context"]
    assert "mixed" in allowed["direction_context"]
    assert "unclear" in allowed["direction_context"]
    assert "range" in allowed["market_context"]
    assert "transition" in allowed["market_context"]
    assert "up" in allowed["direction_context"]
    assert "down" in allowed["direction_context"]
    assert "neutral" in allowed["direction_context"]
    assert "structure_location" in allowed
    assert "local_behavior" in allowed
    assert "confirmation_result" in allowed
    assert "review_outcome" in allowed
    assert "pattern_quality" in allowed
    assert "false_positive_reason" in allowed
    assert "review_confidence_level" in allowed
    assert "primary_candidate_family" in allowed
    assert "secondary_candidate_family" in allowed
    assert "trend_direction" in allowed
    assert "trend_stage" in allowed
    assert "volatility_state" in allowed
    assert "recent_move_context" in allowed
    assert "level_quality" in allowed
    assert "session_context" in allowed
    assert "not_reviewed" in allowed["review_outcome"]
    assert "not_enough_context" in allowed["review_outcome"]
    assert "partial_follow_through" in allowed["confirmation_result"]
    assert "delayed_follow_through" in allowed["confirmation_result"]
    assert "none" in allowed["secondary_candidate_family"]
    assert "needs_recheck" in allowed["review_status"]
    assert "skip" in allowed["review_status"]
    assert "sideways" in payload["legacy_allowed_values"]["direction_context"]
    assert "trend" in payload["legacy_allowed_values"]["market_context"]
    assert "pullback" in payload["legacy_allowed_values"]["market_context"]
    assert "breakout" in payload["legacy_allowed_values"]["market_context"]
    assert payload["numeric_ranges"]["structure_quality"]["min"] == 1
    assert payload["numeric_ranges"]["review_confidence"]["max"] == 5


def test_label_schema_includes_five_layer_summary_and_allowed_values() -> None:
    payload = build_validation_eurusd_pattern_label_schema()
    summary = payload["five_layer_schema"]
    assert summary["ordered_fields"] == list(FIVE_LAYER_ENUM_FIELDS)
    for field in FIVE_LAYER_ENUM_FIELDS:
        assert payload["allowed_values"][field] == ALLOWED_VALUES[field]
        assert field in summary["field_descriptions_cn"]

    policy = payload["candidate_type_policy"]
    assert policy["entry_tag_only"] is True
    assert policy["final_pattern_truth"] is False
    assert "spike_up_reversal" not in payload["allowed_values"]["market_context"]
    assert "spike_up_reversal" in payload["allowed_values"]["recent_move_context"]
    assert "consolidation_after_impulse" in payload["allowed_values"]["trend_stage"]
