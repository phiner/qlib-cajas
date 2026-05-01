"""Build lightweight artifact lineage graph."""

from __future__ import annotations

import hashlib
from pathlib import Path


KEYWORDS = {
    "labels/features": ["label", "feature"],
    "decision packet": ["decision"],
    "adapter": ["adapter", "compatibility"],
    "dataset/handler": ["handler", "dataset_contract"],
    "model bridge": ["model", "experiment", "registry", "comparison"],
    "research gate": ["gate"],
    "final readiness": ["final_readiness"],
    "reproducibility hardening": ["repro", "fingerprint", "normalized"],
    "governance": ["governance"],
    "review bundle": ["review", "bundle"],
}


def _phase_group(name: str) -> str:
    lower = name.lower()
    for k, pats in KEYWORDS.items():
        if any(p in lower for p in pats):
            return k
    return "other"


def _sha(path: Path) -> str:
    h = hashlib.sha256(path.read_bytes())
    return h.hexdigest()


def build_artifact_lineage(*, root: str | Path) -> dict:
    root_path = Path(root).expanduser().resolve()
    nodes = []
    edges = []

    files = [p for p in sorted(root_path.rglob("*")) if p.is_file()]
    for p in files:
        rel = str(p.relative_to(root_path))
        nodes.append(
            {
                "id": rel,
                "artifact_path": str(p),
                "artifact_type": p.suffix.lower().lstrip("."),
                "phase_group": _phase_group(rel),
                "exists": True,
                "checksum": _sha(p) if p.suffix.lower() in {".json", ".md", ".csv", ".jsonl"} else None,
            }
        )

    # Lightweight heuristic edges by directory ancestry.
    for p in files:
        rel = str(p.relative_to(root_path))
        parent = p.parent
        for q in files:
            if q == p:
                continue
            if q.parent == parent and q.name < p.name:
                edges.append({"source": str(q.relative_to(root_path)), "target": rel, "relation": "co_generated"})

    return {"schema_version": "v1", "root": str(root_path), "nodes": nodes, "edges": edges}


def render_artifact_lineage_md(*, lineage: dict) -> str:
    lines = ["# Artifact Lineage", "", f"- nodes: `{len(lineage.get('nodes', []))}`", f"- edges: `{len(lineage.get('edges', []))}`", ""]
    lines.append("## Nodes")
    for n in lineage.get("nodes", [])[:100]:
        lines.append(f"- `{n['id']}` ({n['phase_group']})")
    lines.append("")
    lines.append("## Edges")
    for e in lineage.get("edges", [])[:100]:
        lines.append(f"- `{e['source']}` -> `{e['target']}` ({e['relation']})")
    return "\n".join(lines) + "\n"
