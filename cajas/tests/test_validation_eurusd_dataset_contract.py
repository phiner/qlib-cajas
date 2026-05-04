from cajas.reports.validation_eurusd_dataset_contract import (
    build_validation_eurusd_dataset_contract,
    render_validation_eurusd_dataset_contract_markdown,
)


def test_contract_ready_for_eurusd_15m() -> None:
    payload = build_validation_eurusd_dataset_contract()
    assert payload["status"] == "ready"
    assert payload["symbol"] == "EURUSD"
    assert payload["timeframe"] == "15m"
    assert payload["fixed_timeframe_policy"]["aggregation_allowed"] is False


def test_contract_blocked_for_non_15m() -> None:
    payload = build_validation_eurusd_dataset_contract(timeframe="1h")
    assert payload["status"] == "blocked"


def test_contract_markdown_contains_policy() -> None:
    md = render_validation_eurusd_dataset_contract_markdown(build_validation_eurusd_dataset_contract())
    lower = md.lower()
    assert "fixed to `15m`" in md
    assert "no timeframe aggregation" in lower
