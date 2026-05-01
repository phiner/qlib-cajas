"""Reporting helpers for baseline research workflows."""

from .baseline_report_pack import BaselineReportPack, build_baseline_report_pack
from .markdown_report_exporter import (
    render_baseline_report_pack_markdown,
    render_multi_model_comparison_markdown,
    render_registry_summary_markdown,
    write_markdown_report,
)
from .dashboard_export import DashboardExportReport, export_dashboard_data
from .research_report_pack import ResearchReportPack, build_research_report_pack
from .external_holdout_benchmark import (
    BenchmarkRunSummary,
    ExternalHoldoutBenchmarkReport,
    build_external_holdout_benchmark,
)
from .research_decision_report import ResearchDecisionReport, build_research_decision_report
from .label_variant_comparison import compare_label_variant_runs, write_label_variant_comparison_artifacts
from .label_decision_report import build_label_decision_report
from .qlib_readiness_report import build_qlib_readiness_report
from .research_roadmap_report import build_research_roadmap_report

__all__ = [
    "BaselineReportPack",
    "build_baseline_report_pack",
    "write_markdown_report",
    "render_baseline_report_pack_markdown",
    "render_multi_model_comparison_markdown",
    "render_registry_summary_markdown",
    "DashboardExportReport",
    "export_dashboard_data",
    "ResearchReportPack",
    "build_research_report_pack",
    "BenchmarkRunSummary",
    "ExternalHoldoutBenchmarkReport",
    "build_external_holdout_benchmark",
    "ResearchDecisionReport",
    "build_research_decision_report",
    "compare_label_variant_runs",
    "write_label_variant_comparison_artifacts",
    "build_label_decision_report",
    "build_qlib_readiness_report",
    "build_research_roadmap_report",
]
