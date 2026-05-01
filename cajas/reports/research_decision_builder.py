"""Build conservative research decision packets from existing report artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from .research_decision_schema import (
    ResearchDecisionFinding,
    ResearchDecisionInput,
    ResearchDecisionRecommendation,
    ResearchDecisionResult,
    utc_now_iso,
)


def _load_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"missing file: {path}"
    except json.JSONDecodeError as exc:
        return None, f"malformed json at {path}: {exc}"


def _find_first(base: Path, names: list[str]) -> str:
    for n in names:
        p = base / n
        if p.exists():
            return str(p)
    return str(base / names[0])


def build_research_decision(
    *,
    reports_dir: str | Path,
    run_id: str,
    notes: str = "",
    severe_drift_threshold: float = 0.35,
    unstable_seed_std_threshold: float = 0.03,
    poor_calibration_threshold: float = 0.06,
) -> ResearchDecisionResult:
    base = Path(reports_dir).expanduser().resolve()
    decision_input = ResearchDecisionInput(
        run_id=run_id,
        created_at_utc=utc_now_iso(),
        label_variant_summary_path=_find_first(base, ["label_variant_comparison_report.json"]),
        feature_set_summary_path=_find_first(base, ["feature_set_comparison_report.json"]),
        calibration_summary_path=_find_first(base, ["calibration_analysis_report.json"]),
        seed_stability_summary_path=_find_first(base, ["seed_stability_report.json"]),
        rolling_validation_plan_path=_find_first(base, ["rolling_year_validation_plan.json"]),
        error_slice_summary_path=_find_first(base, ["error_slice_analysis_report.json"]),
        leakage_drift_audit_path=_find_first(base, ["leakage_drift_audit_report.json"]),
        qlib_readiness_report_path=_find_first(base, ["qlib_readiness_report.json"]),
        notes=notes,
    )
    blocking: list[ResearchDecisionFinding] = []
    non_blocking: list[ResearchDecisionFinding] = []
    actions: list[ResearchDecisionRecommendation] = []
    decision = "candidate_for_qlib_trial"
    confidence = "high"

    def add_block(code: str, msg: str, source_path: str) -> None:
        blocking.append(ResearchDecisionFinding(severity="blocking", code=code, message=msg, source_path=source_path))

    leakage, err = _load_json(Path(decision_input.leakage_drift_audit_path))
    if err:
        add_block("missing_or_malformed_leakage_drift", err, decision_input.leakage_drift_audit_path)
    else:
        if leakage.get("forbidden_feature_columns_count", 0) > 0:
            decision = "needs_feature_redesign"
            add_block("forbidden_feature_columns", "forbidden/leakage columns found in feature set", decision_input.leakage_drift_audit_path)
        if float(leakage.get("drift_score_max", 0.0)) >= severe_drift_threshold:
            decision = "needs_feature_redesign"
            non_blocking.append(ResearchDecisionFinding("warning", "severe_drift", "feature drift is high between train and holdout", decision_input.leakage_drift_audit_path))
            actions.append(ResearchDecisionRecommendation("high", "revisit feature set", "drift score indicates unstable distribution shift"))

    label_comp, err = _load_json(Path(decision_input.label_variant_summary_path))
    if err:
        add_block("missing_or_malformed_label_summary", err, decision_input.label_variant_summary_path)
    else:
        run_count = int(label_comp.get("run_count", 0))
        if run_count <= 0:
            decision = "needs_label_redesign"
            add_block("no_label_runs", "no label variant runs found", decision_input.label_variant_summary_path)

    feature_comp, err = _load_json(Path(decision_input.feature_set_summary_path))
    if err:
        add_block("missing_or_malformed_feature_summary", err, decision_input.feature_set_summary_path)
    else:
        if int(feature_comp.get("run_count", 0)) <= 0:
            decision = "needs_feature_redesign"
            add_block("no_feature_runs", "no feature-set runs found", decision_input.feature_set_summary_path)

    calibration, err = _load_json(Path(decision_input.calibration_summary_path))
    if err:
        non_blocking.append(ResearchDecisionFinding("warning", "missing_calibration", err, decision_input.calibration_summary_path))
        confidence = "medium"
    else:
        ece = float(calibration.get("ece_like", 0.0))
        if ece > poor_calibration_threshold:
            if decision == "candidate_for_qlib_trial":
                decision = "needs_feature_redesign"
            non_blocking.append(ResearchDecisionFinding("warning", "poor_calibration", f"ece_like={ece} is above threshold", decision_input.calibration_summary_path))

    stability, err = _load_json(Path(decision_input.seed_stability_summary_path))
    if err:
        non_blocking.append(ResearchDecisionFinding("warning", "missing_stability", err, decision_input.seed_stability_summary_path))
        confidence = "medium"
    else:
        std_val = float(stability.get("macro_f1_std", 0.0))
        if std_val > unstable_seed_std_threshold:
            if decision == "candidate_for_qlib_trial":
                decision = "needs_more_data"
            non_blocking.append(ResearchDecisionFinding("warning", "unstable_seed_behavior", f"macro_f1_std={std_val} exceeds threshold", decision_input.seed_stability_summary_path))

    readiness, err = _load_json(Path(decision_input.qlib_readiness_report_path))
    if err:
        add_block("missing_or_malformed_qlib_readiness", err, decision_input.qlib_readiness_report_path)
    else:
        if readiness.get("unresolved_blockers"):
            if decision == "candidate_for_qlib_trial":
                decision = "needs_more_data"
            non_blocking.append(ResearchDecisionFinding("warning", "readiness_blockers", "qlib readiness report still has unresolved blockers", decision_input.qlib_readiness_report_path))

    for required in [
        decision_input.rolling_validation_plan_path,
        decision_input.error_slice_summary_path,
    ]:
        p = Path(required)
        if not p.exists():
            add_block("missing_required_artifact", f"required artifact missing: {p.name}", required)

    if blocking:
        if decision == "candidate_for_qlib_trial":
            decision = "reject"
        confidence = "low"
        actions.append(ResearchDecisionRecommendation("high", "fix blocking findings", "decision cannot proceed until required artifacts and checks are healthy"))
    elif decision != "candidate_for_qlib_trial" and confidence == "high":
        confidence = "medium"

    if not actions:
        actions.append(
            ResearchDecisionRecommendation(
                "normal",
                "prepare controlled manual review",
                "artifacts are consistent enough for conservative next-step review",
            )
        )

    return ResearchDecisionResult(
        run_id=decision_input.run_id,
        created_at_utc=decision_input.created_at_utc,
        label_variant_summary_path=decision_input.label_variant_summary_path,
        feature_set_summary_path=decision_input.feature_set_summary_path,
        calibration_summary_path=decision_input.calibration_summary_path,
        seed_stability_summary_path=decision_input.seed_stability_summary_path,
        rolling_validation_plan_path=decision_input.rolling_validation_plan_path,
        error_slice_summary_path=decision_input.error_slice_summary_path,
        leakage_drift_audit_path=decision_input.leakage_drift_audit_path,
        qlib_readiness_report_path=decision_input.qlib_readiness_report_path,
        final_decision=decision,
        confidence_level=confidence,
        blocking_findings=blocking,
        non_blocking_findings=non_blocking,
        recommended_next_actions=actions,
        notes=notes,
    )

