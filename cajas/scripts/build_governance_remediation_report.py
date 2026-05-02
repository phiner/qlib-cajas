#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.audits.governance_remediation_report import build_governance_remediation_report, render_governance_remediation_report_md


def main() -> int:
    p = argparse.ArgumentParser(description="Build governance remediation report.")
    p.add_argument("--governance-audit", required=True)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args()

    audit = json.loads(Path(args.governance_audit).expanduser().read_text(encoding="utf-8"))
    report = build_governance_remediation_report(governance_audit=audit)

    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_governance_remediation_report_md(report=report), encoding="utf-8")
    print(f"output json: {out_json}")
    print(f"output md: {out_md}")
    print(f"final_suggested_status: {report['final_suggested_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

