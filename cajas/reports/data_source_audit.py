"""Static data source usage audit."""

from __future__ import annotations

import re
from pathlib import Path

CSV_RE = re.compile(r"[^\s\"']+\.csv", re.IGNORECASE)


def _scan_file(path: Path, data_root: str | None) -> dict:
    text = path.read_text(encoding="utf-8")
    csv_refs = sorted(set(CSV_RE.findall(text)))
    hardcoded_data_root = bool(data_root and data_root in text)
    eurusd_refs = sorted(set(re.findall(r"EURUSD_15 Mins_Bid_[0-9\.\-_]+\.csv", text)))
    return {
        "path": path.as_posix(),
        "hardcoded_data_root": hardcoded_data_root,
        "eurusd_refs": eurusd_refs,
        "csv_refs": csv_refs,
        "uses_read_csv": "read_csv(" in text,
        "uses_open_csv": bool(re.search(r"open\([^\)]*\.csv", text)),
        "has_cli_input_arg": "--input" in text or "input" in text and "argparse" in text,
        "supports_chunking": "chunksize=" in text or "chunk_size" in text,
        "reads_full_csv_likely": "read_csv(" in text and "chunksize=" not in text,
    }


def build_data_source_audit(*, project_root: str | Path, data_root: str | None = None, include_tasks: bool = True) -> dict:
    roots = [Path(project_root).expanduser().resolve()]
    if include_tasks:
        tasks = Path("tasks").resolve()
        if tasks.exists():
            roots.append(tasks)

    files: list[Path] = []
    for root in roots:
        files.extend(sorted(root.rglob("*.py")))
        files.extend(sorted(root.rglob("*.md")))
        files.extend(sorted(root.rglob("*.yaml")))
        files.extend(sorted(root.rglob("*.yml")))

    records = [_scan_file(path, data_root) for path in files]

    hardcoded = [r["path"] for r in records if r["hardcoded_data_root"]]
    read_csv_paths = [r["path"] for r in records if r["uses_read_csv"]]
    full_csv_paths = [r["path"] for r in records if r["reads_full_csv_likely"]]
    chunked_paths = [r["path"] for r in records if r["supports_chunking"]]
    eurusd_refs = sorted({x for r in records for x in r["eurusd_refs"]})

    return {
        "schema_version": "v1",
        "project_root": str(Path(project_root).resolve()),
        "data_root": data_root,
        "hardcoded_data_root_paths": hardcoded,
        "read_csv_paths": read_csv_paths,
        "reads_full_csv_likely_paths": full_csv_paths,
        "supports_chunking_paths": chunked_paths,
        "eurusd_csv_references": eurusd_refs,
        "records": records,
        "summary": {
            "file_count": len(records),
            "hardcoded_data_root_count": len(hardcoded),
            "read_csv_count": len(read_csv_paths),
            "reads_full_csv_likely_count": len(full_csv_paths),
            "chunking_support_count": len(chunked_paths),
        },
    }


def render_data_source_audit_md(*, report: dict) -> str:
    s = report.get("summary", {})
    lines = [
        "# Data Source Audit",
        "",
        f"- project_root: `{report.get('project_root')}`",
        f"- data_root: `{report.get('data_root')}`",
        f"- scanned_files: `{s.get('file_count')}`",
        f"- read_csv_count: `{s.get('read_csv_count')}`",
        f"- reads_full_csv_likely_count: `{s.get('reads_full_csv_likely_count')}`",
        f"- chunking_support_count: `{s.get('chunking_support_count')}`",
        "",
        "## Hardcoded Data Root Paths",
    ]
    for p in report.get("hardcoded_data_root_paths", [])[:40]:
        lines.append(f"- `{p}`")
    lines += ["", "## EURUSD CSV References"]
    refs = report.get("eurusd_csv_references", [])
    if not refs:
        lines.append("- none")
    else:
        for ref in refs:
            lines.append(f"- `{ref}`")
    lines += ["", "## Full CSV Read Candidates"]
    for p in report.get("reads_full_csv_likely_paths", [])[:40]:
        lines.append(f"- `{p}`")
    return "\n".join(lines) + "\n"
