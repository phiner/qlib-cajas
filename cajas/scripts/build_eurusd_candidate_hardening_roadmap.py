#!/usr/bin/env python3
"""Build EURUSD candidate hardening roadmap report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_roadmap(audit: dict[str, Any], warning_inventory: dict[str, Any]) -> dict[str, Any]:
    status = audit.get("status", "unknown")
    next_actions = audit.get("next_actions", []) or []
    watch_items = [
        w["warning_id"]
        for w in warning_inventory.get("warnings", [])
        if w.get("classification") in {"acceptable_watch", "future_extension"}
    ]
    return {
        "status": status,
        "architecture_boundaries": {
            "candidate_generation": "causal past-only candidate logic",
            "review_sampling_filters": "future-aware filters allowed only when explicitly tagged as review filter",
            "human_labels": "manual review outcomes only; no auto-trading action",
            "validation_audit_reports": "deterministic status gates and warning inventory",
            "gui_review": "manual reviewer workflow, no automatic accept/promote",
            "future_research_dataset_export": "strict feature/label window separation",
        },
        "extensibility_risks": [
            "future leakage risk across candidate/filter/label boundaries",
            "multi-label timestamp conflicts and primary-type policy drift",
            "session/year/volatility coverage imbalance over small batches",
            "candidate-type specific hard-coded heuristics growing unbounded",
            "reject feedback loop not yet integrated into candidate scoring",
            "scaling to more symbols/timeframes without schema versioning pressure",
            "label schema drift across review iterations",
            "batch reproducibility and seed/manifest lineage risks",
            "active batch vs candidate source version mismatch risk",
        ],
        "recommended_next_phases": [
            "candidate rule registry abstraction",
            "unified candidate metadata schema contract",
            "deterministic sampling manifest with source hashes",
            "reject feedback loop into batch generation",
            "candidate quality dashboard by type/session/volatility",
            "second-batch generation from first-batch review findings",
            "research dataset export with strict anti-leakage windows",
            "time-split train/validation/test protocol design",
            "multi-symbol/timeframe support only after EURUSD flow stabilizes",
        ],
        "must_not_do_yet": [
            "no model training from first 100 reviews",
            "no trading signal/execution workflow",
            "no random train/test split",
            "no reuse of future-aware review filters as candidate logic",
        ],
        "active_watch_items": watch_items,
        "current_next_actions": next_actions,
    }


def render_roadmap_md(payload: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Candidate Hardening Roadmap",
        "",
        f"- status: `{payload.get('status')}`",
        "",
        "## Architecture Boundaries",
        "",
    ]
    for k, v in (payload.get("architecture_boundaries") or {}).items():
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Extensibility Risks", ""])
    for item in payload.get("extensibility_risks", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Phases", ""])
    for item in payload.get("recommended_next_phases", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Must Not Do Yet", ""])
    for item in payload.get("must_not_do_yet", []):
        lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EURUSD candidate hardening roadmap")
    parser.add_argument("--audit-json", type=Path, default=Path("tmp/validation-eurusd-candidate-audit.json"))
    parser.add_argument("--warning-inventory-json", type=Path, default=Path("tmp/validation-eurusd-candidate-audit-warning-inventory.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-candidate-hardening-roadmap.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-candidate-hardening-roadmap.md"))
    args = parser.parse_args()

    audit = json.loads(args.audit_json.read_text(encoding="utf-8"))
    warnings = json.loads(args.warning_inventory_json.read_text(encoding="utf-8"))
    roadmap = build_roadmap(audit, warnings)
    args.output_json.write_text(json.dumps(roadmap, indent=2), encoding="utf-8")
    args.output_md.write_text(render_roadmap_md(roadmap), encoding="utf-8")
    print(json.dumps({"status": roadmap.get("status"), "watch_items": len(roadmap.get("active_watch_items", []))}))


if __name__ == "__main__":
    main()
