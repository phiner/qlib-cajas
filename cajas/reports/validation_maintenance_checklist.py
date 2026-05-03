"""Maintenance checklist and artifact-freeze packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_count(audit: dict[str, Any]) -> int | None:
    direct = audit.get("read_csv_count")
    if isinstance(direct, int):
        return direct
    nested = (audit.get("summary") or {}).get("read_csv_count")
    if isinstance(nested, int):
        return nested
    return None


def build_validation_maintenance_checklist(
    *,
    maintenance_cadence: Path,
    release_readiness_report: Path,
    final_reviewer_packet: Path,
    milestone_packet: Path,
    runtime_budget_report: Path,
    runtime_edge_report: Path,
    runtime_release_cycle_report: Path,
    manifest_compatibility_report: Path,
    data_source_audit_report: Path,
    optional_followups: Path | None = None,
) -> dict[str, Any]:
    cadence = _load_json(maintenance_cadence)
    readiness = _load_json(release_readiness_report)
    reviewer = _load_json(final_reviewer_packet)
    milestone = _load_json(milestone_packet)
    budget = _load_json(runtime_budget_report)
    edge = _load_json(runtime_edge_report)
    runtime_cycle = _load_json(runtime_release_cycle_report)
    compat = _load_json(manifest_compatibility_report)
    audit = _load_json(data_source_audit_report)
    followups = _load_json(optional_followups) if optional_followups and optional_followups.exists() else {}

    blocking_items: list[str] = []
    if budget.get("overall_status") == "fail":
        blocking_items.append("runtime_budget_status=fail")
    if (budget.get("timing_consistency") or {}).get("status") == "fail":
        blocking_items.append("timing_consistency_status=fail")
    if edge.get("status") == "fail":
        blocking_items.append("runtime_edge_status=fail")
    if runtime_cycle.get("status") == "fail":
        blocking_items.append("runtime_release_cycle_status=fail")
    if compat.get("status") == "fail":
        blocking_items.append("manifest_compatibility_status=fail")
    if readiness.get("status") == "blocked":
        blocking_items.append("release_readiness_status=blocked")
    if reviewer.get("status") == "blocked":
        blocking_items.append("final_reviewer_packet_status=blocked")

    watch_items: list[str] = []
    if cadence.get("status") == "active":
        watch_items.append("maintenance_cadence_status=active")
    if budget.get("overall_status") == "warn":
        watch_items.append("runtime_budget_status=warn")
    if (budget.get("timing_consistency") or {}).get("status") == "warn":
        watch_items.append("timing_consistency_status=warn")
    if edge.get("status") in {"watch", "warn"}:
        watch_items.append(f"runtime_edge_status={edge.get('status')}")
    if runtime_cycle.get("status") in {"watch", "warn"}:
        watch_items.append(f"runtime_release_cycle_status={runtime_cycle.get('status')}")
    watch_items = sorted(set(watch_items))

    if blocking_items:
        status = "blocked"
    elif watch_items:
        status = "watch"
    else:
        status = "ready"

    review_state = "ready_for_review" if status != "blocked" else "blocked"

    routine_commands = [
        {
            "name": "fast_validation",
            "command": "./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json",
            "required": True,
            "expected_status": "pass",
        },
        {
            "name": "runtime_budget",
            "command": "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_validation_runtime_budget.py --budgets cajas/data_examples/validation_runtime_budgets.json --timing-json tmp/fast_validation_latest.json --out-json tmp/validation_runtime_budget_report.json --out-md tmp/validation_runtime_budget_report.md",
            "required": True,
            "expected_status": "pass",
        },
        {
            "name": "runtime_edge",
            "command": "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_runtime_edge_report.py --timing-json tmp/fast_validation_latest.json --runtime-budget-report tmp/validation_runtime_budget_report.json --out-json tmp/validation-runtime-edge-report.json --out-md tmp/validation-runtime-edge-report.md",
            "required": True,
            "expected_status": "pass",
        },
        {
            "name": "runtime_release_cycle",
            "command": "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_runtime_release_cycle_report.py --runtime-edge-report tmp/validation-runtime-edge-report.json --runtime-budget-report tmp/validation_runtime_budget_report.json --fast-timing-json tmp/fast_validation_latest.json --runtime-variance-report tmp/validation-runtime-variance-report.json --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json --out-json tmp/validation-runtime-release-cycle-report.json --out-md tmp/validation-runtime-release-cycle-report.md",
            "required": True,
            "expected_status": "pass",
        },
        {
            "name": "data_source_audit",
            "command": "./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /tmp/nonexistent-data-root-for-static-audit --out-json tmp/data_source_audit.json --out-md tmp/data_source_audit.md",
            "required": True,
            "expected_status": "read_csv_count_stable",
        },
        {
            "name": "final_reviewer_packet",
            "command": "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_final_reviewer_packet.py --release-ready-closure tmp/validation-release-ready-closure.json --alias-post-removal-closure tmp/alias-post-removal-closure.json --runtime-variance-closure tmp/validation-runtime-variance-closure.json --release-readiness-report tmp/validation-release-readiness.json --milestone-packet tmp/validation-milestone-packet.json --review-bundle-manifest tmp/validation-review-bundle/review_bundle_manifest.json --manifest-compatibility-report tmp/validation-review-bundle/manifest_compatibility_report.json --runtime-budget-report tmp/validation_runtime_budget_report.json --runtime-edge-report tmp/validation-runtime-edge-report.json --data-source-audit-report tmp/data_source_audit.json --maintenance-cadence tmp/validation-maintenance-cadence.json --maintenance-checklist tmp/validation-maintenance-checklist.json --optional-followups tmp/validation-optional-followups.json --out-json tmp/validation-final-reviewer-packet.json --out-md tmp/validation-final-reviewer-packet.md",
            "required": True,
            "expected_status": "ready_for_review",
        },
    ]

    canonical_artifacts = [
        "tmp/validation-final-reviewer-packet.md",
        "tmp/validation-release-readiness.md",
        "tmp/validation-milestone-packet.md",
        "tmp/validation-maintenance-cadence.md",
        "tmp/validation-review-bundle/review_bundle_manifest.json",
        "tmp/validation-review-bundle/review_bundle_index.md",
        "tmp/validation-review-bundle/manifest_compatibility_report.json",
        "tmp/validation_runtime_budget_report.json",
        "tmp/validation-runtime-edge-report.json",
        "tmp/validation-runtime-release-cycle-report.json",
        "tmp/validation-runtime-variance-closure.json",
        "tmp/data_source_audit.json",
    ]

    freeze_policy = {
        "canonical_review_surface": canonical_artifacts,
        "generated_artifacts": [
            "tmp/validation-maintenance-checklist.json",
            "tmp/validation-maintenance-checklist.md",
            "tmp/validation-optional-followups.json",
            "tmp/validation-optional-followups.md",
        ],
        "transient_artifacts": [
            "tmp/simulated-confirmed-clear/*",
            "tmp/validation-pytest-runtime-profile-before.json",
            "tmp/validation-pytest-runtime-profile-before.md",
        ],
        "preserved_compatibility": [
            "legacy read normalization kept for archived manifests",
            "no active history_update emission in canonical producer path",
        ],
        "do_not_manually_edit": canonical_artifacts,
    }

    optional_items = [item.get("reason") for item in followups.get("items", []) if isinstance(item, dict) and item.get("reason")]
    optional_items = optional_items or [
        "external consumer ownership/evidence completion for governance trail",
        "optional slow-test optimization from pytest profile",
    ]

    return {
        "schema_version": "v1",
        "status": status,
        "mode": "routine_maintenance",
        "review_state": review_state,
        "routine_commands": routine_commands,
        "canonical_artifacts": canonical_artifacts,
        "freeze_policy": freeze_policy,
        "blocking_policy": {
            "runtime_budget": "blocking",
            "manifest_compatibility": "blocking",
            "data_source_audit_read_csv_count_drift": "watch_or_blocking_by_policy",
            "optional_followups": "non_blocking",
        },
        "blocking_items": blocking_items,
        "watch_items": watch_items,
        "optional_followups": optional_items,
        "optional_followup_count": len(optional_items),
        "optional_followups_blocking": False,
        "rollback_readiness": "preserved",
        "recommended_cadence": cadence.get("recommended_cadence", "next_release_cycle"),
        "data_source_audit_expected_read_csv_count": _read_csv_count(audit),
        "scope_note": "Offline Qlib validation automation only; no trading execution scope.",
    }


def render_validation_maintenance_checklist_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Validation Maintenance Checklist",
            "",
            f"- status: `{payload.get('status')}`",
            f"- mode: `{payload.get('mode')}`",
            f"- review_state: `{payload.get('review_state')}`",
            f"- recommended_cadence: `{payload.get('recommended_cadence')}`",
            "",
            "## Routine Commands",
            "",
            *[
                f"- `{item.get('name')}` expected `{item.get('expected_status')}`: `{item.get('command')}`"
                for item in payload.get("routine_commands", [])
            ],
            "",
            "## Artifact Freeze Policy",
            "",
            f"- canonical_artifact_count: `{len(payload.get('canonical_artifacts', []))}`",
            f"- generated_artifact_count: `{len((payload.get('freeze_policy') or {}).get('generated_artifacts', []))}`",
            f"- transient_artifact_count: `{len((payload.get('freeze_policy') or {}).get('transient_artifacts', []))}`",
            f"- preserved_compatibility: `{(payload.get('freeze_policy') or {}).get('preserved_compatibility', [])}`",
            "",
            "## Blocking Policy",
            "",
            f"- `{payload.get('blocking_policy')}`",
            "",
            "## Optional Followups",
            "",
            *[f"- {item}" for item in payload.get("optional_followups", [])],
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
