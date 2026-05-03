#!/usr/bin/env python3
"""Build validation review bundle by orchestrating existing validation CLIs."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"


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
    warn_only: bool,
) -> dict[str, Any]:
    """Build validation review bundle."""
    out_root.mkdir(parents=True, exist_ok=True)

    git_info = get_git_info()
    commands_executed = []
    commands_skipped = []
    artifacts = {}

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
        ]
        success, output = run_command(budget_cmd, "runtime budget check")
        if success:
            commands_executed.append({"command": " ".join(budget_cmd), "status": "ok"})
            artifacts["runtime_budget_report"] = str(runtime_budget_json)
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
    }

    # Read delivery packet status if available
    packet_manifest_path = packet_dir / "packet_manifest.json"
    if packet_manifest_path.exists():
        with open(packet_manifest_path, encoding="utf-8") as f:
            packet_manifest = json.load(f)
            bundle_manifest["delivery_packet_status"] = packet_manifest.get("overall_status")
            bundle_manifest["runtime_budget_status"] = packet_manifest.get("runtime_budget_status")
            bundle_manifest["reviewer_diff_status"] = packet_manifest.get("reviewer_diff_status")

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
        "## Bundle Summary",
        "",
        f"- bundle_name: `{bundle_name}`",
        f"- created_at: `{bundle_manifest['created_at']}`",
        f"- git_branch: `{git_info['branch']}`",
        f"- git_commit: `{git_info['commit']}`",
        "",
        "## Commands Executed",
        "",
    ]

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


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
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
    parser.add_argument("--warn-only", action="store_true", help="Don't fail on warnings")

    args = parser.parse_args(argv)

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
            warn_only=args.warn_only,
        )

        print(json.dumps({"status": "ok", "bundle_manifest": str(args.out_root / "review_bundle_manifest.json")}))

        # Check if any commands failed
        failed_commands = [cmd for cmd in bundle_manifest["commands_executed"] if cmd["status"] == "fail"]
        if failed_commands and not args.warn_only:
            return 1

        return 0

    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
