"""Build conservative research gate packet from model bridge artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .research_gate_schema import BlockedAction, GateCheckResult, ManualReviewItem, ResearchGatePacket


def _exists_check(name: str, path: str | Path, required: bool) -> dict:
    p = Path(path).expanduser().resolve()
    ok = p.exists()
    return {
        "name": name,
        "path": str(p),
        "required": required,
        "exists": ok,
        "decision": "pass" if ok else ("fail" if required else "warn"),
    }


def build_research_gate_packet(
    *,
    contract_path: str | Path,
    experiment_dir: str | Path,
    registry_path: str | Path | None = None,
    comparison_path: str | Path | None = None,
    handler_smoke_report_path: str | Path | None = None,
    compatibility_report_path: str | Path | None = None,
    research_decision_packet_path: str | Path | None = None,
    min_macro_f1: float = 0.20,
    min_accuracy: float = 0.20,
) -> dict:
    exp = Path(experiment_dir).expanduser().resolve()
    source_paths = {
        "contract": str(Path(contract_path).expanduser().resolve()),
        "experiment_dir": str(exp),
        "registry": "" if registry_path is None else str(Path(registry_path).expanduser().resolve()),
        "comparison": "" if comparison_path is None else str(Path(comparison_path).expanduser().resolve()),
        "handler_smoke_report": "" if handler_smoke_report_path is None else str(Path(handler_smoke_report_path).expanduser().resolve()),
        "compatibility_report": "" if compatibility_report_path is None else str(Path(compatibility_report_path).expanduser().resolve()),
        "research_decision_packet": "" if research_decision_packet_path is None else str(Path(research_decision_packet_path).expanduser().resolve()),
    }

    artifact_checks = [
        _exists_check("contract", source_paths["contract"], True),
        _exists_check("experiment_manifest", exp / "experiment_manifest.json", True),
        _exists_check("metrics", exp / "metrics.json", True),
        _exists_check("predictions", exp / "predictions.csv", True),
        _exists_check("split_summary", exp / "split_summary.json", True),
    ]
    if source_paths["registry"]:
        artifact_checks.append(_exists_check("registry", source_paths["registry"], True))
    if source_paths["comparison"]:
        artifact_checks.append(_exists_check("comparison", source_paths["comparison"], True))
    if source_paths["handler_smoke_report"]:
        artifact_checks.append(_exists_check("handler_smoke_report", source_paths["handler_smoke_report"], False))
    if source_paths["compatibility_report"]:
        artifact_checks.append(_exists_check("compatibility_report", source_paths["compatibility_report"], False))
    if source_paths["research_decision_packet"]:
        artifact_checks.append(_exists_check("research_decision_packet", source_paths["research_decision_packet"], False))

    checks: list[GateCheckResult] = []

    missing_required = [c for c in artifact_checks if c["required"] and not c["exists"]]
    if missing_required:
        checks.append(GateCheckResult("required_artifacts", "blocked", "required artifacts missing", "error"))

    metric_summary = {"accuracy": None, "macro_f1": None}
    if (exp / "metrics.json").exists():
        metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8"))
        accuracy = metrics.get("valid", {}).get("accuracy")
        macro_f1 = metrics.get("valid", {}).get("macro_f1")
        metric_summary = {"accuracy": accuracy, "macro_f1": macro_f1}

        if accuracy is None or macro_f1 is None:
            checks.append(GateCheckResult("metrics_presence", "fail", "required metric values missing", "error"))
        else:
            if float(macro_f1) < min_macro_f1:
                checks.append(GateCheckResult("macro_f1_threshold", "fail", f"macro_f1 below threshold ({macro_f1} < {min_macro_f1})", "error"))
            else:
                checks.append(GateCheckResult("macro_f1_threshold", "pass", "macro_f1 threshold met", "info"))
            if float(accuracy) < min_accuracy:
                checks.append(GateCheckResult("accuracy_threshold", "fail", f"accuracy below threshold ({accuracy} < {min_accuracy})", "error"))
            else:
                checks.append(GateCheckResult("accuracy_threshold", "pass", "accuracy threshold met", "info"))
    else:
        checks.append(GateCheckResult("metrics_presence", "fail", "metrics.json missing", "error"))

    if (exp / "predictions.csv").exists():
        # Count-only: avoid full read for large prediction artifacts
        pred_rows = sum(1 for _ in open(exp / "predictions.csv", encoding="utf-8")) - 1  # subtract header
        if pred_rows <= 0:
            checks.append(GateCheckResult("prediction_rows", "fail", "predictions are empty", "error"))
        else:
            checks.append(GateCheckResult("prediction_rows", "pass", f"predictions rows: {pred_rows}", "info"))

    if (exp / "split_summary.json").exists():
        ss = json.loads((exp / "split_summary.json").read_text(encoding="utf-8"))
        if min(int(ss.get("train", 0)), int(ss.get("valid", 0)), int(ss.get("test", 0))) <= 0:
            checks.append(GateCheckResult("split_quality", "fail", "train/valid/test contains zero rows", "error"))
        else:
            checks.append(GateCheckResult("split_quality", "pass", "train/valid/test split non-empty", "info"))

    if source_paths["registry"] and Path(source_paths["registry"]).exists():
        with Path(source_paths["registry"]).open("r", encoding="utf-8") as f:
            rows = [line for line in f.read().splitlines() if line.strip()]
        if len(rows) == 0:
            checks.append(GateCheckResult("registry_records", "fail", "registry has no records", "error"))
        else:
            checks.append(GateCheckResult("registry_records", "pass", f"registry records: {len(rows)}", "info"))

    if source_paths["comparison"] and Path(source_paths["comparison"]).exists():
        comp = json.loads(Path(source_paths["comparison"]).read_text(encoding="utf-8"))
        ranked = comp.get("ranked_runs", [])
        if not ranked:
            checks.append(GateCheckResult("comparison_top_run", "fail", "comparison has no ranked runs", "error"))
        else:
            checks.append(GateCheckResult("comparison_top_run", "pass", "comparison contains ranked runs", "info"))

    blocked_actions = [
        BlockedAction("broker_connection", "phase 096-105 forbids broker integration").to_dict(),
        BlockedAction("order_routing", "phase 096-105 forbids order submission").to_dict(),
        BlockedAction("live_market_data", "phase 096-105 is offline only").to_dict(),
        BlockedAction("paper_trading_execution", "phase 096-105 forbids execution simulation with orders").to_dict(),
        BlockedAction("portfolio_sizing", "phase 096-105 forbids portfolio optimization").to_dict(),
        BlockedAction("pnl_optimization", "phase 096-105 forbids PnL-driven optimization").to_dict(),
    ]

    manual_review = [
        ManualReviewItem("Review threshold failures", "Metrics are research-only and weak thresholds may still fail in smoke.").to_dict(),
        ManualReviewItem("Verify artifact lineage", "Ensure contract, experiment, registry, and comparison artifacts are consistent.").to_dict(),
    ]

    decisions = [c.decision for c in checks] + [c["decision"] for c in artifact_checks]
    if "blocked" in decisions:
        final = "blocked"
    elif "fail" in decisions:
        final = "blocked"
    elif "warn" in decisions:
        final = "needs_manual_review"
    else:
        final = "offline_review_ready"

    packet = ResearchGatePacket(
        schema_version="v1",
        source_artifact_paths=source_paths,
        artifact_checks=artifact_checks,
        metric_summary=metric_summary,
        checks=[c.to_dict() for c in checks],
        manual_review_checklist=manual_review,
        blocked_actions=blocked_actions,
        final_status=final,
        notes=["Research-only gate. Blocked status is data, not CLI failure."],
    )
    return packet.to_dict()
