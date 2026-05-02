"""Compare normalized artifacts and classify drift severity."""

from __future__ import annotations

import json
from difflib import unified_diff
from pathlib import Path

from cajas.reports.artifact_normalizer import normalize_json_artifact, normalize_markdown_artifact


def _json_paths(left, right, prefix="$"):
    diffs = []
    if type(left) is not type(right):
        diffs.append({"path": prefix, "kind": "type_changed", "left": type(left).__name__, "right": type(right).__name__})
        return diffs
    if isinstance(left, dict):
        lkeys = set(left)
        rkeys = set(right)
        for k in sorted(lkeys - rkeys):
            diffs.append({"path": f"{prefix}.{k}", "kind": "removed_key"})
        for k in sorted(rkeys - lkeys):
            diffs.append({"path": f"{prefix}.{k}", "kind": "added_key"})
        for k in sorted(lkeys & rkeys):
            diffs.extend(_json_paths(left[k], right[k], f"{prefix}.{k}"))
        return diffs
    if isinstance(left, list):
        if len(left) != len(right):
            diffs.append({"path": prefix, "kind": "list_length_changed", "left": len(left), "right": len(right)})
        for i, (lv, rv) in enumerate(zip(left, right)):
            diffs.extend(_json_paths(lv, rv, f"{prefix}[{i}]"))
        if len(left) == len(right) and sorted(map(str, left)) == sorted(map(str, right)) and left != right:
            diffs.append({"path": prefix, "kind": "list_ordering_changed"})
        return diffs
    if left != right:
        diffs.append({"path": prefix, "kind": "scalar_changed", "left": left, "right": right})
    return diffs


def _severity(item: dict) -> str:
    path = item.get("path", "").lower()
    kind = item.get("kind")
    if kind == "list_ordering_changed":
        return "ordering_only"
    if any(k in path for k in ("timestamp", "created_at", "root", "working_directory", "absolute_path")):
        return "normalization_gap"
    if any(k in path for k in ("status", "metrics", "score", "count", "label")):
        return "semantic"
    if any(k in path for k in ("id", "run_name", "path")):
        return "metadata_only"
    return "unknown"


def build_normalized_artifact_diff(*, left_path: str | Path, right_path: str | Path) -> dict:
    left = Path(left_path).expanduser().resolve()
    right = Path(right_path).expanduser().resolve()
    if left.suffix.lower() == ".json" and right.suffix.lower() == ".json":
        l = normalize_json_artifact(input_path=left)["normalized_payload"]
        r = normalize_json_artifact(input_path=right)["normalized_payload"]
        changes = _json_paths(l, r)
        for c in changes:
            c["severity"] = _severity(c)
        return {"schema_version": "v1", "type": "json", "left": str(left), "right": str(right), "changes": changes}
    ltxt = normalize_markdown_artifact(input_path=left)["normalized_text"]
    rtxt = normalize_markdown_artifact(input_path=right)["normalized_text"]
    lines = list(unified_diff(ltxt.splitlines(), rtxt.splitlines(), fromfile=str(left), tofile=str(right), lineterm=""))
    return {"schema_version": "v1", "type": "text", "left": str(left), "right": str(right), "line_diff": lines}

