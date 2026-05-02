from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cajas.reports.validation_delivery_packet import (
    build_validation_delivery_packet,
    generate_packet_index_markdown,
)
from cajas.scripts.build_validation_delivery_packet import main as build_packet_main


class ValidationDeliveryPacketTests(unittest.TestCase):
    def test_packet_manifest_includes_required_fields(self) -> None:
        """Test packet manifest includes required fields."""
        packet = build_validation_delivery_packet(
            packet_name="test_packet",
            created_at="2025-01-01T00:00:00Z",
            git_branch="test-branch",
            git_commit="abc123",
        )
        self.assertEqual(packet.packet_version, "v1")
        self.assertEqual(packet.packet_name, "test_packet")
        self.assertEqual(packet.created_at, "2025-01-01T00:00:00Z")
        self.assertIsNotNone(packet.overall_status)

    def test_markdown_includes_artifact_table_and_scope(self) -> None:
        """Test Markdown includes artifact table and scope note."""
        packet = build_validation_delivery_packet(
            packet_name="test_packet",
            created_at="2025-01-01T00:00:00Z",
        )
        markdown = generate_packet_index_markdown(packet)

        self.assertIn("Validation Delivery Packet", markdown)
        self.assertIn("offline Qlib research infrastructure validation artifacts only", markdown)
        self.assertIn("not a trading, execution, alpha, or model performance report", markdown)
        self.assertIn("Artifact Index", markdown)
        self.assertIn("Reviewer Notes", markdown)
        self.assertIn("Recommended Action", markdown)

    def test_missing_optional_artifact_produces_warn(self) -> None:
        """Test missing optional artifact produces warn."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            (smoke_root / "dataset_quality").mkdir(parents=True)
            (smoke_root / "contract").mkdir(parents=True)

            dq_report = {"quality_score": {"score": 85.0}, "status": "pass"}
            (smoke_root / "dataset_quality" / "dataset_quality_report.json").write_text(
                json.dumps(dq_report), encoding="utf-8"
            )

            contract_report = {
                "status": "pass",
                "error_count": 0,
                "semantic_error_count": 0,
                "drift_summary": {"breaking_count": 0},
            }
            contract_path = smoke_root / "contract" / "dataset_quality_contract_report.json"
            contract_path.write_text(json.dumps(contract_report), encoding="utf-8")

            packet = build_validation_delivery_packet(
                packet_name="test",
                smoke_root=smoke_root,
                contract_report_path=contract_path,
            )

            self.assertEqual(packet.overall_status, "warn")
            self.assertTrue(any("Optional artifacts missing" in note for note in packet.reviewer_notes))

    def test_missing_critical_artifact_fails_by_default(self) -> None:
        """Test missing critical artifact fails by default."""
        packet = build_validation_delivery_packet(
            packet_name="test",
            created_at="2025-01-01T00:00:00Z",
        )
        self.assertEqual(packet.overall_status, "fail")
        self.assertTrue(any("Critical artifacts missing" in note for note in packet.reviewer_notes))

    def test_allow_missing_critical_converts_to_warn(self) -> None:
        """Test allow_missing_critical converts missing critical to warn."""
        packet = build_validation_delivery_packet(
            packet_name="test",
            created_at="2025-01-01T00:00:00Z",
            allow_missing_critical=True,
        )
        # Should not fail, but may warn about optional missing
        self.assertNotEqual(packet.overall_status, "fail")

    def test_cli_writes_manifest_and_index(self) -> None:
        """Test CLI writes manifest and index."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            smoke_root = tmp_path / "smoke"
            (smoke_root / "dataset_quality").mkdir(parents=True)
            (smoke_root / "contract").mkdir(parents=True)

            dq_report = {"quality_score": {"score": 85.0}, "status": "pass"}
            (smoke_root / "dataset_quality" / "dataset_quality_report.json").write_text(
                json.dumps(dq_report), encoding="utf-8"
            )

            contract_report = {
                "status": "pass",
                "error_count": 0,
                "semantic_error_count": 0,
                "drift_summary": {"breaking_count": 0},
            }
            contract_path = smoke_root / "contract" / "dataset_quality_contract_report.json"
            contract_path.write_text(json.dumps(contract_report), encoding="utf-8")

            out_dir = tmp_path / "packet"

            ret = build_packet_main([
                "--packet-name", "test",
                "--smoke-root", str(smoke_root),
                "--contract-report", str(contract_path),
                "--out-dir", str(out_dir),
            ])

            self.assertEqual(ret, 0)
            self.assertTrue((out_dir / "packet_manifest.json").exists())
            self.assertTrue((out_dir / "packet_index.md").exists())


if __name__ == "__main__":
    unittest.main()
