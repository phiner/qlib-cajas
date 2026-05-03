"""History alias migration readiness report for review bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate_map_by_name(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    gates = payload.get("gates", [])
    return {g.get("name"): g for g in gates if isinstance(g, dict) and g.get("name")}


def _required_gate_signature(payload: dict[str, Any]) -> dict[str, str]:
    sig: dict[str, str] = {}
    for gate in payload.get("gates", []):
        if gate.get("required"):
            sig[gate["name"]] = gate.get("status", "unknown")
    return sig


def _optional_gate_signature(payload: dict[str, Any]) -> dict[str, str]:
    sig: dict[str, str] = {}
    for gate in payload.get("gates", []):
        if not gate.get("required"):
            sig[gate["name"]] = gate.get("status", "unknown")
    return sig


def build_history_alias_migration_report(
    *,
    default_bundle_root: Path,
    no_alias_bundle_root: Path,
) -> dict[str, Any]:
    default_manifest = _load_json(default_bundle_root / "review_bundle_manifest.json")
    no_alias_manifest = _load_json(no_alias_bundle_root / "review_bundle_manifest.json")
    default_final = _load_json(default_bundle_root / "final_status.json")
    no_alias_final = _load_json(no_alias_bundle_root / "final_status.json")
    default_matrix = _load_json(default_bundle_root / "profile_matrix.json")
    no_alias_matrix = _load_json(no_alias_bundle_root / "profile_matrix.json")

    checks: list[dict[str, str]] = []

    default_compat = (default_manifest.get("manifest_compatibility") or {}).get("status")
    no_alias_compat = (no_alias_manifest.get("manifest_compatibility") or {}).get("status")
    checks.append(
        {
            "name": "default_manifest_compatibility",
            "status": "pass" if default_compat == "pass" else "fail",
            "summary": f"Default manifest compatibility status is {default_compat!r}.",
        }
    )
    compare_label = "alias-fallback" if "alias-fallback" in str(no_alias_bundle_root) else "no-alias"
    checks.append(
        {
            "name": f"{compare_label}_manifest_compatibility",
            "status": "pass" if no_alias_compat == "pass" else "fail",
            "summary": f"{compare_label} manifest compatibility status is {no_alias_compat!r}.",
        }
    )

    profs = ["local", "ci", "strict"]
    default_profile_status = {
        p: (default_matrix.get("profiles", {}).get(p, {}) or {}).get("overall_status", "unknown")
        for p in profs
    }
    no_alias_profile_status = {
        p: (no_alias_matrix.get("profiles", {}).get(p, {}) or {}).get("overall_status", "unknown")
        for p in profs
    }
    profile_match = default_profile_status == no_alias_profile_status
    checks.append(
        {
            "name": "profile_status_equivalence",
            "status": "pass" if profile_match else "fail",
            "summary": "local/ci/strict statuses match." if profile_match else "local/ci/strict statuses differ.",
        }
    )

    default_required = _required_gate_signature(default_final)
    no_alias_required = _required_gate_signature(no_alias_final)
    required_match = default_required == no_alias_required
    checks.append(
        {
            "name": "required_gate_equivalence",
            "status": "pass" if required_match else "fail",
            "summary": "Required gates match." if required_match else "Required gate outcomes differ.",
        }
    )

    default_optional = _optional_gate_signature(default_final)
    no_alias_optional = _optional_gate_signature(no_alias_final)
    optional_diff = default_optional != no_alias_optional

    if any(c["status"] == "fail" for c in checks):
        status = "fail"
    elif optional_diff:
        status = "warn"
    else:
        status = "pass"

    if status == "pass":
        recommendation = "ready_for_default_no_alias_trial"
        next_action = "Schedule a controlled future phase to flip default alias emission to canonical-only."
    else:
        recommendation = "not_ready"
        next_action = "Keep current default alias behavior and resolve mismatches before default flip."

    return {
        "schema_version": "v1",
        "status": status,
        "default_bundle_root": str(default_bundle_root),
        "no_alias_bundle_root": str(no_alias_bundle_root),
        "comparison_mode": compare_label,
        "checks": checks,
        "profile_status_comparison": {
            "default": default_profile_status,
            "no_alias": no_alias_profile_status,
            "equivalent": profile_match,
        },
        "required_gate_comparison": {
            "default": default_required,
            "no_alias": no_alias_required,
            "equivalent": required_match,
        },
        "optional_gate_differences": {
            "has_differences": optional_diff,
            "default": default_optional,
            "no_alias": no_alias_optional,
        },
        "recommendation": recommendation,
        "next_action": next_action,
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_history_alias_migration_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# History Alias Migration Readiness",
        "",
        f"- Status: `{payload.get('status', 'warn')}`",
        f"- Recommendation: `{payload.get('recommendation', 'not_ready')}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Summary |",
        "|---|---|---|",
    ]
    for check in payload.get("checks", []):
        lines.append(f"| {check.get('name', '-') } | {check.get('status', '-') } | {check.get('summary', '-') } |")

    lines.extend(
        [
            "",
            "## Profile Status Comparison",
            "",
            f"- Default: `{payload.get('profile_status_comparison', {}).get('default', {})}`",
            f"- No-alias: `{payload.get('profile_status_comparison', {}).get('no_alias', {})}`",
            "",
            "## Required Gate Comparison",
            "",
            f"- Equivalent: `{payload.get('required_gate_comparison', {}).get('equivalent', False)}`",
            "",
            "## Optional Differences",
            "",
            f"- Has differences: `{payload.get('optional_gate_differences', {}).get('has_differences', False)}`",
            "",
            "## Next Action",
            "",
            f"- {payload.get('next_action', 'Review differences.')}",
            "",
            "## Scope Note",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
    return "\n".join(lines)
