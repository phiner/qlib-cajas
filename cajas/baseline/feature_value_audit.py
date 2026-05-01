"""Audit feature matrices for non-finite and extreme numeric values."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureValueIssue:
    severity: str
    code: str
    message: str
    column: str | None = None
    count: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class FeatureValueAuditReport:
    row_count: int
    feature_count: int
    nan_count: int
    pos_inf_count: int
    neg_inf_count: int
    large_value_count: int
    max_abs_value: float | None
    columns_with_issues: list[str]
    issues: list[FeatureValueIssue]

    def to_dict(self) -> dict:
        return {
            "row_count": self.row_count,
            "feature_count": self.feature_count,
            "nan_count": self.nan_count,
            "pos_inf_count": self.pos_inf_count,
            "neg_inf_count": self.neg_inf_count,
            "large_value_count": self.large_value_count,
            "max_abs_value": self.max_abs_value,
            "columns_with_issues": self.columns_with_issues,
            "issues": [i.to_dict() for i in self.issues],
        }


def audit_feature_values(
    features_df,
    *,
    large_value_threshold: float = 1e12,
) -> FeatureValueAuditReport:
    df = pd.DataFrame(features_df).copy()
    numeric = df.apply(pd.to_numeric, errors="coerce")

    values = numeric.to_numpy(dtype=float)
    finite_mask = np.isfinite(values)
    nan_mask = np.isnan(values)
    pos_inf_mask = np.isposinf(values)
    neg_inf_mask = np.isneginf(values)
    large_mask = np.isfinite(values) & (np.abs(values) > float(large_value_threshold))

    nan_count = int(nan_mask.sum())
    pos_inf_count = int(pos_inf_mask.sum())
    neg_inf_count = int(neg_inf_mask.sum())
    large_value_count = int(large_mask.sum())

    max_abs = None
    if values.size > 0 and bool(finite_mask.any()):
        max_abs = float(np.nanmax(np.abs(values[finite_mask])))

    issues: list[FeatureValueIssue] = []
    issue_cols: set[str] = set()

    if nan_count > 0:
        sev = "warning" if nan_count <= max(10, int(values.size * 0.01)) else "error"
        issues.append(FeatureValueIssue(severity=sev, code="nan_values", message=f"NaN values found: {nan_count}", count=nan_count))
    if pos_inf_count > 0:
        issues.append(FeatureValueIssue(severity="error", code="pos_inf_values", message=f"+inf values found: {pos_inf_count}", count=pos_inf_count))
    if neg_inf_count > 0:
        issues.append(FeatureValueIssue(severity="error", code="neg_inf_values", message=f"-inf values found: {neg_inf_count}", count=neg_inf_count))
    if large_value_count > 0:
        sev = "warning" if large_value_count <= max(10, int(values.size * 0.001)) else "error"
        issues.append(
            FeatureValueIssue(
                severity=sev,
                code="extreme_values",
                message=f"Values above abs({large_value_threshold}) found: {large_value_count}",
                count=large_value_count,
            )
        )

    for col in numeric.columns:
        col_values = numeric[col].to_numpy(dtype=float)
        c_nan = int(np.isnan(col_values).sum())
        c_inf = int(np.isinf(col_values).sum())
        c_large = int((np.isfinite(col_values) & (np.abs(col_values) > float(large_value_threshold))).sum())
        total = int(len(col_values))
        bad = c_nan + c_inf
        if bad > 0:
            issue_cols.add(str(col))
            if total > 0 and (bad / total) >= 0.2:
                issues.append(
                    FeatureValueIssue(
                        severity="warning",
                        code="column_non_finite_ratio_high",
                        message=f"Column has high non-finite ratio: {bad}/{total}",
                        column=str(col),
                        count=bad,
                    )
                )
        if c_large > 0:
            issue_cols.add(str(col))

    return FeatureValueAuditReport(
        row_count=int(df.shape[0]),
        feature_count=int(df.shape[1]),
        nan_count=nan_count,
        pos_inf_count=pos_inf_count,
        neg_inf_count=neg_inf_count,
        large_value_count=large_value_count,
        max_abs_value=max_abs,
        columns_with_issues=sorted(issue_cols),
        issues=issues,
    )
