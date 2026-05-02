from __future__ import annotations
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from cajas.audits.research_governance_audit import run_research_governance_audit
class ResearchGovernanceAuditTests(unittest.TestCase):
    def test_allowlist_docs_phrase(self) -> None:
        with TemporaryDirectory() as tmp:
            Path(tmp,"doc.md").write_text("no broker execution is allowed",encoding="utf-8")
            self.assertEqual(run_research_governance_audit(root=tmp)["status"],"pass")

    def test_ignores_self_audit_files(self) -> None:
        with TemporaryDirectory() as tmp:
            p = Path(tmp, "cajas", "audits")
            p.mkdir(parents=True, exist_ok=True)
            Path(p, "governance_finding_classifier.py").write_text("submit_order", encoding="utf-8")
            self.assertEqual(run_research_governance_audit(root=tmp)["status"], "pass")
if __name__ == "__main__": unittest.main()
