"""Normalize artifacts for stable semantic comparison."""

from __future__ import annotations

import json
import re
from pathlib import Path


_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?")
_TMP_RE = re.compile(r"/tmp/[A-Za-z0-9_./-]+")


def _norm_scalar(value: str) -> str:
    out = value
    out = _TS_RE.sub("<TS>", out)
    out = _TMP_RE.sub("<TMP_ROOT>", out)
    out = out.replace(str(Path.cwd().resolve()), "<CWD>")
    return out


def _normalize_obj(obj):
    if isinstance(obj, dict):
        out = {}
        for k in sorted(obj.keys()):
            v = obj[k]
            if k in {"created_at_utc", "timestamp", "working_directory", "root", "absolute_path"}:
                out[k] = "<VAR>"
            else:
                out[k] = _normalize_obj(v)
        return out
    if isinstance(obj, list):
        return [_normalize_obj(v) for v in obj]
    if isinstance(obj, str):
        return _norm_scalar(obj)
    return obj


def normalize_json_artifact(*, input_path: str | Path, output_path: str | Path | None = None) -> dict:
    src = Path(input_path).expanduser().resolve()
    payload = json.loads(src.read_text(encoding="utf-8"))
    normalized = _normalize_obj(payload)
    rep = {
        "schema_version": "v1",
        "input_path": str(src),
        "output_path": "" if output_path is None else str(Path(output_path).expanduser().resolve()),
        "normalized_fields": ["timestamps", "tmp_paths", "cwd_paths", "absolute_paths"],
        "preserved_fields": ["status", "metrics", "row_count", "blocked_actions", "decisions"],
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
    txt = txt.replace(str(Path.cwd().resolve()), "<CWD>")
    rep = {
        "schema_version": "v1",
        "input_path": str(src),
        "output_path": "" if output_path is None else str(Path(output_path).expanduser().resolve()),
        "normalized_fields": ["timestamps", "tmp_paths", "cwd_paths"],
        "preserved_fields": ["headers", "status_lines", "checklists", "blocked_actions"],
        "warnings": [],
        "normalized_text": txt,
    }
    if output_path is not None:
        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(txt, encoding="utf-8")
    return rep
