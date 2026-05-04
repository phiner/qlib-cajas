from cajas.reports.validation_eurusd_pattern_label_schema import build_validation_eurusd_pattern_label_schema


def test_label_schema_ready_and_version() -> None:
    payload = build_validation_eurusd_pattern_label_schema()
    assert payload["status"] == "ready"
    assert payload["schema_version"] == "eurusd_15m_pattern_review_v1"


def test_label_schema_allowed_values_and_ranges() -> None:
    payload = build_validation_eurusd_pattern_label_schema()
    assert "human_pattern_label" in payload["allowed_values"]
    assert payload["numeric_ranges"]["structure_quality"]["min"] == 1
    assert payload["numeric_ranges"]["review_confidence"]["max"] == 5
