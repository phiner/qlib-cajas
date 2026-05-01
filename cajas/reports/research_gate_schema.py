"""Schema types for research gate packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class GateCheckResult:
    name: str
    decision: str
    message: str
    severity: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ManualReviewItem:
    item: str
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BlockedAction:
    action: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResearchGatePacket:
    schema_version: str
    source_artifact_paths: dict
    artifact_checks: list[dict]
    metric_summary: dict
    checks: list[dict]
    manual_review_checklist: list[dict]
    blocked_actions: list[dict]
    final_status: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
