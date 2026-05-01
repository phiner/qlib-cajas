"""No-broker dry-run review packet builder."""

from __future__ import annotations


def build_no_broker_dry_run_packet(*, gate_packet: dict) -> dict:
    return {
        "schema_version": "v1",
        "gate_summary": {
            "final_status": gate_packet.get("final_status"),
            "metric_summary": gate_packet.get("metric_summary", {}),
        },
        "artifact_references": gate_packet.get("source_artifact_paths", {}),
        "disabled_capabilities": [
            "no_broker",
            "no_order_routing",
            "no_live_market_data",
            "no_paper_trading_execution",
            "no_portfolio_sizing",
            "no_pnl_optimization",
        ],
        "review_checklist": gate_packet.get("manual_review_checklist", []),
        "next_permitted_actions": [
            "offline artifact review",
            "manual threshold tuning for research",
            "prepare next offline phase input set",
        ],
        "next_blocked_actions": gate_packet.get("blocked_actions", []),
    }
