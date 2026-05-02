"""Dataset quality and chunked feature dry-run reports for offline research."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from cajas.data_io.chunked_csv_reader import iter_csv_chunks


def _classify_issue_severity(issue_type: str, count: int, threshold: float = 0.0) -> str:
    """Classify issue severity for offline research review."""
    if issue_type in ("missing_required_column", "unreadable_input"):
        return "blocked"
    if issue_type in ("missing_labels", "parse_failures", "dominant_imbalance"):
        if count > 0 or threshold > 0.9:
            return "review_needed"
        return "warning"
    if issue_type in ("suspicious_gaps", "rare_class", "moderate_imbalance"):
        return "warning"
    return "info"


def _derive_report_status(severity_counts: dict[str, int]) -> str:
    """Derive overall report status from severity counts."""
    if severity_counts.get("blocked", 0) > 0:
        return "blocked"
    if severity_counts.get("review_needed", 0) > 0:
        return "review_needed"
    if severity_counts.get("warning", 0) > 0:
        return "warn"
    return "pass"


def _compute_quality_score(
    *,
    row_count: int,
    column_count: int,
    parse_ok: int,
    parse_fail: int,
    label_diagnostics: list[dict],
    completeness: list[dict],
    has_required_columns: bool,
) -> dict:
    """Compute offline dataset quality score (not trading/model performance)."""
    components = []
    score = 0.0
    max_score = 100.0

    # Schema completeness (20 points)
    if has_required_columns:
        score += 20.0
        components.append({"name": "schema_completeness", "score": 20.0, "max": 20.0, "status": "pass"})
    else:
        components.append({"name": "schema_completeness", "score": 0.0, "max": 20.0, "status": "blocked"})

    # Timestamp availability (20 points)
    if parse_ok > 0:
        ts_ratio = parse_ok / (parse_ok + parse_fail) if (parse_ok + parse_fail) > 0 else 0.0
        ts_score = 20.0 * ts_ratio
        score += ts_score
        components.append({"name": "timestamp_availability", "score": round(ts_score, 2), "max": 20.0, "status": "pass" if ts_ratio > 0.9 else "warn"})
    else:
        components.append({"name": "timestamp_availability", "score": 0.0, "max": 20.0, "status": "review_needed"})

    # Row count confidence (15 points)
    if row_count >= 100:
        score += 15.0
        components.append({"name": "row_count_confidence", "score": 15.0, "max": 15.0, "status": "pass"})
    elif row_count >= 10:
        score += 10.0
        components.append({"name": "row_count_confidence", "score": 10.0, "max": 15.0, "status": "warn"})
    else:
        components.append({"name": "row_count_confidence", "score": 0.0, "max": 15.0, "status": "review_needed"})

    # Label coverage (20 points)
    if label_diagnostics:
        avg_non_null = sum(d["non_null_count"] for d in label_diagnostics) / len(label_diagnostics)
        label_ratio = min(1.0, avg_non_null / row_count) if row_count > 0 else 0.0
        label_score = 20.0 * label_ratio
        score += label_score
        components.append({"name": "label_coverage", "score": round(label_score, 2), "max": 20.0, "status": "pass" if label_ratio > 0.8 else "warn"})
    else:
        components.append({"name": "label_coverage", "score": 0.0, "max": 20.0, "status": "review_needed"})

    # Column completeness (15 points)
    if completeness:
        avg_completeness = sum(c["completeness_ratio"] for c in completeness) / len(completeness)
        comp_score = 15.0 * avg_completeness
        score += comp_score
        components.append({"name": "column_completeness", "score": round(comp_score, 2), "max": 15.0, "status": "pass" if avg_completeness > 0.9 else "warn"})
    else:
        components.append({"name": "column_completeness", "score": 0.0, "max": 15.0, "status": "review_needed"})

    # Bounded read confidence (10 points)
    score += 10.0
    components.append({"name": "bounded_read_confidence", "score": 10.0, "max": 10.0, "status": "pass"})

    # Derive grade
    pct = (score / max_score) * 100.0
    if pct >= 90:
        grade = "A"
    elif pct >= 75:
        grade = "B"
    elif pct >= 60:
        grade = "C"
    elif pct >= 40:
        grade = "D"
    else:
        grade = "review_needed"

    return {
        "score": round(score, 2),
        "max_score": max_score,
        "percentage": round(pct, 2),
        "grade": grade,
        "components": components,
    }


def _build_label_review_buckets(label_diagnostics: list[dict], row_count: int) -> list[dict]:
    """Build prioritized label review buckets."""
    buckets = []
    for diag in label_diagnostics:
        label = diag["label"]
        null_count = diag["null_count"]
        non_null = diag["non_null_count"]
        distinct = diag["distinct_count"]
        top_ratio = diag["top_ratio"]

        if non_null == 0:
            buckets.append({
                "bucket": "missing_labels",
                "priority": "high",
                "count": row_count,
                "label": label,
                "reason": f"no non-null values for {label}",
                "recommended_action": "inspect label generation or fixture data",
            })
        elif null_count > non_null:
            buckets.append({
                "bucket": "sparse_labels",
                "priority": "high",
                "count": null_count,
                "label": label,
                "reason": f"null_count={null_count} > non_null={non_null}",
                "recommended_action": "review label coverage",
            })
        elif top_ratio >= 0.9:
            buckets.append({
                "bucket": "dominant_class_imbalance",
                "priority": "high",
                "count": int(top_ratio * non_null),
                "label": label,
                "reason": f"top_ratio={top_ratio:.3f}",
                "recommended_action": "review class distribution or rebalance",
            })
        elif top_ratio >= 0.75:
            buckets.append({
                "bucket": "moderate_imbalance",
                "priority": "medium",
                "count": int(top_ratio * non_null),
                "label": label,
                "reason": f"top_ratio={top_ratio:.3f}",
                "recommended_action": "monitor class distribution",
            })
        elif distinct < 2:
            buckets.append({
                "bucket": "single_class",
                "priority": "high",
                "count": non_null,
                "label": label,
                "reason": f"distinct_count={distinct}",
                "recommended_action": "verify label generation logic",
            })

    # Sort: high priority first, then by count descending, then by label name
    buckets.sort(key=lambda b: (
        {"high": 0, "medium": 1, "low": 2}.get(b["priority"], 3),
        -b["count"],
        b["label"],
    ))
    return buckets


def _build_ranked_review_items(
    *,
    quality_score: dict,
    label_buckets: list[dict],
    parse_fail: int,
    suspicious_gap_count: int,
    feature_columns: list[str],
) -> list[dict]:
    """Build ranked offline research review queue."""
    items = []
    rank = 1

    # High priority: blocked/review_needed from quality score
    for comp in quality_score["components"]:
        if comp["status"] in ("blocked", "review_needed"):
            items.append({
                "rank": rank,
                "priority": "high",
                "category": "schema",
                "title": f"Review {comp['name']}",
                "reason": f"status={comp['status']}, score={comp['score']}/{comp['max']}",
                "recommended_action": "inspect dataset schema and fixture data",
                "source_report": "dataset_quality_report",
            })
            rank += 1

    # High priority label buckets
    for bucket in label_buckets:
        if bucket["priority"] == "high":
            items.append({
                "rank": rank,
                "priority": "high",
                "category": "labels",
                "title": f"Review {bucket['bucket']} for {bucket['label']}",
                "reason": bucket["reason"],
                "recommended_action": bucket["recommended_action"],
                "source_report": "label_coverage_diagnostics",
            })
            rank += 1

    # Medium priority: parse failures
    if parse_fail > 0:
        items.append({
            "rank": rank,
            "priority": "medium",
            "category": "time",
            "title": "Review datetime parse failures",
            "reason": f"failed_rows={parse_fail}",
            "recommended_action": "inspect timestamp format and fixture data",
            "source_report": "time_coverage_diagnostics",
        })
        rank += 1

    # Medium priority: suspicious gaps
    if suspicious_gap_count > 0:
        items.append({
            "rank": rank,
            "priority": "medium",
            "category": "time",
            "title": "Review suspicious timestamp gaps",
            "reason": f"gap_events={suspicious_gap_count}",
            "recommended_action": "inspect time series continuity",
            "source_report": "time_coverage_diagnostics",
        })
        rank += 1

    # Medium priority label buckets
    for bucket in label_buckets:
        if bucket["priority"] == "medium":
            items.append({
                "rank": rank,
                "priority": "medium",
                "category": "labels",
                "title": f"Monitor {bucket['bucket']} for {bucket['label']}",
                "reason": bucket["reason"],
                "recommended_action": bucket["recommended_action"],
                "source_report": "label_coverage_diagnostics",
            })
            rank += 1

    # Low priority: feature readiness
    if not feature_columns:
        items.append({
            "rank": rank,
            "priority": "low",
            "category": "features",
            "title": "No feature columns specified",
            "reason": "feature_columns=[]",
            "recommended_action": "specify feature columns for dry-run validation",
            "source_report": "chunked_feature_dry_run",
        })
        rank += 1

    # Default: continue QA loop
    if not items:
        items.append({
            "rank": 1,
            "priority": "low",
            "category": "data_source",
            "title": "Continue periodic dataset QA loop",
            "reason": "no blocking findings",
            "recommended_action": "maintain regular dataset quality checks",
            "source_report": "offline_research_queue_summary",
        })

    return items


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
        f"- status: `{report.get('status', 'unknown')}`",
        f"- schema_version: `{report.get('schema_version', 'v1')}`",
        "",
        "## Quality Score",
        "",
        f"- score: `{report['quality_score']['score']}/{report['quality_score']['max_score']}`",
        f"- percentage: `{report['quality_score']['percentage']}%`",
        f"- grade: `{report['quality_score']['grade']}`",
        "",
        "### Components",
    ]
    for comp in report["quality_score"]["components"]:
        lines.append(f"- {comp['name']}: `{comp['score']}/{comp['max']}` status=`{comp['status']}`")

    lines += [
        "",
        "## Dataset Summary",
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

    if report.get("label_review_buckets"):
        lines += ["", "## Label Review Buckets"]
        for bucket in report["label_review_buckets"]:
            lines.append(f"- [{bucket['priority']}] {bucket['bucket']} for `{bucket['label']}`: {bucket['reason']}")

    lines += ["", "## Instrument Summary", f"- unique_instruments: `{report['instrument_summary']['unique_instrument_count']}`"]
    lines += ["", "## Chunked Feature Dry Run"]
    c = report["chunked_feature_dry_run"]
    lines.append(f"- chunk_count: `{c['chunk_count']}`")
    lines.append(f"- row_count: `{c['row_count']}`")
    lines.append(f"- rows_per_second: `{c['rows_per_second']}`")

    if report.get("feature_readiness"):
        lines += ["", "## Feature Readiness"]
        fr = report["feature_readiness"]
        lines.append(f"- status: `{fr['status']}`")
        lines.append(f"- ready_columns: `{len(fr['ready_columns'])}`")
        if fr.get("warnings"):
            for warn in fr["warnings"]:
                lines.append(f"- warning: {warn}")

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

    if queue.get("ranked_review_items"):
        lines += ["## Ranked Review Items", ""]
        for item in queue["ranked_review_items"]:
            lines.append(f"{item['rank']}. [{item['priority']}] {item['category']}: {item['title']}")
            lines.append(f"   - reason: {item['reason']}")
            lines.append(f"   - action: {item['recommended_action']}")
            lines.append("")

    lines += ["## Legacy Queue Items", ""]
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
        "schema_version": "feature_schema_manifest.v1",
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

    # Compute quality score
    has_required_columns = datetime_col in schema_by_col and instrument_col in schema_by_col
    quality_score = _compute_quality_score(
        row_count=row_count,
        column_count=len(selected_columns),
        parse_ok=parse_ok,
        parse_fail=parse_fail,
        label_diagnostics=label_diagnostics,
        completeness=completeness,
        has_required_columns=has_required_columns,
    )

    # Build label review buckets
    label_buckets = _build_label_review_buckets(label_diagnostics, row_count)

    # Build ranked review items
    ranked_items = _build_ranked_review_items(
        quality_score=quality_score,
        label_buckets=label_buckets,
        parse_fail=parse_fail,
        suspicious_gap_count=len(suspicious_gaps),
        feature_columns=feature_columns,
    )

    # Compute severity counts
    severity_counts = {"info": 0, "warning": 0, "review_needed": 0, "blocked": 0}
    for comp in quality_score["components"]:
        status = comp["status"]
        if status == "blocked":
            severity_counts["blocked"] += 1
        elif status == "review_needed":
            severity_counts["review_needed"] += 1
        elif status == "warn":
            severity_counts["warning"] += 1
        else:
            severity_counts["info"] += 1

    report_status = _derive_report_status(severity_counts)

    # Legacy queue items for backward compatibility
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

    queue_summary = {
        "schema_version": "offline_research_queue_summary.v1",
        "scope": "offline_research_only",
        "items": queue_items,
        "ranked_review_items": ranked_items,
    }

    report = {
        "schema_version": "dataset_quality_research.v1",
        "report_type": "dataset_quality_report",
        "status": report_status,
        "severity_counts": severity_counts,
        "scope": "offline_research_only",
        "input_csv": str(Path(input_csv).expanduser().resolve()),
        "row_count": row_count,
        "column_count": len(selected_columns),
        "quality_score": quality_score,
        "column_completeness": completeness,
        "label_diagnostics": label_diagnostics,
        "label_review_buckets": label_buckets,
        "time_coverage": {
            "datetime_column": datetime_col,
            "datetime_parse_success_count": parse_ok,
            "datetime_parse_failed_count": parse_fail,
            "earliest_timestamp": None if earliest is None else earliest.isoformat(sep=" "),
            "latest_timestamp": None if latest is None else latest.isoformat(sep=" "),
            "suspicious_gap_count": len(suspicious_gaps),
            "suspicious_gap_examples": suspicious_gaps[:10],
            "session_hour_distribution": {str(k): v for k, v in sorted(hours.items())},
            "time_quality": {
                "status": "review_needed" if parse_fail > 0 else "pass",
                "issues": [f"parse_failures={parse_fail}"] if parse_fail > 0 else [],
            },
        },
        "instrument_summary": {
            "instrument_column": instrument_col,
            "unique_instrument_count": len(instruments),
            "top_instruments": [{"instrument": k, "count": v} for k, v in instruments.most_common(10)],
        },
        "chunked_feature_dry_run": chunked_feature_dry_run,
        "feature_readiness": {
            "status": "pass" if feature_columns else "review_needed",
            "ready_columns": feature_columns if feature_columns else [],
            "review_columns": [],
            "blocked_columns": [],
            "warnings": [] if feature_columns else ["no feature columns specified"],
        },
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
