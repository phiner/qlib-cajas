import json
from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_candidate_audit import (
    build_validation_eurusd_candidate_audit,
    render_validation_eurusd_candidate_audit_markdown,
)
from cajas.research.eurusd_pattern_candidates import detect_eurusd_pattern_candidates


def _mini_clean(path: Path) -> Path:
    rows = []
    base = 1.1
    for i in range(120):
        o = base
        c = o + (0.0002 if i % 2 == 0 else -0.00017)
        h = max(o, c) + 0.00035
        l = min(o, c) - 0.0003
        rows.append(
            {
                "timestamp": f"2025-01-01 {i//4:02d}:{(i%4)*15:02d}:00",
                "open": round(o, 6),
                "high": round(h, 6),
                "low": round(l, 6),
                "close": round(c, 6),
                "source_row_index": i,
            }
        )
        base += 0.00002
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return path


def test_audit_report_sections_and_read_only(tmp_path: Path) -> None:
    clean = _mini_clean(tmp_path / "clean.csv")
    clean_df = pd.read_csv(clean)
    cand = detect_eurusd_pattern_candidates(clean_df, min_confidence=0.5)
    cand_path = tmp_path / "candidates.csv"
    cand.to_csv(cand_path, index=False)

    template = cand.head(20).copy()
    template_path = tmp_path / "template.csv"
    template.to_csv(template_path, index=False)

    batch = cand.head(30).copy()
    batch_path = tmp_path / "batch.csv"
    batch.to_csv(batch_path, index=False)
    before = batch_path.read_text(encoding="utf-8")

    payload = build_validation_eurusd_candidate_audit(
        candidate_csv=cand_path,
        template_csv=template_path,
        batch_csv=batch_path,
        clean_view_csv=clean,
        rejected_csv=tmp_path / "missing_rejected.csv",
    )
    assert payload["status"] in {"pass", "watch", "needs_rule_refinement"}
    for key in [
        "causality_summary",
        "future_usage_summary",
        "selection_explainability_summary",
        "multi_label_summary",
        "duplicate_region_summary",
        "coverage_summary",
        "active_batch_warnings",
        "next_actions",
    ]:
        assert key in payload
    assert before == batch_path.read_text(encoding="utf-8")
    md = render_validation_eurusd_candidate_audit_markdown(payload)
    assert "EURUSD Candidate Audit" in md


def test_audit_missing_candidate_blocked(tmp_path: Path) -> None:
    payload = build_validation_eurusd_candidate_audit(
        candidate_csv=tmp_path / "missing.csv",
        template_csv=tmp_path / "template.csv",
        batch_csv=tmp_path / "batch.csv",
        clean_view_csv=tmp_path / "clean.csv",
        rejected_csv=tmp_path / "rejected.csv",
    )
    assert payload["status"] == "blocked"


def test_candidate_rows_include_causality_fields(tmp_path: Path) -> None:
    clean = _mini_clean(tmp_path / "clean2.csv")
    cand = detect_eurusd_pattern_candidates(pd.read_csv(clean), min_confidence=0.5)
    needed = [
        "causal_candidate",
        "candidate_logic_uses_future_bars",
        "candidate_logic_future_bars_used",
        "review_filter_uses_future_bars",
        "review_filter_future_bars_used",
        "label_uses_future_bars",
        "not_for_live_signal",
        "primary_selection_reason",
    ]
    for col in needed:
        assert col in cand.columns


def test_audit_status_gate_payload_when_selected_rows_are_complete(tmp_path: Path) -> None:
    clean = _mini_clean(tmp_path / "clean_pass.csv")
    cand = detect_eurusd_pattern_candidates(pd.read_csv(clean), min_confidence=0.5)
    if cand.empty:
        return
    batch = cand.copy()
    if "excluded_late_reversal_anchor" in batch.columns:
        batch = batch[~batch["excluded_late_reversal_anchor"].fillna(False).astype(bool)]
    if "preferred_review_candidate" in batch.columns:
        batch = batch[batch["preferred_review_candidate"].fillna(True).astype(bool)]
    batch = batch.head(30).copy()
    cand_path = tmp_path / "cand.csv"
    template_path = tmp_path / "template.csv"
    batch_path = tmp_path / "batch.csv"
    cand.to_csv(cand_path, index=False)
    cand.head(100).to_csv(template_path, index=False)
    batch.to_csv(batch_path, index=False)
    payload = build_validation_eurusd_candidate_audit(
        candidate_csv=cand_path,
        template_csv=template_path,
        batch_csv=batch_path,
        clean_view_csv=clean,
        rejected_csv=tmp_path / "rej.csv",
    )
    assert payload["status"] in {"pass", "watch", "needs_rule_refinement"}
    assert "audit_gates" in payload
    assert "batch_quality_metrics" in payload
    assert "trend_tail_bias_audit" in payload


def test_trend_tail_bias_summary_present(tmp_path: Path) -> None:
    clean = _mini_clean(tmp_path / "clean_tail.csv")
    cand = detect_eurusd_pattern_candidates(pd.read_csv(clean), min_confidence=0.5)
    if cand.empty:
        return
    cand_path = tmp_path / "cand_tail.csv"
    batch_path = tmp_path / "batch_tail.csv"
    cand.to_csv(cand_path, index=False)
    cand.head(50).to_csv(tmp_path / "template_tail.csv", index=False)
    cand.head(20).to_csv(batch_path, index=False)
    payload = build_validation_eurusd_candidate_audit(
        candidate_csv=cand_path,
        template_csv=tmp_path / "template_tail.csv",
        batch_csv=batch_path,
        clean_view_csv=clean,
        rejected_csv=tmp_path / "rej_tail.csv",
    )
    summary = payload.get("trend_tail_bias_audit", {})
    assert "trend_batch_count" in summary
    assert "trend_near_tail_ratio" in summary
    assert "tail_bias_status" in summary


def test_audit_status_needs_rule_refinement_on_selected_reason_gap(tmp_path: Path) -> None:
    clean = _mini_clean(tmp_path / "clean_needs.csv")
    cand = detect_eurusd_pattern_candidates(pd.read_csv(clean), min_confidence=0.5)
    if cand.empty:
        return
    cand = cand.copy()
    cand.loc[:10, "primary_selection_reason"] = ""
    cand_path = tmp_path / "cand.csv"
    template_path = tmp_path / "template.csv"
    batch_path = tmp_path / "batch.csv"
    cand.to_csv(cand_path, index=False)
    cand.head(50).to_csv(template_path, index=False)
    cand.head(20).to_csv(batch_path, index=False)
    payload = build_validation_eurusd_candidate_audit(
        candidate_csv=cand_path,
        template_csv=template_path,
        batch_csv=batch_path,
        clean_view_csv=clean,
        rejected_csv=tmp_path / "rej.csv",
    )
    assert payload["status"] == "needs_rule_refinement"


def test_audit_status_blocked_when_missing_causality_columns(tmp_path: Path) -> None:
    clean = _mini_clean(tmp_path / "clean_blocked.csv")
    cand = detect_eurusd_pattern_candidates(pd.read_csv(clean), min_confidence=0.5)
    if cand.empty:
        return
    cand = cand.drop(
        columns=[
            "causal_candidate",
            "candidate_logic_uses_future_bars",
            "candidate_logic_future_bars_used",
            "review_filter_uses_future_bars",
            "review_filter_future_bars_used",
            "label_uses_future_bars",
            "not_for_live_signal",
            "future_usage_role",
        ],
        errors="ignore",
    )
    cand_path = tmp_path / "cand.csv"
    template_path = tmp_path / "template.csv"
    batch_path = tmp_path / "batch.csv"
    cand.to_csv(cand_path, index=False)
    cand.head(50).to_csv(template_path, index=False)
    cand.head(20).to_csv(batch_path, index=False)
    payload = build_validation_eurusd_candidate_audit(
        candidate_csv=cand_path,
        template_csv=template_path,
        batch_csv=batch_path,
        clean_view_csv=clean,
        rejected_csv=tmp_path / "rej.csv",
    )
    assert payload["status"] == "blocked"
