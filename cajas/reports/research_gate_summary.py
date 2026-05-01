"""Render markdown summary for research gate packets."""

from __future__ import annotations


def render_research_gate_summary(*, gate_packet: dict, no_broker_packet: dict) -> str:
    checks = gate_packet.get("checks", [])
    artifact_checks = gate_packet.get("artifact_checks", [])
    count = {"pass": 0, "warn": 0, "fail": 0, "blocked": 0}
    for item in checks + artifact_checks:
        d = item.get("decision")
        if d in count:
            count[d] += 1

    lines = [
        "# Research Gate Summary",
        "",
        f"- final_status: `{gate_packet.get('final_status')}`",
        f"- pass checks: `{count['pass']}`",
        f"- warn checks: `{count['warn']}`",
        f"- fail checks: `{count['fail']}`",
        f"- blocked checks: `{count['blocked']}`",
        "",
        "## Metric Summary",
        f"- accuracy: `{gate_packet.get('metric_summary', {}).get('accuracy')}`",
        f"- macro_f1: `{gate_packet.get('metric_summary', {}).get('macro_f1')}`",
        "",
        "## Blocked Actions",
    ]
    blocked = no_broker_packet.get("next_blocked_actions", [])
    if not blocked:
        lines.append("- none")
    else:
        for b in blocked:
            if isinstance(b, dict):
                lines.append(f"- {b.get('action')}: {b.get('reason')}")
            else:
                lines.append(f"- {b}")
    lines += ["", "## Manual Review Checklist"]
    for item in gate_packet.get("manual_review_checklist", []):
        lines.append(f"- {item.get('item')}: {item.get('rationale')}")
    return "\n".join(lines) + "\n"
