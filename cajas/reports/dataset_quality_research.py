"""Dataset quality and chunked feature dry-run reports for offline research."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from cajas.data_io.chunked_csv_reader import iter_csv_chunks


def _to_rows(chunk: Any) -> tuple[list[dict], dict[str, str]]:
    if hasattr(chunk, "to_dict") and hasattr(chunk, "dtypes"):
        rows = chunk.to_dict(orient="records")
        dtypes = {str(k): str(v) for k, v in chunk.dtypes.to_dict().items()}
        return rows, dtypes
    if isinstance(chunk, list):
        if not chunk:
            return [], {}
        keys = list(chunk[0].keys())
        return chunk, {k: "unknown" for k in keys}
    return [], {}


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _to_md(report: dict) -> str:
    lines = [
        "# Dataset Quality Research Report",
        "",
        f"- row_count: `{report['row_count']}`",
        f"- column_count: `{report['column_count']}`",
        f"- datetime_parse_success_count: `{report['time_coverage']['datetime_parse_success_count']}`",
        f"- datetime_parse_failed_count: `{report['time_coverage']['datetime_parse_failed_count']}`",
        f"- earliest: `{report['time_coverage']['earliest_timestamp']}`",
        f"- latest: `{report['time_coverage']['latest_timestamp']}`",
        "",
        "## Label Diagnostics",
    ]
    for row in report["label_diagnostics"]:
        lines.append(
            f"- `{row['label']}` null=`{row['null_count']}` distinct=`{row['distinct_count']}` top_ratio=`{row['top_ratio']}` warning=`{row['imbalance_warning']}`"
        )
    lines += ["", "## Instrument Summary", f"- unique_instruments: `{report['instrument_summary']['unique_instrument_count']}`"]
    lines += ["", "## Chunked Feature Dry Run"]
    c = report["chunked_feature_dry_run"]
    lines.append(f"- chunk_count: `{c['chunk_count']}`")
    lines.append(f"- row_count: `{c['row_count']}`")
    lines.append(f"- rows_per_second: `{c['rows_per_second']}`")
    return "\n".join(lines) + "\n"


def _feature_manifest_md(manifest: dict) -> str:
    lines = ["# Feature Schema Manifest", ""]
    for feature in manifest["features"]:
        lines.append(
            f"- `{feature['name']}` dtype=`{feature['dtype']}` source_stage=`{feature['source_stage']}` tag=`{feature.get('tag','')}`"
        )
    return "\n".join(lines) + "\n"


def _queue_md(queue: dict) -> str:
    lines = ["# Offline Research Queue Summary", ""]
    for item in queue["items"]:
        lines.append(f"- [{item['priority']}] {item['task']}: {item['reason']}")
    return "\n".join(lines) + "\n"


def build_dataset_quality_research_artifacts(
    *,
    input_csv: str | Path,
    label_columns: list[str],
    feature_columns: list[str] | None = None,
    datetime_col: str = "datetime",
    instrument_col: str = "instrument",
    chunk_size: int = 50_000,
    row_limit: int | None = None,
    imbalance_warn_threshold: float = 0.75,
) -> dict:
    feature_columns = feature_columns or []
    col_counters: dict[str, dict[str, int]] = {}
    label_counters: dict[str, Counter[str]] = {label: Counter() for label in label_columns}
    label_nulls: dict[str, int] = {label: 0 for label in label_columns}

    row_count = 0
    chunk_count = 0
    parse_ok = 0
    parse_fail = 0
    earliest: datetime | None = None
    latest: datetime | None = None
    prev_dt: datetime | None = None
    suspicious_gaps: list[dict] = []
    hours: Counter[int] = Counter()
    instruments: Counter[str] = Counter()
    schema_by_col: dict[str, str] = {}

    selected_columns = sorted(set([datetime_col, instrument_col, *label_columns, *feature_columns]))
    for raw_chunk in iter_csv_chunks(
        input_csv,
        columns=selected_columns or None,
        chunk_size=chunk_size,
        row_limit=row_limit,
        parse_dates=[datetime_col],
    ):
        rows, dtypes = _to_rows(raw_chunk)
        if not rows:
            continue
        chunk_count += 1
        row_count += len(rows)
        for k, v in dtypes.items():
            schema_by_col[k] = v

        for row in rows:
            for col in selected_columns:
                v = row.get(col)
                if col not in col_counters:
                    col_counters[col] = {"non_null": 0, "null": 0}
                if v is None or str(v).strip() == "":
                    col_counters[col]["null"] += 1
                else:
                    col_counters[col]["non_null"] += 1

            dt = _parse_dt(row.get(datetime_col))
            if dt is None:
                parse_fail += 1
            else:
                parse_ok += 1
                if earliest is None or dt < earliest:
                    earliest = dt
                if latest is None or dt > latest:
                    latest = dt
                hours[dt.hour] += 1
                if prev_dt is not None:
                    gap = (dt - prev_dt).total_seconds()
                    if gap > 60 * 60 * 24:
                        suspicious_gaps.append({"from": prev_dt.isoformat(sep=" "), "to": dt.isoformat(sep=" "), "gap_seconds": int(gap)})
                prev_dt = dt

            inst = str(row.get(instrument_col, "")).strip()
            if inst:
                instruments[inst] += 1

            for label in label_columns:
                lv = row.get(label)
                if lv is None or str(lv).strip() == "":
                    label_nulls[label] += 1
                else:
                    label_counters[label][str(lv).strip()] += 1

    label_diagnostics: list[dict] = []
    for label in label_columns:
        ctr = label_counters[label]
        total_non_null = sum(ctr.values())
        top_ratio = 0.0
        if total_non_null > 0:
            top_ratio = max(ctr.values()) / total_non_null
        label_diagnostics.append(
            {
                "label": label,
                "null_count": label_nulls[label],
                "non_null_count": total_non_null,
                "distinct_count": len(ctr),
                "distribution": dict(ctr),
                "top_ratio": round(top_ratio, 6),
                "imbalance_warning": top_ratio >= imbalance_warn_threshold and total_non_null > 0,
            }
        )

    completeness = []
    for col, counts in sorted(col_counters.items()):
        total = counts["non_null"] + counts["null"]
        ratio = (counts["non_null"] / total) if total else 0.0
        completeness.append(
            {
                "column": col,
                "non_null_count": counts["non_null"],
                "null_count": counts["null"],
                "completeness_ratio": round(ratio, 6),
            }
        )

    chunked_feature_dry_run = {
        "selected_columns": selected_columns,
        "feature_columns": feature_columns,
        "chunk_size": chunk_size,
        "row_limit": row_limit,
        "chunk_count": chunk_count,
        "row_count": row_count,
        "schema_consistency": {"column_dtype_map": schema_by_col},
        "rows_per_second": None,  # filled by CLI timing wrapper
    }

    feature_manifest = {
        "schema_version": "v1",
        "features": [
            {
                "name": col,
                "dtype": schema_by_col.get(col, "unknown"),
                "source_stage": "feature_extraction",
                "tag": "fx_structure" if "feature" in col or col in feature_columns else "",
            }
            for col in feature_columns
        ],
    }

    queue_items: list[dict] = []
    for label in label_diagnostics:
        if label["imbalance_warning"]:
            queue_items.append({"priority": "high", "task": f"review imbalance for {label['label']}", "reason": f"top_ratio={label['top_ratio']}"})
    if parse_fail > 0:
        queue_items.append({"priority": "high", "task": "review datetime parse failures", "reason": f"failed_rows={parse_fail}"})
    if suspicious_gaps:
        queue_items.append({"priority": "medium", "task": "review suspicious timestamp gaps", "reason": f"gap_events={len(suspicious_gaps)}"})
    if not queue_items:
        queue_items.append({"priority": "low", "task": "continue periodic dataset QA loop", "reason": "no blocking findings"})

    queue_summary = {"schema_version": "v1", "scope": "offline_research_only", "items": queue_items}

    report = {
        "schema_version": "v1",
        "scope": "offline_research_only",
        "input_csv": str(Path(input_csv).expanduser().resolve()),
        "row_count": row_count,
        "column_count": len(selected_columns),
        "column_completeness": completeness,
        "label_diagnostics": label_diagnostics,
        "time_coverage": {
            "datetime_column": datetime_col,
            "datetime_parse_success_count": parse_ok,
            "datetime_parse_failed_count": parse_fail,
            "earliest_timestamp": None if earliest is None else earliest.isoformat(sep=" "),
            "latest_timestamp": None if latest is None else latest.isoformat(sep=" "),
            "suspicious_gap_count": len(suspicious_gaps),
            "suspicious_gap_examples": suspicious_gaps[:10],
            "session_hour_distribution": {str(k): v for k, v in sorted(hours.items())},
        },
        "instrument_summary": {
            "instrument_column": instrument_col,
            "unique_instrument_count": len(instruments),
            "top_instruments": [{"instrument": k, "count": v} for k, v in instruments.most_common(10)],
        },
        "chunked_feature_dry_run": chunked_feature_dry_run,
    }

    return {
        "dataset_quality_report": report,
        "feature_schema_manifest": feature_manifest,
        "offline_research_queue_summary": queue_summary,
    }


def build_dataset_quality_report(**kwargs: Any) -> dict:
    return build_dataset_quality_research_artifacts(**kwargs)["dataset_quality_report"]


def build_label_coverage_diagnostics(**kwargs: Any) -> dict:
    report = build_dataset_quality_research_artifacts(**kwargs)["dataset_quality_report"]
    return {
        "schema_version": report["schema_version"],
        "scope": report["scope"],
        "label_diagnostics": report["label_diagnostics"],
    }


def build_time_coverage_diagnostics(**kwargs: Any) -> dict:
    report = build_dataset_quality_research_artifacts(**kwargs)["dataset_quality_report"]
    return {
        "schema_version": report["schema_version"],
        "scope": report["scope"],
        "time_coverage": report["time_coverage"],
        "instrument_summary": report["instrument_summary"],
    }


def build_chunked_feature_dry_run(**kwargs: Any) -> dict:
    report = build_dataset_quality_research_artifacts(**kwargs)["dataset_quality_report"]
    return {
        "schema_version": report["schema_version"],
        "scope": report["scope"],
        "chunked_feature_dry_run": report["chunked_feature_dry_run"],
    }


def build_feature_schema_manifest(**kwargs: Any) -> dict:
    return build_dataset_quality_research_artifacts(**kwargs)["feature_schema_manifest"]


def build_offline_research_queue_summary(**kwargs: Any) -> dict:
    return build_dataset_quality_research_artifacts(**kwargs)["offline_research_queue_summary"]


def render_dataset_quality_bundle_markdown(*, bundle: dict) -> dict[str, str]:
    return {
        "dataset_quality_report_md": _to_md(bundle["dataset_quality_report"]),
        "feature_schema_manifest_md": _feature_manifest_md(bundle["feature_schema_manifest"]),
        "offline_research_queue_summary_md": _queue_md(bundle["offline_research_queue_summary"]),
    }


def render_dataset_quality_report_markdown(*, report: dict) -> str:
    return _to_md(report)


def render_label_coverage_markdown(*, diagnostics: dict) -> str:
    lines = ["# Label Coverage Diagnostics", ""]
    for row in diagnostics.get("label_diagnostics", []):
        lines.append(
            f"- `{row['label']}` null=`{row['null_count']}` non_null=`{row['non_null_count']}` top_ratio=`{row['top_ratio']}` warning=`{row['imbalance_warning']}`"
        )
    return "\n".join(lines) + "\n"


def render_time_coverage_markdown(*, diagnostics: dict) -> str:
    coverage = diagnostics.get("time_coverage", {})
    lines = [
        "# Time Coverage Diagnostics",
        "",
        f"- earliest: `{coverage.get('earliest_timestamp')}`",
        f"- latest: `{coverage.get('latest_timestamp')}`",
        f"- datetime_parse_success_count: `{coverage.get('datetime_parse_success_count')}`",
        f"- datetime_parse_failed_count: `{coverage.get('datetime_parse_failed_count')}`",
        f"- suspicious_gap_count: `{coverage.get('suspicious_gap_count')}`",
    ]
    return "\n".join(lines) + "\n"


def render_chunked_feature_dry_run_markdown(*, dry_run: dict) -> str:
    node = dry_run.get("chunked_feature_dry_run", {})
    lines = [
        "# Chunked Feature Dry Run",
        "",
        f"- chunk_size: `{node.get('chunk_size')}`",
        f"- row_limit: `{node.get('row_limit')}`",
        f"- chunk_count: `{node.get('chunk_count')}`",
        f"- row_count: `{node.get('row_count')}`",
        f"- rows_per_second: `{node.get('rows_per_second')}`",
    ]
    return "\n".join(lines) + "\n"


def render_feature_schema_manifest_markdown(*, manifest: dict) -> str:
    return _feature_manifest_md(manifest)


def render_offline_research_queue_summary_markdown(*, queue: dict) -> str:
    return _queue_md(queue)
