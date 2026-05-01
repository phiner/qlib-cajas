"""Catalog of research run artifacts under a root."""

from __future__ import annotations

import json
from pathlib import Path


def build_research_run_catalog(*, root: str | Path) -> dict:
    root_path = Path(root).expanduser().resolve()
    items = {
        "experiment_manifests": [],
        "metrics_files": [],
        "registry_files": [],
        "comparison_files": [],
        "gate_packets": [],
        "readiness_packets": [],
        "repro_reports": [],
        "governance_reports": [],
    }

    for p in root_path.rglob("*"):
        if not p.is_file():
            continue
        name = p.name
        rel = str(p.relative_to(root_path))
        if name == "experiment_manifest.json":
            items["experiment_manifests"].append(rel)
        elif name == "metrics.json":
            items["metrics_files"].append(rel)
        elif "registry" in name and name.endswith(".jsonl"):
            items["registry_files"].append(rel)
        elif "comparison" in name and name.endswith(".json"):
            items["comparison_files"].append(rel)
        elif name == "research_gate_packet.json":
            items["gate_packets"].append(rel)
        elif name == "final_readiness_packet.json":
            items["readiness_packets"].append(rel)
        elif "reproducibility_report" in name:
            items["repro_reports"].append(rel)
        elif "governance" in name:
            items["governance_reports"].append(rel)

    return {"schema_version": "v1", "root": str(root_path), "summary": {k: len(v) for k, v in items.items()}, "items": items}


def render_research_run_catalog_md(*, catalog: dict) -> str:
    lines = ["# Research Run Catalog", ""]
    for k, v in catalog.get("summary", {}).items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    for k, vals in catalog.get("items", {}).items():
        lines.append(f"## {k}")
        if not vals:
            lines.append("- none")
        else:
            for x in vals:
                lines.append(f"- `{x}`")
        lines.append("")
    return "\n".join(lines)
