"""Schema for the phase 56-65 research decision packet."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

DECISION_VALUES = {
    "reject",
    "needs_more_data",
    "needs_label_redesign",
    "needs_feature_redesign",
    "candidate_for_qlib_trial",
}

CONFIDENCE_VALUES = {"low", "medium", "high"}


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ResearchDecisionInput:
    run_id: str
    created_at_utc: str
    label_variant_summary_path: str
    feature_set_summary_path: str
    calibration_summary_path: str
    seed_stability_summary_path: str
    rolling_validation_plan_path: str
    error_slice_summary_path: str
    leakage_drift_audit_path: str
    qlib_readiness_report_path: str
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResearchDecisionFinding:
    severity: str
    code: str
    message: str
    source_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResearchDecisionRecommendation:
    priority: str
    action: str
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResearchDecisionResult:
    run_id: str
    created_at_utc: str
    label_variant_summary_path: str
    feature_set_summary_path: str
    calibration_summary_path: str
    seed_stability_summary_path: str
    rolling_validation_plan_path: str
    error_slice_summary_path: str
    leakage_drift_audit_path: str
    qlib_readiness_report_path: str
    final_decision: str
    confidence_level: str
    blocking_findings: list[ResearchDecisionFinding] = field(default_factory=list)
    non_blocking_findings: list[ResearchDecisionFinding] = field(default_factory=list)
    recommended_next_actions: list[ResearchDecisionRecommendation] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        if self.final_decision not in DECISION_VALUES:
            raise ValueError(f"invalid decision: {self.final_decision}")
        if self.confidence_level not in CONFIDENCE_VALUES:
            raise ValueError(f"invalid confidence: {self.confidence_level}")
        data = asdict(self)
        return data

