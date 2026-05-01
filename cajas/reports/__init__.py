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
from .research_decision_schema import (
    ResearchDecisionInput,
    ResearchDecisionFinding,
    ResearchDecisionRecommendation,
    ResearchDecisionResult,
)
from .research_decision_builder import build_research_decision
from .candidate_promotion_manifest import build_candidate_promotion_manifest
from .research_report_index import build_research_report_index
from .qlib_adapter_contract import QlibAdapterContract, ContractIssue, validate_qlib_adapter_contract
from .qlib_adapter_contract_builder import build_qlib_adapter_contract
from .qlib_integration_packet import build_qlib_integration_packet
from .qlib_compatibility_report import build_qlib_compatibility_report
from .qlib_dataset_contract import QlibDatasetContract, DatasetContractIssue
from .qlib_dataset_contract_builder import build_qlib_dataset_contract
from .qlib_handler_input_builder import build_qlib_handler_input
from .qlib_handler_smoke_validator import validate_qlib_handler_input
from .qlib_model_training_contract import QlibModelTrainingContract, ModelContractIssue
from .qlib_model_training_contract_builder import build_qlib_model_training_contract
from .qlib_experiment_artifacts import write_experiment_artifacts
from .qlib_model_metrics import compute_classification_metrics
from .qlib_model_run_registry import register_qlib_model_run, load_qlib_model_registry
from .qlib_model_run_comparison import build_qlib_model_run_comparison
from .research_gate_builder import build_research_gate_packet
from .research_gate_schema import ResearchGatePacket, GateCheckResult, ManualReviewItem, BlockedAction
from .no_broker_dry_run_packet import build_no_broker_dry_run_packet
from .research_gate_summary import render_research_gate_summary
from .research_pipeline_manifest import build_research_pipeline_manifest
from .reproducibility_check import build_reproducibility_report
from .ci_validation_plan import build_ci_validation_plan
from .final_readiness_packet import build_final_readiness_packet
from .final_readiness_summary import render_final_readiness_summary
from .artifact_normalizer import normalize_json_artifact, normalize_markdown_artifact
from .stable_fingerprint import build_stable_fingerprint
from .stable_reproducibility_check import build_stable_reproducibility_report
from .artifact_lineage import build_artifact_lineage, render_artifact_lineage_md
from .research_run_catalog import build_research_run_catalog, render_research_run_catalog_md
from .offline_review_packet import build_offline_review_packet, render_offline_review_packet_md
from .final_research_bundle import build_final_research_bundle, render_final_research_bundle_md

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
    "ResearchDecisionInput",
    "ResearchDecisionFinding",
    "ResearchDecisionRecommendation",
    "ResearchDecisionResult",
    "build_research_decision",
    "build_candidate_promotion_manifest",
    "build_research_report_index",
    "QlibAdapterContract",
    "ContractIssue",
    "validate_qlib_adapter_contract",
    "build_qlib_adapter_contract",
    "build_qlib_integration_packet",
    "build_qlib_compatibility_report",
    "QlibDatasetContract",
    "DatasetContractIssue",
    "build_qlib_dataset_contract",
    "build_qlib_handler_input",
    "validate_qlib_handler_input",
    "QlibModelTrainingContract",
    "ModelContractIssue",
    "build_qlib_model_training_contract",
    "write_experiment_artifacts",
    "compute_classification_metrics",
    "register_qlib_model_run",
    "load_qlib_model_registry",
    "build_qlib_model_run_comparison",
    "build_research_gate_packet",
    "ResearchGatePacket",
    "GateCheckResult",
    "ManualReviewItem",
    "BlockedAction",
    "build_no_broker_dry_run_packet",
    "render_research_gate_summary",
    "build_research_pipeline_manifest",
    "build_reproducibility_report",
    "build_ci_validation_plan",
    "build_final_readiness_packet",
    "render_final_readiness_summary",
    "normalize_json_artifact",
    "normalize_markdown_artifact",
    "build_stable_fingerprint",
    "build_stable_reproducibility_report",
    "build_artifact_lineage",
    "render_artifact_lineage_md",
    "build_research_run_catalog",
    "render_research_run_catalog_md",
    "build_offline_review_packet",
    "render_offline_review_packet_md",
    "build_final_research_bundle",
    "render_final_research_bundle_md",
]
