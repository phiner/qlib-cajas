import json
from pathlib import Path

from cajas.scripts.build_eurusd_candidate_audit_warning_inventory import build_warning_inventory
from cajas.scripts.build_eurusd_candidate_hardening_roadmap import build_roadmap


def test_warning_inventory_builds_classifications() -> None:
    payload = {
        "status": "needs_rule_refinement",
        "causality_summary": {"missing_causality_columns": [], "candidate_logic_uses_future_bars_true_count": 0},
        "selection_explainability_summary": {"missing_selection_reason": 2, "trend_missing_segment_metadata": 1},
        "multi_label_summary": {"timestamps_with_multiple_candidate_types": 10},
        "duplicate_region_summary": {"same_region_duplicates": 3},
        "audit_gates": {"should_fix_failures": ["coverage_imbalance_detected"]},
        "batch_quality_metrics": {"coverage_warnings": ["year_over_concentrated"]},
    }
    inv = build_warning_inventory(payload)
    assert inv["warning_count"] >= 4
    assert "must_fix_now" in inv["warning_count_by_classification"]


def test_hardening_roadmap_builds_sections(tmp_path: Path) -> None:
    audit = {"status": "watch", "next_actions": ["tighten_same_region_sampling"]}
    inv = {"warnings": [{"warning_id": "x", "classification": "acceptable_watch"}]}
    out = build_roadmap(audit, inv)
    assert out["status"] == "watch"
    assert "architecture_boundaries" in out
    assert "recommended_next_phases" in out
    p = tmp_path / "roadmap.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    assert p.exists()
