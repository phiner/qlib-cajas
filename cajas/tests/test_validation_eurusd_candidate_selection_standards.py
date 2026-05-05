from cajas.reports.validation_eurusd_candidate_selection_standards import (
    build_validation_eurusd_candidate_selection_standards,
)


REQUIRED_TYPES = {
    "short_trend_up_candidate",
    "short_trend_down_candidate",
    "mid_trend_up_candidate",
    "mid_trend_down_candidate",
    "lower_wick_rejection_candidate",
    "upper_wick_rejection_candidate",
    "possible_false_breakout_candidate",
    "doji_indecision_candidate",
    "compression_candidate",
    "expansion_candidate",
}


REQUIRED_FIELDS = {
    "candidate_type",
    "rule_family",
    "primary_inputs",
    "lookback_window",
    "future_window_used_by_candidate_logic",
    "future_window_used_by_review_filter",
    "reason_codes",
    "selection_reason_codes",
    "primary_selection_reason",
    "known_failure_modes",
    "current_tail_risk",
    "review_guidance",
}


def test_selection_standards_cover_all_required_types_and_fields() -> None:
    payload = build_validation_eurusd_candidate_selection_standards()
    assert payload["status"] == "ready"
    rows = payload["candidate_selection_standards"]
    assert len(rows) >= 10
    got = {r["candidate_type"] for r in rows}
    assert REQUIRED_TYPES.issubset(got)
    for row in rows:
        assert REQUIRED_FIELDS.issubset(set(row.keys()))
