#!/usr/bin/env python3
"""Safe tmp archive executor. Defaults to dry-run."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def _load_plan(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError("plan_json_missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("plan_json_invalid") from exc
    if payload.get("report_status") != "tmp_cleanup_plan_ready":
        raise ValueError("plan_not_ready")
    return payload


def _is_manual_like(rel: str) -> bool:
    n = Path(rel).name.lower()
    return ("completed" in n) or ("events.jsonl" in n) or ("manual" in n)


def _candidate_block_reasons(rel: str, plan: dict[str, Any], tmp_root: Path) -> list[str]:
    reasons: list[str] = []
    p = Path(rel)
    if p.is_absolute():
        reasons.append("absolute_path_not_allowed")
    if ".." in p.parts:
        reasons.append("outside_tmp_path_not_allowed")
    if rel.startswith("archive/"):
        reasons.append("archive_dir_not_candidate")
    if rel in set(plan.get("protected_paths", [])):
        reasons.append("protected_path")
    if rel in set(plan.get("active_artifact_paths", [])):
        reasons.append("active_artifact_path")
    if rel in set(plan.get("manual_artifact_paths", [])) or _is_manual_like(rel):
        reasons.append("manual_artifact_path")
    if rel.endswith("EURUSD_15m_Bid_clean_view.csv") or rel.endswith("EURUSD_15m_Bid_quarantined_rows.csv"):
        reasons.append("source_dataset_path")
    full = tmp_root / rel
    if not str(full.resolve()).startswith(str(tmp_root.resolve())):
        reasons.append("outside_tmp_root")
    return reasons


def _build_manifest(plan: dict[str, Any], mode: str, archive_dir: str, archived: list[str], blocked: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "mode": mode,
        "archive_dir": archive_dir,
        "plan_json": plan.get("_plan_json_path", ""),
        "archived_or_would_archive": archived,
        "blocked_candidates": blocked,
        "dry_run_only": mode == "dry_run",
    }


def execute_archive(plan_json: Path, dry_run: bool, apply: bool, output_json: Path | None = None) -> dict[str, Any]:
    if dry_run and apply:
        raise ValueError("choose_one_mode")
    if not dry_run and not apply:
        dry_run = True

    plan = _load_plan(plan_json)
    plan["_plan_json_path"] = str(plan_json)
    tmp_root = Path(plan.get("tmp_root", "tmp"))
    candidates = [str(x) for x in plan.get("archive_candidates", [])]
    allowed = set(candidates)
    blocked: dict[str, list[str]] = {}
    accepted: list[str] = []
    for rel in candidates:
        reasons = _candidate_block_reasons(rel, plan, tmp_root)
        if rel not in allowed:
            reasons.append("not_in_archive_candidates")
        if reasons:
            blocked[rel] = sorted(set(reasons))
            continue
        accepted.append(rel)

    archive_dir = str(plan.get("archive_dir", "tmp/archive/unknown_market_state_cleanup"))
    if dry_run:
        summary = {
            "mode": "dry_run",
            "plan_json": str(plan_json),
            "archive_dir": archive_dir,
            "archive_candidate_count": len(candidates),
            "would_archive_count": len(accepted),
            "blocked_candidate_count": len(blocked),
            "blocked_reasons": sorted({r for reasons in blocked.values() for r in reasons}),
            "manifest_would_be_written": True,
        }
        if output_json is not None:
            output_json.parent.mkdir(parents=True, exist_ok=True)
            output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    archive_root = Path(archive_dir)
    archive_root.mkdir(parents=True, exist_ok=True)
    archived: list[str] = []
    for rel in accepted:
        src = tmp_root / rel
        if not src.exists():
            blocked[rel] = sorted(set(blocked.get(rel, []) + ["candidate_missing"]))
            continue
        dst = archive_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        archived.append(rel)

    manifest = _build_manifest(plan, "apply", archive_dir, archived, blocked)
    manifest_json = archive_root / "archive_manifest.json"
    manifest_md = archive_root / "archive_manifest.md"
    manifest_json.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest_md.write_text(
        "\n".join(
            [
                "# tmp Archive Manifest",
                "",
                f"- archived_count: `{len(archived)}`",
                f"- blocked_candidate_count: `{len(blocked)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    summary = {
        "mode": "apply",
        "archive_dir": archive_dir,
        "archived_count": len(archived),
        "manifest_json": str(manifest_json),
        "manifest_md": str(manifest_md),
        "blocked_candidate_count": len(blocked),
    }
    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive tmp artifacts safely (dry-run by default)")
    parser.add_argument("--plan-json", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()
    summary = execute_archive(args.plan_json, dry_run=args.dry_run, apply=args.apply, output_json=args.output_json)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
