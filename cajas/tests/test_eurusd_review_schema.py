from cajas.research.eurusd_review_schema import (
    ALLOWED_VALUES,
    CANONICAL_REVIEW_FIELDS,
    DEFAULT_REVIEW_VALUES,
    FIVE_LAYER_ENUM_FIELDS,
    default_review_values,
    validate_review_row,
)
from cajas.research.eurusd_pattern_review_gui import default_review_values as gui_default_review_values


def test_every_schema_field_has_allowed_values() -> None:
    assert ALLOWED_VALUES
    for field, values in ALLOWED_VALUES.items():
        assert isinstance(values, list)
        assert len(values) > 0


def test_defaults_are_in_allowed_values() -> None:
    for field, value in DEFAULT_REVIEW_VALUES.items():
        if field in ALLOWED_VALUES:
            assert value in ALLOWED_VALUES[field]


def test_not_reviewed_exists_for_five_layer_fields() -> None:
    for field in FIVE_LAYER_ENUM_FIELDS:
        assert "not_reviewed" in ALLOWED_VALUES[field]


def test_default_review_row_is_valid() -> None:
    row = default_review_values()
    result = validate_review_row(row)
    assert result["errors"] == []


def test_validation_fails_for_unknown_value() -> None:
    row = default_review_values()
    row["local_behavior"] = "unknown_behavior"
    result = validate_review_row(row)
    assert any(x.startswith("invalid_value:local_behavior") for x in result["errors"])


def test_gui_default_review_values_stays_importable_and_compatible() -> None:
    defaults = gui_default_review_values()
    assert "structure_location" in defaults
    assert defaults["structure_location"] == "not_reviewed"


def test_new_vocabulary_fields_exist_in_defaults() -> None:
    row = default_review_values()
    for field in [
        "recent_move_context",
        "trend_direction",
        "trend_stage",
        "volatility_state",
        "level_quality",
        "session_context",
    ]:
        assert field in row
        assert row[field] == "not_reviewed"
    for field in ["direction_context", "review_status", "structure_quality", "follow_through_quality", "review_confidence_level"]:
        assert field not in row


def test_recent_move_context_values_and_market_context_boundary() -> None:
    assert "recent_move_context" in ALLOWED_VALUES
    assert "spike_up_reversal" in ALLOWED_VALUES["recent_move_context"]
    assert "spike_down_reversal" in ALLOWED_VALUES["recent_move_context"]
    assert "sharp_rise_then_consolidation" in ALLOWED_VALUES["recent_move_context"]
    assert "sharp_drop_then_consolidation" in ALLOWED_VALUES["recent_move_context"]
    assert "spike_up_reversal" not in ALLOWED_VALUES["market_context"]


def test_extended_vocabulary_completeness_rules() -> None:
    assert "consolidation_after_impulse" in ALLOWED_VALUES["trend_stage"]
    assert "middle_of_nowhere" in ALLOWED_VALUES["structure_location"]
    assert "none" in ALLOWED_VALUES["secondary_candidate_family"]


def test_canonical_review_fields_list_is_five_layer_only() -> None:
    assert "review_confidence" in CANONICAL_REVIEW_FIELDS
    assert "human_rationale_zh" in CANONICAL_REVIEW_FIELDS
    assert "human_counterexample_zh" in CANONICAL_REVIEW_FIELDS
    assert "human_uncertainty_reason_zh" in CANONICAL_REVIEW_FIELDS
    assert "human_context_notes_zh" in CANONICAL_REVIEW_FIELDS
    assert "review_confidence_level" not in CANONICAL_REVIEW_FIELDS
    for field in ["direction_context", "review_status", "structure_quality", "follow_through_quality", "pattern_label"]:
        assert field not in CANONICAL_REVIEW_FIELDS
