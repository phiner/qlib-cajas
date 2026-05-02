"""Classify governance findings conservatively for remediation reporting."""

from __future__ import annotations


def classify_governance_finding(*, finding: dict) -> str:
    snippet = str(finding.get("snippet", "")).lower()
    category = str(finding.get("category", "")).lower()
    file_path = str(finding.get("file", "")).lower()

    if any(x in snippet for x in ("no broker", "forbidden", "blocked", "do not add live trading", "paper trading execution is blocked")):
        return "allowed_boundary_documentation"
    if "/tests/" in file_path or file_path.endswith(".md"):
        if any(x in snippet for x in ("broker", "live trading", "pnl optimization", "position sizing")):
            return "allowed_test_fixture"
    if any(x in snippet for x in ("--broker", "--live", "--paper")):
        return "allowed_cli_argument_name"
    if any(x in snippet for x in ("submit_order", "route_order", "broker client", "position sizing function")):
        return "true_violation"
    if category in {"credentials", "network_calls", "live_trading", "broker_integration"} and "allowed" not in snippet:
        return "needs_manual_review"
    if finding.get("severity") == "warning":
        return "false_positive_candidate"
    return "needs_manual_review"

