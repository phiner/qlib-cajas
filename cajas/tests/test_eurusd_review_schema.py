from cajas.research.eurusd_review_schema import (
    ALLOWED_VALUES,
    DEFAULT_REVIEW_VALUES,
    FIVE_LAYER_ENUM_FIELDS,
    LEGACY_ALLOWED_VALUES,
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


def test_legacy_value_can_warn_without_error() -> None:
    row = default_review_values()
    row["direction_context"] = LEGACY_ALLOWED_VALUES["direction_context"][0]
    result = validate_review_row(row, allow_legacy=True)
    assert result["errors"] == []
    assert any(x.startswith("legacy_value:direction_context") for x in result["warnings"])


def test_gui_default_review_values_stays_importable_and_compatible() -> None:
    defaults = gui_default_review_values()
    assert defaults["human_pattern_label"] == "unclear"
    assert defaults["review_status"] == "pending"
    assert "structure_location" in defaults
    assert defaults["structure_location"] == "not_reviewed"
