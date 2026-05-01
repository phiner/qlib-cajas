"""Label audit utilities for baseline readiness gating."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class LabelAuditIssue:
    severity: str
    code: str
    message: str
    label: str | None = None


@dataclass(frozen=True)
class LabelAuditReport:
    label_col: str
    expected_classes: list[str]
    observed_classes: list[str]
    distribution: dict[str, int]
    missing_count: int
    total_count: int
    issues: list[LabelAuditIssue]

    def to_dict(self) -> dict:
        out = asdict(self)
        out["issues"] = [asdict(i) for i in self.issues]
        return out


def audit_labels(
    labels: pd.Series,
    *,
    label_col: str = "future_direction_8",
    expected_classes: tuple[str, ...] = ("down", "flat", "up"),
    rare_class_min_count: int = 10,
) -> LabelAuditReport:
    series = labels.copy()
    issues: list[LabelAuditIssue] = []

    missing_count = int(series.isna().sum())
    total_count = int(len(series))
    if missing_count > 0:
        issues.append(
            LabelAuditIssue(
                severity="error",
                code="MISSING_LABELS",
                message=f"{missing_count} missing labels found",
            )
        )

    observed = sorted([str(x) for x in series.dropna().unique()])
    dist = series.value_counts(dropna=True).sort_index()
    distribution = {str(k): int(v) for k, v in dist.items()}

    expected_set = set(expected_classes)
    unknown = sorted([c for c in observed if c not in expected_set])
    for cls in unknown:
        issues.append(
            LabelAuditIssue(
                severity="error",
                code="UNKNOWN_CLASS",
                message="Unknown class found",
                label=cls,
            )
        )

    for cls in expected_classes:
        if cls not in distribution:
            severity = "warning" if total_count < 100 else "error"
            issues.append(
                LabelAuditIssue(
                    severity=severity,
                    code="EXPECTED_CLASS_MISSING",
                    message="Expected class not found in labels",
                    label=cls,
                )
            )
        elif distribution[cls] < rare_class_min_count:
            issues.append(
                LabelAuditIssue(
                    severity="warning",
                    code="RARE_CLASS",
                    message=f"Class frequency below {rare_class_min_count}",
                    label=cls,
                )
            )

    return LabelAuditReport(
        label_col=label_col,
        expected_classes=list(expected_classes),
        observed_classes=observed,
        distribution=distribution,
        missing_count=missing_count,
        total_count=total_count,
        issues=issues,
    )
