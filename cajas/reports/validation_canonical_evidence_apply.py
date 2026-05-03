"""Guarded canonical evidence apply report for dry-run and explicit apply modes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _consumer_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item.get("name"): item for item in payload.get("consumers", []) if item.get("name")}


def _diff_summary(real: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    real_map = _consumer_map(real)
    candidate_map = _consumer_map(candidate)
    changed_consumers: list[str] = []
    status_changes: list[dict[str, str]] = []
    for name, cand in candidate_map.items():
        old = real_map.get(name, {})
        if old.get("status") != cand.get("status"):
            changed_consumers.append(name)
            status_changes.append(
                {
                    "consumer": name,
                    "from": str(old.get("status")),
                    "to": str(cand.get("status")),
                }
            )
    return {"changed_consumers": changed_consumers, "status_changes": status_changes}


def _rollback_plan(real_evidence: Path, backup_out: Path) -> list[str]:
    return [
        f"Restore apply target file from backup `{backup_out}`.",
        "Regenerate evidence closure, alias sunset review, release readiness, and milestone packet.",
        "Confirm release readiness returns to pre-apply watch state if rollback is needed.",
    ]


def _post_apply_commands() -> list[str]:
    return [
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_consumer_evidence_closure_report.py --consumer-evidence cajas/data_examples/history_alias_external_consumers.json --out-json tmp/history-alias-consumer-evidence-closure.json --out-md tmp/history-alias-consumer-evidence-closure.md",
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_alias_sunset_review.py --migration-readiness-report tmp/history-alias-migration-readiness.json --milestone-packet tmp/validation-milestone-packet.json --consumer-evidence cajas/data_examples/history_alias_external_consumers.json --out-json tmp/history-alias-sunset-review.json --out-md tmp/history-alias-sunset-review.md",
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_alias_removal_plan.py --alias-sunset-review tmp/history-alias-sunset-review.json --migration-readiness-report tmp/history-alias-migration-readiness.json --release-readiness-report tmp/validation-release-readiness.json --out-json tmp/history-alias-removal-plan.json --out-md tmp/history-alias-removal-plan.md",
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_release_readiness_report.py --milestone-packet tmp/validation-milestone-packet.json --alias-sunset-review tmp/history-alias-sunset-review.json --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json --runtime-variance-report tmp/validation-runtime-variance-report.json --runtime-edge-report tmp/validation-runtime-edge-report.json --runtime-budget-report tmp/validation_runtime_budget_report.json --alias-removal-plan tmp/history-alias-removal-plan.json --consumer-evidence-closure-report tmp/history-alias-consumer-evidence-closure.json --consumer-owner-handoff tmp/history-alias-consumer-owner-handoff.json --consumer-owner-response-validation tmp/history-alias-consumer-owner-response-validation.json --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json --out-json tmp/validation-release-readiness.json --out-md tmp/validation-release-readiness.md",
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_validation_milestone_packet.py --review-bundle-root tmp/validation-review-bundle --alias-fallback-bundle-root tmp/validation-review-bundle-alias-fallback --runtime-edge-report tmp/validation-runtime-edge-report.json --migration-readiness-report tmp/history-alias-migration-readiness.json --runtime-budget-report tmp/validation_runtime_budget_report.json --data-source-audit-report tmp/data_source_audit.json --fast-timing-json tmp/fast_validation_latest.json --alias-sunset-review tmp/history-alias-sunset-review.json --runtime-release-cycle-report tmp/validation-runtime-release-cycle-report.json --runtime-variance-report tmp/validation-runtime-variance-report.json --release-readiness-report tmp/validation-release-readiness.json --alias-removal-plan tmp/history-alias-removal-plan.json --consumer-evidence-closure-report tmp/history-alias-consumer-evidence-closure.json --consumer-owner-handoff tmp/history-alias-consumer-owner-handoff.json --consumer-owner-response-validation tmp/history-alias-consumer-owner-response-validation.json --runtime-watch-triage-report tmp/validation-runtime-watch-triage-report.json --pytest-runtime-profile tmp/validation-pytest-runtime-profile.json --out-json tmp/validation-milestone-packet.json --out-md tmp/validation-milestone-packet.md",
        "./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json",
        "PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_validation_runtime_budget.py --budgets cajas/data_examples/validation_runtime_budgets.json --timing-json tmp/fast_validation_latest.json --out-json tmp/validation_runtime_budget_report.json --out-md tmp/validation_runtime_budget_report.md",
        "./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /tmp/nonexistent-data-root-for-static-audit --out-json tmp/data_source_audit.json --out-md tmp/data_source_audit.md",
        "git diff --check && find cajas -path \"*/init.py\" && ./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py",
    ]


def build_canonical_evidence_apply_report(
    *,
    real_evidence: Path,
    candidate_evidence: Path,
    canonical_evidence_update_plan: Path,
    approval_file: Path,
    backup_out: Path,
    out_evidence: Path,
    dry_run: bool,
    apply_in_place: bool,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    real = _load_json(real_evidence)
    candidate = _load_json(candidate_evidence)
    plan = _load_json(canonical_evidence_update_plan)
    approval = _load_json(approval_file)

    approval_ok = approval.get("approved") is True
    plan_ready = plan.get("status") == "ready_to_apply"
    candidate_valid = bool(plan.get("candidate_valid", False))

    if not approval_ok:
        status = "blocked"
        next_action = "manual_approval_required"
    elif not plan_ready or not candidate_valid:
        status = "blocked"
        next_action = "fix_update_plan_inputs"
    elif apply_in_place and not backup_out:
        status = "blocked"
        next_action = "provide_backup_path"
    elif dry_run:
        status = "dry_run_ready"
        next_action = "manual_apply_in_dedicated_phase"
    elif apply_in_place:
        status = "applied"
        next_action = "run_post_apply_validations"
    else:
        status = "dry_run_ready"
        next_action = "manual_apply_in_dedicated_phase"

    write_payload: dict[str, Any] | None = None
    if status in {"dry_run_ready", "applied"}:
        out_evidence.parent.mkdir(parents=True, exist_ok=True)
        out_evidence.write_text(json.dumps(candidate, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        write_payload = candidate
    if status == "applied":
        current_target = _load_json(out_evidence) if out_evidence.exists() else real
        backup_out.parent.mkdir(parents=True, exist_ok=True)
        backup_out.write_text(json.dumps(current_target, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        out_evidence.write_text(json.dumps(candidate, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    payload = {
        "schema_version": "v1",
        "status": status,
        "apply_in_place": apply_in_place,
        "dry_run": dry_run,
        "real_evidence_file": str(real_evidence),
        "candidate_evidence_file": str(candidate_evidence),
        "backup_file": str(backup_out),
        "out_evidence_file": str(out_evidence),
        "diff_summary": _diff_summary(real, candidate),
        "rollback_plan": _rollback_plan(real_evidence, backup_out),
        "post_apply_validation_commands": _post_apply_commands(),
        "alias_fallback_removal_allowed": False,
        "next_action": next_action,
        "scope_note": "Offline Qlib validation automation only; this phase does not remove fallback.",
    }
    return payload, write_payload


def render_canonical_evidence_apply_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Canonical Evidence Apply Guard",
            "",
            f"- Status: `{payload.get('status', 'invalid')}`",
            f"- apply_in_place: `{payload.get('apply_in_place', False)}`",
            f"- dry_run: `{payload.get('dry_run', True)}`",
            f"- alias_fallback_removal_allowed: `{payload.get('alias_fallback_removal_allowed', False)}`",
            f"- next_action: `{payload.get('next_action')}`",
            "",
            "## Diff Summary",
            "",
            f"- changed_consumers: `{(payload.get('diff_summary') or {}).get('changed_consumers', [])}`",
            f"- status_changes: `{(payload.get('diff_summary') or {}).get('status_changes', [])}`",
            "",
            "## Rollback Plan",
            "",
            *[f"- {step}" for step in payload.get("rollback_plan", [])],
            "",
            "## Post-Apply Validation Commands",
            "",
            *[f"- `{cmd}`" for cmd in payload.get("post_apply_validation_commands", [])],
            "",
            "## Non-Goal",
            "",
            "- Do not remove alias fallback in this phase.",
            "",
            "## Scope Boundary",
            "",
            f"- {payload.get('scope_note', '')}",
            "",
        ]
    )
