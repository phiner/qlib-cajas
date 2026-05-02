"""Normalize artifacts for stable semantic comparison."""

from __future__ import annotations

import json
import re
from pathlib import Path

from cajas.reports.normalization_rule_registry import get_normalization_rules


_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?")
_TMP_RE = re.compile(r"/tmp/[A-Za-z0-9_./-]+")
_RUN_ROOT_RE = re.compile(r"\brun_[ab]\b")
_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_TS_FRACTION_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}\.\d+(?:Z|[+-]\d{2}:\d{2})?")
_HEX64_RE = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)


def _norm_scalar(value: str) -> str:
    out = value
    out = _TS_FRACTION_RE.sub("<TS>", out)
    out = _TS_RE.sub("<TS>", out)
    out = _TMP_RE.sub("<TMP_ROOT>", out)
    out = _RUN_ROOT_RE.sub("<RUN_ROOT>", out)
    out = _UUID_RE.sub("<UUID>", out)
    out = _HEX64_RE.sub("<HASH64>", out)
    out = out.replace(str(Path.cwd().resolve()), "<CWD>")
    return out


def normalize_stable_value(obj):
    if isinstance(obj, dict):
        out = {}
        for k in sorted(obj.keys()):
            v = obj[k]
            if k in {"created_at_utc", "timestamp", "working_directory", "root", "absolute_path", "run_id", "registry_id", "sha256"}:
                out[k] = "<VAR>"
            else:
                out[k] = normalize_stable_value(v)
        return out
    if isinstance(obj, list):
        return [normalize_stable_value(v) for v in obj]
    if isinstance(obj, str):
        return _norm_scalar(obj)
    return obj


def normalize_json_artifact(*, input_path: str | Path, output_path: str | Path | None = None) -> dict:
    src = Path(input_path).expanduser().resolve()
    payload = json.loads(src.read_text(encoding="utf-8"))
    normalized = normalize_stable_value(payload)
    rep = {
        "schema_version": "v1",
        "input_path": str(src),
        "output_path": "" if output_path is None else str(Path(output_path).expanduser().resolve()),
        "normalized_fields": ["timestamps", "tmp_paths", "cwd_paths", "absolute_paths", "run_root_labels"],
        "preserved_fields": ["status", "metrics", "row_count", "blocked_actions", "decisions"],
        "normalization_rules": [r.rule_id for r in get_normalization_rules() if r.enabled_by_default],
        "warnings": [],
        "normalized_payload": normalized,
    }
    if output_path is not None:
        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(normalized, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rep


def normalize_markdown_artifact(*, input_path: str | Path, output_path: str | Path | None = None) -> dict:
    src = Path(input_path).expanduser().resolve()
    txt = src.read_text(encoding="utf-8")
    txt = _TS_RE.sub("<TS>", txt)
    txt = _TMP_RE.sub("<TMP_ROOT>", txt)
    txt = _RUN_ROOT_RE.sub("<RUN_ROOT>", txt)
    txt = txt.replace(str(Path.cwd().resolve()), "<CWD>")
    rep = {
        "schema_version": "v1",
        "input_path": str(src),
        "output_path": "" if output_path is None else str(Path(output_path).expanduser().resolve()),
        "normalized_fields": ["timestamps", "tmp_paths", "cwd_paths", "run_root_labels"],
        "preserved_fields": ["headers", "status_lines", "checklists", "blocked_actions"],
        "normalization_rules": [r.rule_id for r in get_normalization_rules() if r.enabled_by_default],
        "warnings": [],
        "normalized_text": txt,
    }
    if output_path is not None:
        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt, encoding="utf-8")
    return rep
