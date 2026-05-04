import json
from pathlib import Path

from cajas.reports.validation_eurusd_research_readiness import (
    build_validation_eurusd_research_readiness,
    render_validation_eurusd_research_readiness_markdown,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_readiness_ready_for_pattern_research(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
    )
    assert payload["status"] == "ready_for_pattern_research"


def test_readiness_watch_for_non_blocking_audit_watch(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "watch"}),
    )
    assert payload["status"] == "watch"


def test_readiness_with_clean_view_when_raw_blocked(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "blocked"}),
        clean_dataset_view_report=_write(
            tmp_path / "clean_view.json",
            {"status": "ready", "quarantined_row_count": 10, "output_paths": {"clean_csv": "tmp/eurusd/clean.csv"}},
        ),
    )
    assert payload["status"] == "ready_for_pattern_research_with_clean_view"
    assert payload["raw_dataset_blocked"] is True
    assert payload["clean_view_approved_for_pattern_research"] is True


def test_readiness_blocked_for_blocking_inputs(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "watch"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "blocked"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
    )
    assert payload["status"] == "blocked"
    assert payload["blocking"] is True



def test_readiness_with_batch_and_guide_ready(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
        pattern_review_qa_report=_write(tmp_path / "qa.json", {"status": "ready"}),
        pattern_label_schema_report=_write(tmp_path / "schema.json", {"status": "ready"}),
        pattern_review_template_report=_write(tmp_path / "template.json", {"status": "ready"}),
        review_batch_report=_write(tmp_path / "batch.json", {"status": "ready", "batch_row_count": 100}),
        review_guide_report=_write(tmp_path / "guide.json", {"status": "ready"}),
    )
    assert payload["next_action"] == "review_batch_001"
    assert payload["review_batch_status"] == "ready"
    assert payload["review_guide_status"] == "ready"


def test_readiness_with_awaiting_batch_completion(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
        pattern_review_qa_report=_write(tmp_path / "qa.json", {"status": "ready"}),
        pattern_label_schema_report=_write(tmp_path / "schema.json", {"status": "ready"}),
        pattern_review_template_report=_write(tmp_path / "template.json", {"status": "ready"}),
        review_batch_report=_write(tmp_path / "batch.json", {"status": "ready", "batch_row_count": 100}),
        review_guide_report=_write(tmp_path / "guide.json", {"status": "ready"}),
        review_batch_completion_report=_write(
            tmp_path / "completion.json",
            {"status": "awaiting_completed_batch", "blocking": False, "reviewed_count": 0, "pending_count": 100}
        ),
    )
    assert payload["next_action"] == "fill_batch_001_review"
    assert payload["batch_completion_status"] == "awaiting_completed_batch"


def test_readiness_blocked_on_batch_completion(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
        review_batch_completion_report=_write(tmp_path / "completion.json", {"status": "blocked"}),
    )
    assert payload["status"] == "blocked"
    assert "review_batch_completion_blocked" in payload["blocking_reasons"]


def test_readiness_markdown_policy(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
    )
    md = render_validation_eurusd_research_readiness_markdown(payload).lower()
    assert "no live trading" in md
    assert "no qlib core changes" in md



def test_readiness_with_merge_awaiting(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
        pattern_review_qa_report=_write(tmp_path / "qa.json", {"status": "ready"}),
        pattern_label_schema_report=_write(tmp_path / "schema.json", {"status": "ready"}),
        pattern_review_template_report=_write(tmp_path / "template.json", {"status": "ready"}),
        review_batch_report=_write(tmp_path / "batch.json", {"status": "ready", "batch_row_count": 100}),
        review_guide_report=_write(tmp_path / "guide.json", {"status": "ready"}),
        review_batch_merge_report=_write(
            tmp_path / "merge.json",
            {"status": "awaiting_completed_batch", "blocking": False, "reviewed_count_added": 0}
        ),
    )
    assert payload["next_action"] == "fill_batch_001_review"
    assert payload["batch_merge_status"] == "awaiting_completed_batch"


def test_readiness_with_merge_ready(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
        pattern_review_qa_report=_write(tmp_path / "qa.json", {"status": "ready"}),
        pattern_label_schema_report=_write(tmp_path / "schema.json", {"status": "ready"}),
        pattern_review_template_report=_write(tmp_path / "template.json", {"status": "ready"}),
        review_batch_report=_write(tmp_path / "batch.json", {"status": "ready", "batch_row_count": 100}),
        review_guide_report=_write(tmp_path / "guide.json", {"status": "ready"}),
        review_batch_merge_report=_write(
            tmp_path / "merge.json",
            {"status": "ready", "blocking": False, "reviewed_count_added": 10, "reviewed_count_total": 10}
        ),
    )
    assert payload["next_action"] == "regenerate_review_feedback_summary"
    assert payload["batch_merge_status"] == "ready"
    assert payload["batch_merge_reviewed_count_added"] == 10
    assert payload["batch_merge_reviewed_count_total"] == 10


def test_readiness_blocked_on_merge(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
        review_batch_merge_report=_write(tmp_path / "merge.json", {"status": "blocked"}),
    )
    assert payload["status"] == "blocked"
    assert "review_batch_merge_blocked" in payload["blocking_reasons"]


def test_readiness_markdown_policy(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
    )
    md = render_validation_eurusd_research_readiness_markdown(payload).lower()
    assert "no live trading" in md
    assert "no qlib core changes" in md


def test_readiness_includes_pattern_candidate_pack_when_provided(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "blocked"}),
        clean_dataset_view_report=_write(
            tmp_path / "clean.json",
            {"status": "ready", "quarantined_row_count": 10, "output_paths": {"clean_csv": "tmp/eurusd/clean.csv"}},
        ),
        pattern_candidate_pack_report=_write(
            tmp_path / "pack.json",
            {"status": "watch", "candidate_count": 321},
        ),
    )
    assert payload["status"] == "ready_for_pattern_research_with_clean_view"
    assert payload["pattern_candidate_pack_status"] == "watch"
    assert payload["pattern_candidate_count"] == 321
    assert payload["next_action"] == "review_pattern_samples"


def test_readiness_begin_human_pattern_review_when_review_stack_ready(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "blocked"}),
        clean_dataset_view_report=_write(
            tmp_path / "clean.json",
            {"status": "ready", "quarantined_row_count": 10, "output_paths": {"clean_csv": "tmp/eurusd/clean.csv"}},
        ),
        pattern_candidate_pack_report=_write(tmp_path / "pack.json", {"status": "ready", "candidate_count": 100}),
        pattern_review_qa_report=_write(tmp_path / "qa.json", {"status": "ready"}),
        pattern_label_schema_report=_write(tmp_path / "schema.json", {"status": "ready"}),
        pattern_review_template_report=_write(tmp_path / "template.json", {"status": "ready"}),
    )
    assert payload["status"] == "ready_for_pattern_research_with_clean_view"
    assert payload["next_action"] == "begin_human_pattern_review"


def test_readiness_with_awaiting_feedback_is_non_blocking(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "blocked"}),
        clean_dataset_view_report=_write(
            tmp_path / "clean.json",
            {"status": "ready", "quarantined_row_count": 10, "output_paths": {"clean_csv": "tmp/eurusd/clean.csv"}},
        ),
        review_feedback_report=_write(
            tmp_path / "feedback.json",
            {"status": "awaiting_review_input", "reviewed_count": 0, "pending_count": 500},
        ),
    )
    assert payload["status"] == "ready_for_pattern_research_with_clean_view"
    assert payload["next_action"] == "complete_human_review_template"


def test_readiness_blocked_when_feedback_blocked(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "blocked"}),
        clean_dataset_view_report=_write(
            tmp_path / "clean.json",
            {"status": "ready", "quarantined_row_count": 10, "output_paths": {"clean_csv": "tmp/eurusd/clean.csv"}},
        ),
        review_feedback_report=_write(
            tmp_path / "feedback.json",
            {"status": "blocked"},
        ),
    )
    assert payload["status"] == "blocked"
    assert "review_feedback_blocked" in payload["blocking_reasons"]


def test_readiness_prefers_run_local_review_app_when_gui_available(tmp_path: Path) -> None:
    payload = build_validation_eurusd_research_readiness(
        base_maintenance_continuation_report=_write(tmp_path / "base.json", {"status": "routine_continues"}),
        dataset_contract_report=_write(tmp_path / "contract.json", {"status": "ready"}),
        dataset_audit_report=_write(tmp_path / "audit.json", {"status": "ready"}),
        pattern_review_qa_report=_write(tmp_path / "qa.json", {"status": "ready"}),
        pattern_label_schema_report=_write(tmp_path / "schema.json", {"status": "ready"}),
        pattern_review_template_report=_write(tmp_path / "template.json", {"status": "ready"}),
        review_batch_report=_write(tmp_path / "batch.json", {"status": "ready", "batch_row_count": 100}),
        review_guide_report=_write(tmp_path / "guide.json", {"status": "ready"}),
        review_batch_completion_report=_write(
            tmp_path / "completion.json",
            {"status": "awaiting_completed_batch", "blocking": False, "reviewed_count": 0, "pending_count": 100},
        ),
        pattern_review_gui_report=_write(
            tmp_path / "gui.json",
            {"status": "watch", "launcher_command": "./scripts/run_eurusd_review_gui.sh"},
        ),
    )
    assert payload["pattern_review_gui_status"] == "watch"
    assert payload["next_action"] == "run_local_review_app"
    assert payload["review_app_run_command"] == "./scripts/run_eurusd_review_gui.sh"
