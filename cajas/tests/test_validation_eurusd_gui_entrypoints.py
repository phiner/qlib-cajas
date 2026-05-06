"""Tests for EURUSD GUI entrypoint disambiguation report."""

from __future__ import annotations

import json
from pathlib import Path

from cajas.reports.validation_eurusd_gui_entrypoints import build_eurusd_gui_entrypoints_report


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_gui_entrypoints_clear(tmp_path: Path) -> None:
    pattern_launcher = _write(
        tmp_path / "run_eurusd_review_gui.sh",
        '#!/usr/bin/env bash\nAPP_PATH="cajas/apps/eurusd_pattern_review_app.py"\n./.venv-qlib313/bin/python -m streamlit run "${APP_PATH}"\n',
    )
    pattern_app = _write(
        tmp_path / "eurusd_pattern_review_app.py",
        "\n".join(
            [
                "EURUSD Pattern Review / EURUSD 形态审核",
                "final sample-level labels · CSV/JSONL persistence · no LLM · no trading",
                "Overall Human Review / 总体人工审核",
                "human_label",
                "human_confidence",
            ]
        ),
    )
    market_state_launcher = _write(
        tmp_path / "run_eurusd_market_state_inspection_gui.sh",
        "./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_market_state_inspection_app.py\n",
    )
    market_state_app = _write(
        tmp_path / "eurusd_market_state_inspection_app.py",
        "\n".join(
            [
                "EURUSD 四层市场状态图表审阅",
                "layer feedback only unless explicitly wired to final review",
                'st.tabs(["P3", "M8", "M24", "M128", "Local", "Notes"])',
                "P3/M8/M24/M128/Local are layer evidence fields.",
                "Local = immediate local structure around the target candle.",
                "These fields support review reasoning but do not replace the final sample-level human_label in the Pattern Review GUI.",
            ]
        ),
    )
    kickoff_doc = _write(
        tmp_path / "kickoff.md",
        "\n".join(
            [
                "Use Pattern Review GUI for final human sample review.",
                "Use Market-State Inspection GUI only for layer/state inspection unless explicitly stated.",
                "human_label belongs to final sample-level review.",
                "P3/M8/M24/M128/Local are evidence layers.",
                "./scripts/run_eurusd_review_gui.sh",
                "./scripts/run_eurusd_market_state_inspection_gui.sh",
            ]
        ),
    )
    roadmap_doc = _write(tmp_path / "roadmap.md", kickoff_doc.read_text(encoding="utf-8"))
    trial = _write(tmp_path / "trial.json", json.dumps({"status": "not_approved"}))

    report = build_eurusd_gui_entrypoints_report(
        pattern_launcher=pattern_launcher,
        pattern_app=pattern_app,
        market_state_launcher=market_state_launcher,
        market_state_app=market_state_app,
        kickoff_doc=kickoff_doc,
        roadmap_doc=roadmap_doc,
        trial_approval_json=trial,
    )
    assert report["report_status"] == "gui_entrypoints_clear"
    assert report["pattern_review_command"] == "./scripts/run_eurusd_review_gui.sh"
    assert report["pattern_review_has_final_human_label"] is True
    assert report["market_state_has_layer_tabs"] is True
    assert report["market_state_local_explained"] is True
    assert report["apps_have_distinct_titles"] is True
    assert report["docs_disambiguate_apps"] is True
    assert report["trial_approval_status"] == "not_approved"


def test_gui_entrypoints_blocked_when_docs_do_not_disambiguate(tmp_path: Path) -> None:
    pattern_launcher = _write(tmp_path / "pattern.sh", 'APP_PATH="cajas/apps/eurusd_pattern_review_app.py"\n')
    pattern_app = _write(tmp_path / "pattern.py", "EURUSD Pattern Review / EURUSD 形态审核\nhuman_label\nhuman_confidence\n")
    market_state_launcher = _write(tmp_path / "market.sh", "cajas/apps/eurusd_market_state_inspection_app.py\n")
    market_state_app = _write(
        tmp_path / "market.py",
        'st.tabs(["P3", "M8", "M24", "M128", "Local", "Notes"])\nlayer feedback only unless explicitly wired to final review\nP3/M8/M24/M128/Local are layer evidence fields.\nLocal = immediate local structure around the target candle.\nThese fields support review reasoning but do not replace the final sample-level human_label in the Pattern Review GUI.\n',
    )
    kickoff_doc = _write(tmp_path / "kickoff.md", "missing disambiguation")
    roadmap_doc = _write(tmp_path / "roadmap.md", "missing disambiguation")
    trial = _write(tmp_path / "trial.json", json.dumps({"status": "not_approved"}))

    report = build_eurusd_gui_entrypoints_report(
        pattern_launcher=pattern_launcher,
        pattern_app=pattern_app,
        market_state_launcher=market_state_launcher,
        market_state_app=market_state_app,
        kickoff_doc=kickoff_doc,
        roadmap_doc=roadmap_doc,
        trial_approval_json=trial,
    )
    assert report["report_status"] == "blocked"
    assert "docs_do_not_disambiguate_apps" in report["blocking_reasons"]
