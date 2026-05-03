#!/usr/bin/env python3
"""Build validation review bundle by orchestrating existing validation CLIs."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from cajas.reports.validation_review_bundle_history import (
    append_snapshot,
    compute_delta,
    create_snapshot_from_bundle,
    detect_regressions,
    generate_history_summary_markdown,
    read_snapshots,
)
from cajas.reports.validation_gate_summary import (
    DEFAULT_CI_PROFILES,
    ValidationGate,
    build_final_status_payload,
    load_ci_profile_policy,
    render_final_status_markdown,
)
from cajas.reports.validation_review_bundle_metadata import (
    HISTORY_STATUS_FAIL,
    HISTORY_STATUS_PASS,
    infer_history_status,
    normalize_history_metadata,
    summarize_compatibility_issues,
    validate_history_metadata_compatibility,
)
from cajas.scripts.check_review_bundle_manifest_compatibility import (
    build_compatibility_report,
    render_compatibility_markdown,
)

def _extract_read_csv_count(audit_data: dict[str, Any] | None) -> int | None:
    if not isinstance(audit_data, dict):
        return None
    top = audit_data.get("read_csv_count")
    if isinstance(top, int):
        return top
    summary = audit_data.get("summary")
    if isinstance(summary, dict):
        nested = summary.get("read_csv_count")
        if isinstance(nested, int):
            return nested
    return None


def get_git_info() -> dict[str, str]:
    """Get current git branch and commit."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return {"branch": branch, "commit": commit}
    except Exception:
        return {"branch": "unknown", "commit": "unknown"}


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        env = dict(**__import__("os").environ)
        repo_root = str(Path(__file__).resolve().parents[2])
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{repo_root}:{existing_pythonpath}" if existing_pythonpath else repo_root
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"


def format_seconds(value: Any) -> str:
    """Format seconds for human-readable markdown output."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}s"
    except (TypeError, ValueError):
        return "N/A"


def _load_json_if_exists(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None



def build_review_bundle(
    bundle_name: str,
    out_root: Path,
    smoke_root: Path,
    fast_timing_json: Path | None,
    budgets: Path | None,
    baseline_root: Path | None,
    create_baseline_from_current: bool,
    run_fast_validation: bool,
    skip_fast_validation: bool,
    run_data_source_audit: bool,
    skip_data_source_audit: bool,
    data_root: Path | None,
    build_experiment_manifest: bool,
    copy_artifacts: bool,
    update_history: bool,
    history_jsonl: Path | None,
    history_last_n: int,
    check_manifest_compatibility: bool = False,
    manifest_compatibility_out_json: Path | None = None,
    manifest_compatibility_out_md: Path | None = None,
    warn_only: bool = False,
    ci: bool = False,
    fail_on_warn: bool = False,
    skip_history: bool = False,
    skip_manifest_compatibility: bool = False,
    skip_runtime_budget: bool = False,
    max_timing_age_seconds: int = 3600,
    ci_profile: str = "ci",
    ci_profile_config: Path | None = None,
    omit_history_update_alias: bool = False,
    include_history_update_alias: bool = False,
) -> dict[str, Any]:
    """Build validation review bundle."""
    out_root.mkdir(parents=True, exist_ok=True)

    git_info = get_git_info()
    commands_executed = []
    commands_skipped = []
    artifacts = {}
    warnings = []
    runtime_budget_report_data: dict[str, Any] | None = None

    if ci:
        if ci_profile not in DEFAULT_CI_PROFILES:
            raise ValueError(f"unknown ci_profile: {ci_profile}")
        if skip_history:
            update_history = False
        elif not update_history:
            update_history = True
        if skip_manifest_compatibility:
            check_manifest_compatibility = False
        elif not check_manifest_compatibility:
            check_manifest_compatibility = True
        if skip_runtime_budget:
            budgets = None
        if not run_fast_validation and not fast_timing_json:
            message = "CI mode requires --fast-timing-json or --run-fast-validation."
            if warn_only:
                warnings.append(message)
            else:
                raise RuntimeError(message)
    profile_config, profile_policy = load_ci_profile_policy(
        ci_profile if ci else "local",
        ci_profile_config,
    )

    # Step 1: Run dataset quality smoke
    smoke_cmd = [
        sys.executable,
        "cajas/scripts/run_dataset_quality_smoke.py",
        "--out-root",
        str(smoke_root),
    ]
    success, output = run_command(smoke_cmd, "dataset quality smoke")
    if success:
        commands_executed.append({"command": " ".join(smoke_cmd), "status": "ok"})
        artifacts["smoke_root"] = str(smoke_root)
    else:
        commands_executed.append({"command": " ".join(smoke_cmd), "status": "fail", "error": output})

    # Step 2: Fast validation timing
    if run_fast_validation:
        fast_timing_json = out_root / "fast_validation_timing.json"
        fast_cmd = [
            sys.executable,
            "cajas/scripts/run_fast_validation.py",
            "--tier",
            "fast",
            "--timing-json",
            str(fast_timing_json),
        ]
        success, output = run_command(fast_cmd, "fast validation")
        if success:
            commands_executed.append({"command": " ".join(fast_cmd), "status": "ok"})
            artifacts["fast_timing_json"] = str(fast_timing_json)
        else:
            commands_executed.append({"command": " ".join(fast_cmd), "status": "fail", "error": output})
    elif skip_fast_validation:
        commands_skipped.append({"command": "run_fast_validation.py", "reason": "skip requested"})
    elif fast_timing_json and fast_timing_json.exists():
        commands_skipped.append({"command": "run_fast_validation.py", "reason": "using existing timing JSON"})
        artifacts["fast_timing_json"] = str(fast_timing_json)
    else:
        commands_skipped.append({"command": "run_fast_validation.py", "reason": "no timing JSON provided"})

    # Step 3: Runtime budget check
    runtime_budget_json = out_root / "validation_runtime_budget_report.json"
    runtime_budget_md = out_root / "validation_runtime_budget_report.md"
    if fast_timing_json and fast_timing_json.exists() and budgets and budgets.exists():
        budget_cmd = [
            sys.executable,
            "cajas/scripts/check_validation_runtime_budget.py",
            "--budgets",
            str(budgets),
            "--timing-json",
            str(fast_timing_json),
            "--out-json",
            str(runtime_budget_json),
            "--out-md",
            str(runtime_budget_md),
            "--max-age-seconds",
            str(max_timing_age_seconds),
        ]
        success, output = run_command(budget_cmd, "runtime budget check")
        if success:
            commands_executed.append({"command": " ".join(budget_cmd), "status": "ok"})
            artifacts["runtime_budget_report"] = str(runtime_budget_json)
            runtime_budget_report_data = _load_json_if_exists(runtime_budget_json)
        else:
            commands_executed.append({"command": " ".join(budget_cmd), "status": "fail", "error": output})
    else:
        commands_skipped.append({"command": "check_validation_runtime_budget.py", "reason": "missing timing JSON or budgets"})

    # Step 4: Reviewer diff
    reviewer_diff_json = out_root / "reviewer_diff_report.json"
    reviewer_diff_md = out_root / "reviewer_diff_report.md"
    if create_baseline_from_current and smoke_root.exists():
        baseline_root = out_root / "baseline_smoke"
        baseline_root.mkdir(parents=True, exist_ok=True)
        # Copy smoke artifacts as baseline
        import shutil
        if (smoke_root / "contract").exists():
            shutil.copytree(smoke_root / "contract", baseline_root / "contract", dirs_exist_ok=True)
        artifacts["baseline_root"] = str(baseline_root)

    if baseline_root and baseline_root.exists():
        diff_cmd = [
            sys.executable,
            "cajas/scripts/build_reviewer_diff_report.py",
            "--baseline-root",
            str(baseline_root),
            "--current-root",
            str(smoke_root),
            "--out-json",
            str(reviewer_diff_json),
            "--out-md",
            str(reviewer_diff_md),
        ]
        success, output = run_command(diff_cmd, "reviewer diff")
        if success:
            commands_executed.append({"command": " ".join(diff_cmd), "status": "ok"})
            artifacts["reviewer_diff_report"] = str(reviewer_diff_json)
        else:
            commands_executed.append({"command": " ".join(diff_cmd), "status": "fail", "error": output})
    else:
        commands_skipped.append({"command": "build_reviewer_diff_report.py", "reason": "no baseline provided"})

    # Step 5: Experiment manifest
    if build_experiment_manifest:
        manifest_json = out_root / "qlib_experiment_manifest.json"
        manifest_md = out_root / "qlib_experiment_manifest.md"
        manifest_cmd = [
            sys.executable,
            "cajas/scripts/build_qlib_experiment_manifest.py",
            "--manifest-name",
            bundle_name,
            "--out-json",
            str(manifest_json),
            "--out-md",
            str(manifest_md),
        ]
        success, output = run_command(manifest_cmd, "experiment manifest")
        if success:
            commands_executed.append({"command": " ".join(manifest_cmd), "status": "ok"})
            artifacts["experiment_manifest"] = str(manifest_json)
        else:
            commands_executed.append({"command": " ".join(manifest_cmd), "status": "fail", "error": output})
    else:
        commands_skipped.append({"command": "build_qlib_experiment_manifest.py", "reason": "not requested"})

    # Step 6: Data source audit
    audit_json = out_root / "data_source_audit.json"
    audit_md = out_root / "data_source_audit.md"
    if run_data_source_audit and data_root:
        audit_cmd = [
            sys.executable,
            "cajas/scripts/audit_data_sources.py",
            "--project-root",
            "cajas",
            "--data-root",
            str(data_root),
            "--out-json",
            str(audit_json),
            "--out-md",
            str(audit_md),
        ]
        success, output = run_command(audit_cmd, "data source audit")
        if success:
            commands_executed.append({"command": " ".join(audit_cmd), "status": "ok"})
            artifacts["data_source_audit"] = str(audit_json)
        else:
            commands_executed.append({"command": " ".join(audit_cmd), "status": "fail", "error": output})
    elif skip_data_source_audit:
        commands_skipped.append({"command": "audit_data_sources.py", "reason": "skip requested"})
    else:
        commands_skipped.append({"command": "audit_data_sources.py", "reason": "not requested"})

    # Step 7: Build delivery packet
    packet_dir = out_root / "delivery_packet"
    packet_cmd = [
        sys.executable,
        "cajas/scripts/build_validation_delivery_packet.py",
        "--packet-name",
        bundle_name,
        "--smoke-root",
        str(smoke_root),
        "--out-dir",
        str(packet_dir),
    ]
    if (smoke_root / "contract" / "dataset_quality_contract_report.json").exists():
        packet_cmd.extend(["--contract-report", str(smoke_root / "contract" / "dataset_quality_contract_report.json")])
    if (smoke_root / "contract" / "dataset_quality_trend_snapshot.json").exists():
        packet_cmd.extend(["--trend-snapshot", str(smoke_root / "contract" / "dataset_quality_trend_snapshot.json")])
    if runtime_budget_json.exists():
        packet_cmd.extend(["--runtime-budget-report", str(runtime_budget_json)])
    if reviewer_diff_json.exists():
        packet_cmd.extend(["--reviewer-diff-report", str(reviewer_diff_json)])
    if artifacts.get("experiment_manifest"):
        packet_cmd.extend(["--experiment-manifest", artifacts["experiment_manifest"]])
    if audit_json.exists():
        packet_cmd.extend(["--data-source-audit", str(audit_json)])
    if copy_artifacts:
        packet_cmd.append("--copy-artifacts")

    success, output = run_command(packet_cmd, "delivery packet")
    if success:
        commands_executed.append({"command": " ".join(packet_cmd), "status": "ok"})
        artifacts["delivery_packet"] = str(packet_dir)
    else:
        commands_executed.append({"command": " ".join(packet_cmd), "status": "fail", "error": output})

    # Build bundle manifest
    bundle_manifest = {
        "bundle_name": bundle_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_branch": git_info["branch"],
        "git_commit": git_info["commit"],
        "commands_executed": commands_executed,
        "commands_skipped": commands_skipped,
        "artifacts": artifacts,
        "warnings": warnings,
    }

    # Read delivery packet status if available
    packet_manifest_path = packet_dir / "packet_manifest.json"
    if packet_manifest_path.exists():
        with open(packet_manifest_path, encoding="utf-8") as f:
            packet_manifest = json.load(f)
            bundle_manifest["delivery_packet_status"] = packet_manifest.get("overall_status")
            bundle_manifest["runtime_budget_status"] = packet_manifest.get("runtime_budget_status")
            bundle_manifest["reviewer_diff_status"] = packet_manifest.get("reviewer_diff_status")
    if runtime_budget_report_data is None:
        runtime_budget_report_data = _load_json_if_exists(runtime_budget_json)
    if runtime_budget_report_data:
        timing_consistency = runtime_budget_report_data.get("timing_consistency")
        if isinstance(timing_consistency, dict):
            bundle_manifest["timing_consistency"] = {
                "status": timing_consistency.get("status", "warn"),
                "issues": timing_consistency.get("issues", []),
                "timing_path": timing_consistency.get("timing_path"),
            }
            if timing_consistency.get("status") == "warn":
                warnings.append("timing consistency warnings detected")
            if timing_consistency.get("status") == "fail":
                warnings.append("timing consistency failures detected")
                if not warn_only:
                    raise RuntimeError("timing consistency check failed")

    # Step 8: Optional history update
    history_metadata: dict[str, Any] = {"requested": update_history}
    stable_history: dict[str, Any] = {
        "enabled": update_history,
        "history_jsonl": str(history_jsonl) if history_jsonl else None,
        "summary_json": None,
        "summary_md": None,
        "status": "not_requested",
        "snapshot_count": 0,
        "latest_bundle_status": None,
        "runtime_budget_status": bundle_manifest.get("runtime_budget_status"),
        "regression_count": 0,
        "delta_from_previous": {},
        "latest_snapshot": {},
        "regressions": [],
        "reviewer_recommendation": None,
    }
    history_failed = False
    if update_history:
        if not history_jsonl:
            history_failed = True
            history_metadata.update(
                {
                    "status": "error",
                    "error": "history_jsonl is required when --update-history is set",
                }
            )
            stable_history["status"] = HISTORY_STATUS_FAIL
            stable_history["note"] = "History update failed because required history path was missing."
        else:
            try:
                previous_snapshots = read_snapshots(history_jsonl)
                previous_snapshot = previous_snapshots[-1] if previous_snapshots else None

                current_snapshot = create_snapshot_from_bundle(
                    bundle_root=out_root,
                    branch=git_info["branch"],
                    commit=git_info["commit"],
                    created_at=bundle_manifest["created_at"],
                )
                append_snapshot(history_jsonl, current_snapshot)
                snapshots = read_snapshots(history_jsonl)

                history_summary_json = history_jsonl.parent / "review_bundle_history_summary.json"
                history_summary_md = history_jsonl.parent / "review_bundle_history_summary.md"

                delta = compute_delta(current_snapshot, previous_snapshot) if previous_snapshot else {}
                regressions = detect_regressions(current_snapshot, previous_snapshot) if previous_snapshot else []
                recommendation = (
                    "review_regressions"
                    if regressions
                    else "stable_or_improved"
                    if current_snapshot.runtime_budget_status == "pass"
                    and current_snapshot.delivery_packet_status in ("pass", "warn")
                    else "review_warnings"
                )

                history_summary = {
                    "snapshot_count": len(snapshots),
                    "latest_snapshot": {
                        "created_at": current_snapshot.created_at,
                        "branch": current_snapshot.branch,
                        "commit": current_snapshot.commit,
                        "delivery_packet_status": current_snapshot.delivery_packet_status,
                        "runtime_budget_status": current_snapshot.runtime_budget_status,
                        "fast_total_seconds": current_snapshot.fast_total_seconds,
                        "pytest_fast_seconds": current_snapshot.pytest_fast_seconds,
                    },
                    "latest_bundle_status": current_snapshot.delivery_packet_status,
                    "delta_from_previous": delta,
                    "regressions": regressions,
                    "regression_count": len(regressions),
                    "reviewer_recommendation": recommendation,
                }
                history_summary_json.parent.mkdir(parents=True, exist_ok=True)
                with open(history_summary_json, "w", encoding="utf-8") as f:
                    json.dump(history_summary, f, indent=2)
                with open(history_summary_md, "w", encoding="utf-8") as f:
                    f.write(generate_history_summary_markdown(snapshots, last_n=history_last_n))

                history_status = infer_history_status(recommendation, regressions, history_error=False)
                legacy_status = "not_requested" if history_status == "not_requested" else "error" if history_status == "fail" else history_status
                history_metadata.update(
                    {
                        "status": legacy_status,
                        "history_jsonl": str(history_jsonl),
                        "summary_json": str(history_summary_json),
                        "summary_md": str(history_summary_md),
                        "latest_bundle_status": current_snapshot.delivery_packet_status,
                        "latest_snapshot": history_summary["latest_snapshot"],
                        "delta_from_previous": delta,
                        "regressions": regressions,
                        "regression_count": len(regressions),
                        "reviewer_recommendation": recommendation,
                    }
                )
                stable_history.update(
                    {
                        "history_jsonl": str(history_jsonl),
                        "summary_json": str(history_summary_json),
                        "summary_md": str(history_summary_md),
                        "status": history_status,
                        "snapshot_count": len(snapshots),
                        "latest_bundle_status": current_snapshot.delivery_packet_status,
                        "runtime_budget_status": current_snapshot.runtime_budget_status,
                        "regression_count": len(regressions),
                        "delta_from_previous": delta,
                        "latest_snapshot": history_summary["latest_snapshot"],
                        "regressions": regressions,
                        "reviewer_recommendation": recommendation,
                    }
                )
                artifacts["history_jsonl"] = str(history_jsonl)
                artifacts["history_summary_json"] = str(history_summary_json)
                artifacts["history_summary_md"] = str(history_summary_md)
            except Exception as exc:
                history_failed = True
                history_metadata.update({"status": "error", "error": str(exc)})
                stable_history["status"] = HISTORY_STATUS_FAIL
                stable_history["note"] = f"History update failed: {exc}"
    else:
        history_metadata["status"] = "not_requested"
        stable_history = {
            "enabled": False,
            "status": "not_requested",
            "note": "History update was not requested for this bundle.",
        }
    bundle_manifest["history"] = stable_history
    # Phase 2006-2065: default manifest is canonical-only. Alias is explicit fallback.
    should_emit_history_alias = include_history_update_alias and not omit_history_update_alias
    if should_emit_history_alias:
        bundle_manifest["history_update"] = {
            "deprecated": True,
            "use": "history",
            "deprecation_stage": "compatibility_alias",
            "removal_target_phase": "future",
            "consumer_action": "Read manifest.history instead.",
            **history_metadata,
        }
    compatibility_issues = validate_history_metadata_compatibility(bundle_manifest)
    if compatibility_issues:
        bundle_manifest["history_compatibility_issues"] = compatibility_issues

    # Step 9: Optional manifest compatibility report
    compat_meta: dict[str, Any]
    if check_manifest_compatibility:
        compat_json = manifest_compatibility_out_json or (out_root / "manifest_compatibility_report.json")
        compat_md = manifest_compatibility_out_md or (out_root / "manifest_compatibility_report.md")
        report = build_compatibility_report(
            bundle_manifest,
            str(out_root / "review_bundle_manifest.json"),
        )
        compat_json.parent.mkdir(parents=True, exist_ok=True)
        compat_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        compat_md.parent.mkdir(parents=True, exist_ok=True)
        compat_md.write_text(render_compatibility_markdown(report), encoding="utf-8")
        artifacts["manifest_compatibility_report_json"] = str(compat_json)
        artifacts["manifest_compatibility_report_md"] = str(compat_md)
        compat_meta = {
            "enabled": True,
            "status": report["status"],
            "error_count": report["error_count"],
            "warning_count": report["warning_count"],
            "info_count": report["info_count"],
            "canonical_source": report["history_source"],
            "deprecated_alias_present": "yes" if isinstance(bundle_manifest.get("history_update"), dict) else "no",
            "report_json": str(compat_json),
            "report_md": str(compat_md),
        }
        if report["status"] == "warn":
            warnings.append("manifest compatibility warnings detected")
        if report["status"] == "fail":
            warnings.append("manifest compatibility errors detected")
        if report["status"] == "fail" and not warn_only:
            raise RuntimeError("manifest compatibility check failed")
    else:
        compat_meta = {
            "enabled": False,
            "status": "not_requested",
            "note": "Manifest compatibility check was not requested.",
        }
    bundle_manifest["manifest_compatibility"] = compat_meta
    if history_failed:
        msg = f"history update failed: {history_metadata.get('error', 'unknown error')}"
        if warn_only:
            warnings.append(msg)
        else:
            raise RuntimeError(msg)

    # Build gate summary and final status artifacts
    gates: list[ValidationGate] = []
    smoke_status = "pass" if any(
        c["status"] == "ok" and "run_dataset_quality_smoke.py" in c["command"] for c in commands_executed
    ) else "fail"
    gates.append(
        ValidationGate(
            "dataset_quality_smoke",
            True,
            smoke_status,
            "smoke_ok" if smoke_status == "pass" else "smoke_failed",
            "none" if smoke_status == "pass" else "rerun_validation",
            "dataset quality smoke run",
            None,
            None,
        )
    )

    if runtime_budget_report_data:
        gates.append(
            ValidationGate(
                "runtime_budget",
                True,
                runtime_budget_report_data.get("budget_status", runtime_budget_report_data.get("overall_status", "warn")),
                "within_budget" if runtime_budget_report_data.get("budget_status", runtime_budget_report_data.get("overall_status", "warn")) == "pass" else "budget_warning_or_fail",
                "none" if runtime_budget_report_data.get("budget_status", runtime_budget_report_data.get("overall_status", "warn")) == "pass" else "review",
                "runtime budget report",
                str(runtime_budget_json),
                str(runtime_budget_md),
            )
        )
        timing = runtime_budget_report_data.get("timing_consistency", {})
        gates.append(
            ValidationGate(
                "timing_consistency",
                True if ci else False,
                timing.get("status", "warn") if isinstance(timing, dict) else "warn",
                "timing_consistent" if isinstance(timing, dict) and timing.get("status") == "pass" else "timing_consistency_issue",
                "none" if isinstance(timing, dict) and timing.get("status") == "pass" else "rerun_validation",
                "timing freshness/consistency",
                str(runtime_budget_json),
                str(runtime_budget_md),
            )
        )
    else:
        gates.append(
            ValidationGate(
                "runtime_budget",
                True,
                "not_run",
                "not_requested_or_missing_input",
                "required_input",
                "runtime budget report not available",
                None,
                None,
            )
        )

    if check_manifest_compatibility:
        gates.append(
            ValidationGate(
                "manifest_compatibility",
                True if ci else False,
                compat_meta.get("status", "warn"),
                "manifest_compatible" if compat_meta.get("status") == "pass" else "manifest_compatibility_issue",
                "none" if compat_meta.get("status") == "pass" else "review",
                "manifest compatibility report",
                compat_meta.get("report_json"),
                compat_meta.get("report_md"),
            )
        )
    else:
        gates.append(
            ValidationGate(
                "manifest_compatibility",
                False,
                "not_run",
                "not_requested",
                "none",
                "compatibility check not requested",
                None,
                None,
            )
        )

    history_status = stable_history.get("status", "not_run") if isinstance(stable_history, dict) else "not_run"
    gates.append(
        ValidationGate(
            "history",
            True if (ci and update_history) else False,
            history_status,
            "history_ok" if history_status == "pass" else "history_warning_or_fail" if history_status in {"warn", "fail"} else "not_requested",
            "none" if history_status == "pass" else "review" if history_status == "warn" else "fix" if history_status == "fail" else "none",
            "review bundle history update",
            stable_history.get("summary_json") if isinstance(stable_history, dict) else None,
            stable_history.get("summary_md") if isinstance(stable_history, dict) else None,
        )
    )

    packet_status = bundle_manifest.get("delivery_packet_status", "not_run")
    delivery_required = ci and ci_profile in {"ci", "strict"}
    gates.append(
        ValidationGate(
            "delivery_packet",
            delivery_required,
            packet_status,
            "delivery_packet_ok" if packet_status == "pass" else "delivery_packet_warn" if packet_status == "warn" else "delivery_packet_failed_or_missing",
            "none" if packet_status == "pass" else "review" if packet_status == "warn" else "fix",
            "validation delivery packet",
            str(packet_dir / "packet_manifest.json"),
            None,
        )
    )
    reviewer_diff_status = bundle_manifest.get("reviewer_diff_status", "not_run")
    gates.append(
        ValidationGate(
            "reviewer_diff",
            False,
            reviewer_diff_status,
            "reviewer_diff_ok" if reviewer_diff_status == "pass" else "reviewer_diff_warn_or_fail" if reviewer_diff_status in {"warn", "fail"} else "not_run",
            "none" if reviewer_diff_status in {"pass", "not_run"} else "review",
            "reviewer diff report",
            str(reviewer_diff_json) if reviewer_diff_json.exists() else None,
            str(reviewer_diff_md) if reviewer_diff_md.exists() else None,
        )
    )

    if artifacts.get("data_source_audit"):
        audit_data = _load_json_if_exists(artifacts.get("data_source_audit"))
        read_count = _extract_read_csv_count(audit_data)
        summary = f"data-source audit completed (read_csv_count={read_count})" if read_count is not None else "data-source audit completed"
        gates.append(
            ValidationGate(
                "data_source_audit",
                False,
                "pass",
                "audit_ok",
                "none",
                summary,
                artifacts.get("data_source_audit"),
                str(audit_md) if audit_md.exists() else None,
            )
        )
    elif run_data_source_audit:
        gates.append(
            ValidationGate(
                "data_source_audit",
                True if ci else False,
                "fail",
                "audit_requested_but_missing",
                "fix",
                "data-source audit requested but not produced",
                None,
                None,
            )
        )
    else:
        gates.append(
            ValidationGate(
                "data_source_audit",
                False,
                "not_run",
                "not_requested",
                "none",
                "data-source audit not requested",
                None,
                None,
            )
        )

    final_status_payload = build_final_status_payload(
        gates=gates,
        bundle_name=bundle_name,
        created_at=bundle_manifest["created_at"],
        git_branch=git_info["branch"],
        git_commit=git_info["commit"],
        profile=ci_profile if ci else "local",
        profile_config=profile_config,
        profile_policy=profile_policy,
        command=" ".join(sys.argv),
    )
    final_status_json = out_root / "final_status.json"
    final_status_md = out_root / "final_status.md"
    final_status_json.write_text(json.dumps(final_status_payload, indent=2), encoding="utf-8")
    final_status_md.write_text(render_final_status_markdown(final_status_payload), encoding="utf-8")
    artifacts["final_status_json"] = str(final_status_json)
    artifacts["final_status_md"] = str(final_status_md)
    bundle_manifest["final_status"] = {
        "schema_version": final_status_payload["schema_version"],
        "run_id": final_status_payload["run_id"],
        "profile": final_status_payload["profile"],
        "overall_status": final_status_payload["overall_status"],
        "overall_reason_code": final_status_payload["overall_reason_code"],
        "overall_reason": final_status_payload["overall_reason"],
        "reviewer_next_action": final_status_payload["reviewer_next_action"],
        "primary_artifact": final_status_payload["primary_artifact"],
        "json": str(final_status_json),
        "md": str(final_status_md),
    }

    # Generate Profile Matrix
    try:
        from cajas.reports.validation_profile_matrix import (
            build_profile_matrix,
            render_profile_matrix_markdown,
        )
        matrix_payload = build_profile_matrix(
            base_payload=final_status_payload,
            profile_config=_load_json_if_exists(ci_profile_config) if ci_profile_config else None,
        )
        matrix_json = out_root / "profile_matrix.json"
        matrix_md = out_root / "profile_matrix.md"
        matrix_json.write_text(json.dumps(matrix_payload, indent=2), encoding="utf-8")
        matrix_md.write_text(render_profile_matrix_markdown(matrix_payload), encoding="utf-8")
        artifacts["profile_matrix_json"] = str(matrix_json)
        artifacts["profile_matrix_md"] = str(matrix_md)
        bundle_manifest["profile_matrix"] = {
            "json": str(matrix_json),
            "md": str(matrix_md),
        }
    except Exception as e:
        logger.warning(f"Failed to generate profile matrix: {e}")

    # Write bundle manifest
    manifest_path = out_root / "review_bundle_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(bundle_manifest, f, indent=2)

    # Write bundle index
    index_lines = [
        f"# Validation Review Bundle: {bundle_name}",
        "",
        "**Important**: This bundle summarizes offline Qlib research infrastructure validation artifacts only.",
        "",
        f"Overall status: `{final_status_payload['overall_status']}`",
        f"Profile: `{final_status_payload.get('profile')}`",
        (
            "Optional warnings are visible but do not escalate overall status."
            if not final_status_payload.get("profile_policy", {}).get("optional_warn_affects_status", True)
            else "Optional warnings escalate overall status."
        ),
        "",
        "## Escalation Summary",
        "",
    ]
    escalated = [
        g for g in final_status_payload.get("gates", []) if g.get("status") in {"warn", "fail", "not_run"} and g.get("escalated")
    ]
    non_escalated_warn = [
        g for g in final_status_payload.get("gates", []) if g.get("status") == "warn" and not g.get("escalated")
    ]
    index_lines.extend(
        [
            f"- escalated_gates: `{len(escalated)}`",
            f"- non_escalated_warning_gates: `{len(non_escalated_warn)}`",
            f"- primary_artifact: `{final_status_payload.get('primary_artifact')}`",
            f"- reviewer_next_action: `{final_status_payload.get('reviewer_next_action')}`",
            "",
        ]
    )

    if "profile_matrix" in locals() and "matrix_payload" in locals():
        index_lines.extend([
            "## Profile Matrix Summary",
            "",
            "| Profile | Overall | Escalated warnings | Blocking gates | Next action |",
            "|---|---|---:|---:|---|",
        ])
        
        profiles = matrix_payload.get("profiles", {})
        for prof in ["local", "ci", "strict"]:
            if prof in profiles:
                p = profiles[prof]
                index_lines.append(
                    f"| {prof} | {p['overall_status']} | {p['escalated_count']} | {p['blocking_count']} | {p['next_action']} |"
                )
        index_lines.extend([
            "",
            f"See full matrix report: `{artifacts.get('profile_matrix_md', 'profile_matrix.md')}`",
            "",
        ])

    index_lines.extend([
        "## CI Gate Summary",
            "",
            "| Gate | Required | Status | Escalated | Profile Effect | Reason | Action | Artifact |",
            "|---|---:|---|---:|---|---|---|---|",
        ]
    )

    for gate in final_status_payload["gates"]:
        artifact = gate.get("artifact_json") or gate.get("artifact_md") or ""
        index_lines.append(
            f"| {gate.get('name')} | {'yes' if gate.get('required') else 'no'} | {gate.get('status')} | {'yes' if gate.get('escalated') else 'no'} | {gate.get('profile_effect', '')} | {gate.get('reason_code', '')} | {gate.get('action', '')} | {artifact} |"
        )

    index_lines.extend([
        "",
        "## Bundle Summary",
        "",
        f"- bundle_name: `{bundle_name}`",
        f"- created_at: `{bundle_manifest['created_at']}`",
        f"- git_branch: `{git_info['branch']}`",
        f"- git_commit: `{git_info['commit']}`",
        "",
        "## Commands Executed",
        "",
    ])

    for cmd_info in commands_executed:
        status_icon = "✅" if cmd_info["status"] == "ok" else "❌"
        index_lines.append(f"- {status_icon} `{cmd_info['command']}`")
        if cmd_info.get("error"):
            index_lines.append(f"  - Error: {cmd_info['error'][:100]}")

    index_lines.extend([
        "",
        "## Commands Skipped",
        "",
    ])

    for cmd_info in commands_skipped:
        index_lines.append(f"- ⏭️ `{cmd_info['command']}` - {cmd_info['reason']}")

    index_lines.extend([
        "",
        "## Generated Artifacts",
        "",
    ])

    for artifact_name, artifact_path in artifacts.items():
        index_lines.append(f"- {artifact_name}: `{artifact_path}`")

    index_lines.extend([
        "",
        "## Status Summary",
        "",
    ])

    if "delivery_packet_status" in bundle_manifest:
        index_lines.append(f"- delivery_packet_status: `{bundle_manifest['delivery_packet_status']}`")
    if "runtime_budget_status" in bundle_manifest:
        index_lines.append(f"- runtime_budget_status: `{bundle_manifest['runtime_budget_status']}`")
    if "reviewer_diff_status" in bundle_manifest:
        index_lines.append(f"- reviewer_diff_status: `{bundle_manifest['reviewer_diff_status']}`")

    index_lines.extend(["", "## History Summary", ""])
    history_section = normalize_history_metadata(bundle_manifest)
    if history_section.get("enabled") and history_section.get("status") != "not_requested":
        if history_section.get("source") == "history_update":
            index_lines.append("- Compatibility warning: canonical history field missing; fallback to deprecated history_update alias.")
        index_lines.append(f"- History status: `{history_section.get('status', HISTORY_STATUS_PASS)}`")
        index_lines.append(f"- Snapshot count: `{history_section.get('snapshot_count', 0)}`")
        index_lines.append(f"- Latest bundle status: `{history_section.get('latest_bundle_status', 'N/A')}`")
        index_lines.append(f"- Runtime budget status: `{history_section.get('runtime_budget_status', bundle_manifest.get('runtime_budget_status', 'N/A'))}`")
        index_lines.append(f"- Regression notes: `{history_section.get('regression_count', 0)} regressions`")
        index_lines.append(f"- History JSONL: `{history_section.get('history_jsonl')}`")
        index_lines.append(f"- History summary: `{history_section.get('summary_md')}`")
        index_lines.append("")
        index_lines.append("### History Delta")
        index_lines.append("")
        delta = history_section.get("delta_from_previous", {})
        if not delta:
            index_lines.append("No previous snapshot available.")
        else:
            fast_delta = delta.get("fast_total_delta")
            pytest_delta = delta.get("pytest_fast_delta")
            latest = history_section.get("latest_snapshot") or {}
            latest_fast = latest.get("fast_total_seconds")
            latest_pytest = latest.get("pytest_fast_seconds")
            prev_fast = latest_fast - fast_delta if latest_fast is not None and fast_delta is not None else None
            prev_pytest = latest_pytest - pytest_delta if latest_pytest is not None and pytest_delta is not None else None
            index_lines.extend([
                "| Metric | Previous | Current | Delta |",
                "|---|---:|---:|---:|",
                f"| fast_total | {format_seconds(prev_fast)} | {format_seconds(latest_fast)} | {format_seconds(fast_delta)} |",
                f"| pytest_fast | {format_seconds(prev_pytest)} | {format_seconds(latest_pytest)} | {format_seconds(pytest_delta)} |",
            ])
        index_lines.append("")
        if history_section.get("latest_bundle_status") is not None:
            index_lines.append(f"- Latest bundle status (raw): `{history_section['latest_bundle_status']}`")
        if history_section.get("regressions"):
            index_lines.append("- Regression details:")
            for regression in history_section["regressions"]:
                index_lines.append(f"  - {regression}")
        if history_section.get("reviewer_recommendation"):
            index_lines.append(f"- Reviewer recommendation: `{history_section['reviewer_recommendation']}`")
    elif history_section.get("status") == HISTORY_STATUS_FAIL:
        index_lines.append(f"- History status: `{HISTORY_STATUS_FAIL}`")
        index_lines.append(f"- History update error: `{history_section.get('note', 'unknown error')}`")
    else:
        index_lines.append(history_section.get("note", "History update was not requested for this bundle."))

    index_lines.extend(["", "## Manifest Compatibility", ""])
    manifest_compat = bundle_manifest.get("manifest_compatibility", {})
    if manifest_compat.get("enabled"):
        index_lines.append(f"- Status: `{manifest_compat.get('status', 'warn')}`")
        index_lines.append(f"- Canonical source: `{manifest_compat.get('canonical_source', 'unknown')}`")
        index_lines.append(f"- Deprecated alias present: `{manifest_compat.get('deprecated_alias_present', 'unknown')}`")
        index_lines.append(f"- Errors: `{manifest_compat.get('error_count', 0)}`")
        index_lines.append(f"- Warnings: `{manifest_compat.get('warning_count', 0)}`")
        index_lines.append(f"- Info: `{manifest_compat.get('info_count', 0)}`")
        index_lines.append(f"- Report JSON: `{manifest_compat.get('report_json')}`")
        index_lines.append(f"- Report Markdown: `{manifest_compat.get('report_md')}`")
    else:
        index_lines.append("Manifest compatibility check was not requested for this bundle.")

    index_lines.extend(["", "## Timing Consistency", ""])
    timing_consistency = bundle_manifest.get("timing_consistency", {})
    if timing_consistency:
        index_lines.append(f"- Status: `{timing_consistency.get('status', 'warn')}`")
        if artifacts.get("fast_timing_json"):
            index_lines.append(f"- Timing JSON: `{artifacts.get('fast_timing_json')}`")
        issues = timing_consistency.get("issues", [])
        if issues:
            index_lines.append("- Issues:")
            for issue in issues:
                index_lines.append(
                    f"  - [{issue.get('severity', 'warning')}] {issue.get('code', 'unknown')}: {issue.get('message', '')}"
                )
        else:
            index_lines.append("- Issues: none")
    else:
        index_lines.append("Timing consistency data not available.")

    index_lines.extend([
        "",
        "## Reviewer Next Action",
        "",
    ])

    if bundle_manifest.get("delivery_packet_status") == "pass":
        index_lines.append("**Ready for merge**: All critical validations passed.")
    elif bundle_manifest.get("delivery_packet_status") == "warn":
        index_lines.append("**Review warnings**: Some optional artifacts missing or warnings detected.")
    else:
        index_lines.append("**Action required**: Review failed validations before merge.")

    index_lines.append("")

    index_path = out_root / "review_bundle_index.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines))

    return bundle_manifest


def _flag_present(argv: list[str], flag: str) -> bool:
    return flag in argv


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Build validation review bundle")
    parser.add_argument("--bundle-name", required=True, help="Bundle name")
    parser.add_argument("--out-root", type=Path, required=True, help="Output root directory")
    parser.add_argument("--smoke-root", type=Path, required=True, help="Smoke test output root")
    parser.add_argument("--fast-timing-json", type=Path, help="Fast validation timing JSON")
    parser.add_argument("--budgets", type=Path, help="Runtime budgets JSON")
    parser.add_argument("--baseline-root", type=Path, help="Baseline root for reviewer diff")
    parser.add_argument("--create-baseline-from-current", action="store_true", help="Create baseline from current smoke")
    parser.add_argument("--run-fast-validation", action="store_true", help="Run fast validation")
    parser.add_argument("--skip-fast-validation", action="store_true", help="Skip fast validation")
    parser.add_argument("--run-data-source-audit", action="store_true", help="Run data source audit")
    parser.add_argument("--skip-data-source-audit", action="store_true", help="Skip data source audit")
    parser.add_argument("--data-root", type=Path, help="Data root for audit")
    parser.add_argument("--build-experiment-manifest", action="store_true", help="Build experiment manifest")
    parser.add_argument("--copy-artifacts", action="store_true", help="Copy artifacts to delivery packet")
    parser.add_argument("--update-history", action="store_true", help="Append this bundle to history and write summaries")
    parser.add_argument(
        "--history-jsonl",
        type=Path,
        default=Path("tmp/validation-review-bundle/history/review_bundle_history.jsonl"),
        help="History JSONL path used with --update-history",
    )
    parser.add_argument("--history-last-n", type=int, default=10, help="Number of snapshots in history markdown summary")
    parser.add_argument(
        "--check-manifest-compatibility",
        action="store_true",
        help="Generate manifest compatibility report using canonical history guard checks",
    )
    parser.add_argument(
        "--manifest-compatibility-out-json",
        type=Path,
        help="Output JSON path for manifest compatibility report",
    )
    parser.add_argument(
        "--manifest-compatibility-out-md",
        type=Path,
        help="Output markdown path for manifest compatibility report",
    )
    parser.add_argument("--warn-only", action="store_true", help="Don't fail on warnings")
    parser.add_argument("--ci", action="store_true", help="Enable CI-friendly standard gating mode")
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit non-zero when final overall status is warn")
    parser.add_argument("--skip-history", action="store_true", help="Skip history update in CI mode")
    parser.add_argument("--skip-manifest-compatibility", action="store_true", help="Skip manifest compatibility in CI mode")
    parser.add_argument("--skip-runtime-budget", action="store_true", help="Skip runtime budget check in CI mode")
    parser.add_argument("--max-timing-age-seconds", type=int, default=3600, help="Maximum accepted timing age for runtime budget checks")
    parser.add_argument("--ci-profile", choices=["local", "ci", "strict"], default="ci", help="CI gate aggregation profile")
    parser.add_argument(
        "--ci-profile-config",
        type=Path,
        help="Optional external CI profile config JSON (profiles/local|ci|strict)",
    )
    parser.add_argument(
        "--preset",
        choices=["local_review", "ci_required", "strict_release"],
        help="Apply automation preset to set flags automatically",
    )
    parser.add_argument(
        "--preset-config",
        type=Path,
        default=Path("cajas/data_examples/validation_review_bundle_presets.json"),
        help="Path to presets config JSON",
    )
    parser.add_argument(
        "--include-history-update-alias",
        action="store_true",
        help="Include deprecated history_update alias for compatibility fallback.",
    )
    parser.add_argument(
        "--omit-history-update-alias",
        action="store_true",
        help="Compatibility flag retained during transition; default already omits history_update alias.",
    )

    args = parser.parse_args(argv)

    if args.preset:
        try:
            presets_data = json.loads(args.preset_config.read_text(encoding="utf-8"))
            preset_cfg = presets_data.get("presets", {}).get(args.preset)
            if preset_cfg:
                if "ci_profile" in preset_cfg and not _flag_present(raw_argv, "--ci-profile"):
                    args.ci_profile = preset_cfg["ci_profile"]
                if preset_cfg.get("warn_only") and not _flag_present(raw_argv, "--warn-only"):
                    args.warn_only = True
                if preset_cfg.get("fail_on_warn") and not _flag_present(raw_argv, "--fail-on-warn"):
                    args.fail_on_warn = True
                if preset_cfg.get("run_fast_validation") and not _flag_present(raw_argv, "--run-fast-validation"):
                    args.run_fast_validation = True
                if preset_cfg.get("update_history") and not _flag_present(raw_argv, "--update-history"):
                    args.update_history = True
                if preset_cfg.get("check_manifest_compatibility") and not _flag_present(raw_argv, "--check-manifest-compatibility"):
                    args.check_manifest_compatibility = True
        except Exception as e:
            logger.warning(f"Failed to load preset config: {e}")

    try:
        bundle_manifest = build_review_bundle(
            bundle_name=args.bundle_name,
            out_root=args.out_root,
            smoke_root=args.smoke_root,
            fast_timing_json=args.fast_timing_json,
            budgets=args.budgets,
            baseline_root=args.baseline_root,
            create_baseline_from_current=args.create_baseline_from_current,
            run_fast_validation=args.run_fast_validation,
            skip_fast_validation=args.skip_fast_validation,
            run_data_source_audit=args.run_data_source_audit,
            skip_data_source_audit=args.skip_data_source_audit,
            data_root=args.data_root,
            build_experiment_manifest=args.build_experiment_manifest,
            copy_artifacts=args.copy_artifacts,
            update_history=args.update_history,
            history_jsonl=args.history_jsonl,
            history_last_n=args.history_last_n,
            check_manifest_compatibility=args.check_manifest_compatibility,
            manifest_compatibility_out_json=args.manifest_compatibility_out_json,
            manifest_compatibility_out_md=args.manifest_compatibility_out_md,
            warn_only=args.warn_only,
            ci=args.ci,
            fail_on_warn=args.fail_on_warn,
            skip_history=args.skip_history,
            skip_manifest_compatibility=args.skip_manifest_compatibility,
            skip_runtime_budget=args.skip_runtime_budget,
            max_timing_age_seconds=args.max_timing_age_seconds,
            ci_profile=args.ci_profile,
            ci_profile_config=args.ci_profile_config,
            omit_history_update_alias=args.omit_history_update_alias,
            include_history_update_alias=args.include_history_update_alias,
        )

        print(json.dumps({"status": "ok", "bundle_manifest": str(args.out_root / "review_bundle_manifest.json")}))

        # Check if any commands failed
        failed_commands = [cmd for cmd in bundle_manifest["commands_executed"] if cmd["status"] == "fail"]
        if failed_commands and not args.warn_only:
            return 1
        overall = (bundle_manifest.get("final_status") or {}).get("overall_status")
        if overall == "fail" and not args.warn_only:
            return 1
        if overall == "warn" and args.fail_on_warn:
            return 1

        return 0

    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
