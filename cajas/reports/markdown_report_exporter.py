"""Export compact markdown summaries from report payloads."""

from __future__ import annotations

from pathlib import Path


def write_markdown_report(
    *,
    output_path: str | Path,
    title: str,
    sections: list[tuple[str, str]],
) -> str:
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.append(f"## {heading}")
        lines.append(body.strip())
        lines.append("")
    text = "\n".join(lines).strip() + "\n"
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


def render_baseline_report_pack_markdown(report: dict) -> str:
    valid = report.get("valid_metrics", {})
    test = report.get("test_metrics", {})
    body = (
        f"Run: `{report.get('run_name')}`\n\n"
        f"Model family: `{report.get('model_family')}`\n\n"
        f"Target label: `{report.get('target_label')}`\n\n"
        f"Valid accuracy: `{valid.get('accuracy')}`\n\n"
        f"Test accuracy: `{test.get('accuracy')}`\n\n"
        "Classification-only summary. No trading/backtest/profit analysis."
    )
    return body


def render_multi_model_comparison_markdown(report: dict) -> str:
    rows = report.get("comparison", {}).get("rows", [])
    lines = [
        f"Run: `{report.get('run_name')}`",
        f"Primary metric: `{report.get('primary_metric')}`",
        f"Best model: `{report.get('best_model_by_primary_metric')}`",
        "",
        "| Model | test_macro_f1 | test_accuracy |",
        "|---|---:|---:|",
    ]
    for row in rows:
        m = row.get("metrics", {})
        lines.append(f"| {row.get('model_family_used')} | {m.get('test_macro_f1')} | {m.get('test_accuracy')} |")
    lines.append("")
    lines.append("Classification-only comparison. No trading/backtest/profit analysis.")
    return "\n".join(lines)


def render_registry_summary_markdown(report: dict) -> str:
    return (
        f"Registry: `{report.get('registry_path')}`\n\n"
        f"Total records: `{report.get('total_records')}`\n\n"
        f"Training runs: `{len(report.get('training_runs', []))}`\n\n"
        "Local registry summary only. No trading/backtest/profit analysis."
    )
