"""Conservative tmp artifact cleanup planning (dry-run only)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTECTED_INPUT_RELATIVE_PATHS = {
    "eurusd/EURUSD_15m_Bid_clean_view.csv",
    "eurusd/EURUSD_15m_Bid_quarantined_rows.csv",
}

ACTIVE_ARTIFACT_BASENAMES = {
    "EURUSD_15m_market_state_dataset.csv",
    "EURUSD_15m_market_state_dataset.jsonl",
    "validation-eurusd-market-state.json",
    "validation-eurusd-market-state.md",
    "EURUSD_15m_market_state_samples.csv",
    "EURUSD_15m_market_state_samples.jsonl",
    "validation-eurusd-market-state-sample-export.json",
    "validation-eurusd-market-state-sample-export.md",
    "EURUSD_15m_market_state_inspection_packet.csv",
    "EURUSD_15m_market_state_inspection_packet.jsonl",
    "validation-eurusd-market-state-inspection-packet.json",
    "validation-eurusd-market-state-inspection-packet.md",
    "validation-eurusd-market-state-inspection-feedback.json",
    "validation-eurusd-market-state-inspection-feedback.md",
    "EURUSD_15m_micro_pattern_review_packet.csv",
    "EURUSD_15m_micro_pattern_review_packet.jsonl",
    "validation-eurusd-micro-pattern-review-packet.json",
    "validation-eurusd-micro-pattern-review-packet.md",
    "validation-eurusd-micro-pattern-manual-labels.json",
    "validation-eurusd-micro-pattern-manual-labels.md",
    "validation-eurusd-market-state-bundle.json",
    "validation-eurusd-market-state-bundle.md",
    "validation-eurusd-market-state-qlib-adapter-contract.json",
    "validation-eurusd-market-state-dataset-quality.json",
    "validation-eurusd-real-llm-integration-readiness.json",
    "validation-eurusd-real-llm-integration-readiness.md",
    "validation-eurusd-llm-trial-approval.json",
    "validation-eurusd-llm-trial-approval.md",
    "fast_validation_latest.json",
    "validation-tmp-artifact-cleanup-plan.json",
    "validation-tmp-artifact-cleanup-plan.md",
}


def _is_manual_artifact(path: Path) -> bool:
    n = path.name.lower()
    return (
        "completed" in n
        or "events.jsonl" in n
        or "manual" in n
        or "reviewed" in n
    )


def build_tmp_artifact_cleanup_plan(tmp_root: Path) -> dict[str, Any]:
    if not tmp_root.exists():
        return {
            "report_status": "blocked",
            "tmp_root": str(tmp_root),
            "blocking_reasons": ["tmp_root_missing"],
        }

    files = [p for p in tmp_root.rglob("*") if p.is_file()]
    protected_paths: list[str] = []
    active_paths: list[str] = []
    manual_paths: list[str] = []
    archive_candidates: list[str] = []
    total_candidate_size_bytes = 0

    for f in files:
        rel = f.relative_to(tmp_root).as_posix()
        if rel.startswith("archive/"):
            continue
        if rel in PROTECTED_INPUT_RELATIVE_PATHS:
            protected_paths.append(rel)
            continue
        if f.name in ACTIVE_ARTIFACT_BASENAMES:
            active_paths.append(rel)
            continue
        if _is_manual_artifact(f):
            manual_paths.append(rel)
            continue
        archive_candidates.append(rel)
        total_candidate_size_bytes += int(f.stat().st_size)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_dir = f"tmp/archive/{ts}_market_state_cleanup"
    return {
        "report_status": "tmp_cleanup_plan_ready",
        "tmp_root": str(tmp_root),
        "protected_input_count": len(protected_paths),
        "active_artifact_count": len(active_paths),
        "manual_artifact_count": len(manual_paths),
        "archive_candidate_count": len(archive_candidates),
        "delete_candidate_count": 0,
        "total_candidate_size_bytes": int(total_candidate_size_bytes),
        "dry_run_only": True,
        "archive_dir": archive_dir,
        "protected_paths": sorted(protected_paths),
        "active_artifact_paths": sorted(active_paths),
        "manual_artifact_paths": sorted(manual_paths),
        "archive_candidates": sorted(archive_candidates),
        "delete_candidates": [],
        "blocking_reasons": [],
    }


def render_tmp_artifact_cleanup_plan_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# tmp Artifact Cleanup Plan",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- dry_run_only: `{report.get('dry_run_only')}`",
        f"- protected_input_count: `{report.get('protected_input_count')}`",
        f"- active_artifact_count: `{report.get('active_artifact_count')}`",
        f"- manual_artifact_count: `{report.get('manual_artifact_count')}`",
        f"- archive_candidate_count: `{report.get('archive_candidate_count')}`",
        f"- total_candidate_size_bytes: `{report.get('total_candidate_size_bytes')}`",
        "",
        "## Policy",
        "",
        "- never auto-delete protected inputs or manual review artifacts",
        "- archive plan first; no apply execution in this phase",
    ]
    return "\n".join(lines) + "\n"
