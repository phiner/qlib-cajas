"""Feature audit utilities for baseline readiness gating."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd
from pandas.api.types import is_numeric_dtype


@dataclass(frozen=True)
class FeatureAuditIssue:
    severity: str
    code: str
    message: str
    column: str | None = None


@dataclass(frozen=True)
class FeatureAuditReport:
    feature_count: int
    feature_columns: list[str]
    leakage_columns_declared: list[str]
    leakage_columns_found: list[str]
    non_numeric_features: list[str]
    all_null_features: list[str]
    constant_features: list[str]
    missing_value_counts: dict[str, int]
    missing_value_ratios: dict[str, float]
    top_missing_features: list[dict[str, object]]
    issues: list[FeatureAuditIssue]

    def to_dict(self) -> dict:
        out = asdict(self)
        out["issues"] = [asdict(i) for i in self.issues]
        return out


def audit_features(
    features_df: pd.DataFrame,
    *,
    declared_leakage_columns: list[str] | tuple[str, ...],
    top_n_missing: int = 10,
) -> FeatureAuditReport:
    df = features_df.copy()
    issues: list[FeatureAuditIssue] = []
    feature_columns = list(df.columns)

    if not feature_columns:
        issues.append(
            FeatureAuditIssue(
                severity="error",
                code="NO_FEATURES",
                message="No feature columns found",
            )
        )

    leakage_set = set(declared_leakage_columns)
    leakage_found = sorted([c for c in feature_columns if c in leakage_set])
    for col in leakage_found:
        issues.append(
            FeatureAuditIssue(
                severity="error",
                code="LEAKAGE_COLUMN_FOUND",
                message="Declared leakage column found in features",
                column=col,
            )
        )

    non_numeric = sorted([c for c in feature_columns if not is_numeric_dtype(df[c])])
    for col in non_numeric:
        issues.append(
            FeatureAuditIssue(
                severity="error",
                code="NON_NUMERIC_FEATURE",
                message="Feature column is non-numeric",
                column=col,
            )
        )

    all_null = sorted([c for c in feature_columns if int(df[c].isna().sum()) == len(df)])
    for col in all_null:
        issues.append(
            FeatureAuditIssue(
                severity="error",
                code="ALL_NULL_FEATURE",
                message="Feature column contains only null values",
                column=col,
            )
        )

    constant: list[str] = []
    for col in feature_columns:
        if col in all_null:
            continue
        if df[col].nunique(dropna=True) <= 1:
            constant.append(col)
            issues.append(
                FeatureAuditIssue(
                    severity="warning",
                    code="CONSTANT_FEATURE",
                    message="Feature column is constant",
                    column=col,
                )
            )

    row_count = len(df)
    missing_counts = {c: int(df[c].isna().sum()) for c in feature_columns}
    missing_ratios = {
        c: (float(missing_counts[c]) / float(row_count) if row_count > 0 else 0.0)
        for c in feature_columns
    }
    for col, count in missing_counts.items():
        if count > 0 and col not in all_null:
            issues.append(
                FeatureAuditIssue(
                    severity="warning",
                    code="MISSING_VALUES",
                    message=f"Feature column has {count} missing values",
                    column=col,
                )
            )

    top_missing = sorted(
        [
            {
                "column": col,
                "missing_count": missing_counts[col],
                "missing_ratio": missing_ratios[col],
            }
            for col in feature_columns
            if missing_counts[col] > 0
        ],
        key=lambda x: (-int(x["missing_count"]), str(x["column"])),
    )[:top_n_missing]

    return FeatureAuditReport(
        feature_count=len(feature_columns),
        feature_columns=feature_columns,
        leakage_columns_declared=list(declared_leakage_columns),
        leakage_columns_found=leakage_found,
        non_numeric_features=non_numeric,
        all_null_features=all_null,
        constant_features=sorted(constant),
        missing_value_counts=missing_counts,
        missing_value_ratios=missing_ratios,
        top_missing_features=top_missing,
        issues=issues,
    )
