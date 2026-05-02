"""Static data source usage audit with line-level triage."""

from __future__ import annotations

import re
from pathlib import Path

CSV_RE = re.compile(r"[^\s\"']+\.csv", re.IGNORECASE)
EURUSD_RE = re.compile(r"EURUSD_15 Mins_Bid_[0-9\.\-_]+\.csv")


def _iter_line_hits(text: str, pattern: str) -> list[dict]:
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        if pattern in line:
            out.append({"line": i, "snippet": line.strip()[:200]})
    return out


def _classify(path: Path, uses_read_csv: bool, hardcoded_data_root: bool, csv_refs: list[str]) -> str:
    p = path.as_posix()
    if p.endswith(".md") or p.endswith(".yaml") or p.endswith(".yml"):
        return "docs_only"
    if "/tests/" in p:
        return "test_only"
    if hardcoded_data_root or any("/home/phiner/projects/research/data" in x for x in csv_refs):
        return "real_data_risk"
    if uses_read_csv:
        return "generated_artifact_risk"
    if "fixture" in p:
        return "fixture_only"
    return "unknown"


def _remediation(category: str, supports_chunking: bool) -> str:
    if category == "real_data_risk":
        return "add allow_large_data + row_limit/chunk_size and default sample-only"
    if category == "generated_artifact_risk":
        return "prefer row_limit or chunked reads for large artifacts"
    if category == "test_only":
        return "ensure tiny fixtures and avoid subprocess-heavy csv paths"
    if supports_chunking:
        return "keep_fast"
    return "consider chunking or loading policy"


def _scan_file(path: Path, data_root: str | None) -> dict:
    text = path.read_text(encoding="utf-8")
    csv_refs = sorted(set(CSV_RE.findall(text)))
    hardcoded_data_root = bool(data_root and data_root in text)
    eurusd_refs = sorted(set(EURUSD_RE.findall(text)))
    uses_read_csv = "read_csv(" in text
    supports_chunking = "chunksize=" in text or "chunk_size" in text
    policy_guarded = "evaluate_loading_decision(" in text and "CsvLoadingPolicy(" in text
    
    # False positive detection
    p = path.as_posix()
    is_chunked_csv_reader_impl = "chunked_csv_reader.py" in p
    is_string_pattern_only = "READ_PATTERNS" in text or "WRITE_PATTERNS" in text
    
    reads_full_csv_likely = (
        uses_read_csv
        and "chunksize=" not in text
        and "nrows=" not in text
        and not policy_guarded
        and not is_chunked_csv_reader_impl
        and not is_string_pattern_only
    )
    
    category = _classify(path, uses_read_csv, hardcoded_data_root, csv_refs)
    remediation = _remediation(category, supports_chunking)
    return {
        "path": path.as_posix(),
        "hardcoded_data_root": hardcoded_data_root,
        "eurusd_refs": eurusd_refs,
        "csv_refs": csv_refs,
        "uses_read_csv": uses_read_csv,
        "uses_open_csv": bool(re.search(r"open\([^\)]*\.csv", text)),
        "has_cli_input_arg": "--input" in text or ("argparse" in text and "input" in text),
        "supports_chunking": supports_chunking,
        "policy_guarded": policy_guarded,
        "reads_full_csv_likely": reads_full_csv_likely,
        "category": category,
        "suggested_remediation": remediation,
        "read_csv_hits": _iter_line_hits(text, "read_csv("),
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

    by_category: dict[str, int] = {}
    for r in records:
        by_category[r["category"]] = by_category.get(r["category"], 0) + 1

    return {
        "schema_version": "v2",
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
            "by_category": by_category,
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
        "## Category Summary",
    ]
    for k, v in sorted((s.get("by_category") or {}).items()):
        lines.append(f"- {k}: `{v}`")

    lines += ["", "## High-Risk Full CSV Candidates"]
    for r in report.get("records", []):
        if r.get("reads_full_csv_likely") and r.get("category") in {"real_data_risk", "generated_artifact_risk"}:
            hit = (r.get("read_csv_hits") or [{}])[0]
            lines.append(
                f"- `{r['path']}` line `{hit.get('line')}`: {r.get('suggested_remediation')} | `{hit.get('snippet','')}`"
            )

    lines += ["", "## EURUSD CSV References"]
    refs = report.get("eurusd_csv_references", [])
    if not refs:
        lines.append("- none")
    else:
        for ref in refs:
            lines.append(f"- `{ref}`")
    return "\n".join(lines) + "\n"
