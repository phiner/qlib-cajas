from __future__ import annotations

from pathlib import Path

import pandas as pd

from cajas.reports.validation_eurusd_micro_pattern_manual_labels import build_micro_pattern_manual_labels_report


def test_manual_labels_defaults_to_awaiting(tmp_path: Path) -> None:
    packet = tmp_path / "packet.csv"
    pd.DataFrame([{"sample_id": "a", "micro_pattern_event_3": "micro_noise"}]).to_csv(packet, index=False)
    completed = tmp_path / "completed.csv"
    report = build_micro_pattern_manual_labels_report(packet_csv=packet, completed_labels_csv=completed, output_template_csv=completed)
    assert report["report_status"] == "awaiting_manual_micro_pattern_labels"
    assert completed.exists()
