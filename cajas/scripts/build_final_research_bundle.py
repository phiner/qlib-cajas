#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.final_research_bundle import build_final_research_bundle, render_final_research_bundle_md


def _load(path: str | Path) -> dict:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build final research bundle outputs.")
    p.add_argument("--root", required=True)
    p.add_argument("--final-readiness-packet", required=True)
    p.add_argument("--final-readiness-summary", required=True)
    p.add_argument("--stable-reproducibility-report", required=True)
    p.add_argument("--governance-audit", required=True)
    p.add_argument("--artifact-lineage", required=True)
    p.add_argument("--run-catalog", required=True)
    p.add_argument("--offline-review-packet", required=True)
    p.add_argument("--ci-validation-plan", required=True)
    p.add_argument("--governance-review-decision", default=None)
    p.add_argument("--research-only-approval-packet", default=None)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args(argv)

    bundle = build_final_research_bundle(
        root=str(Path(args.root).expanduser().resolve()),
        final_readiness_packet=_load(args.final_readiness_packet),
        final_readiness_summary_path=str(Path(args.final_readiness_summary).expanduser().resolve()),
        stable_repro_report=_load(args.stable_reproducibility_report),
        governance_audit=_load(args.governance_audit),
        artifact_lineage=_load(args.artifact_lineage),
        run_catalog=_load(args.run_catalog),
        offline_review_packet=_load(args.offline_review_packet),
        ci_validation_plan=_load(args.ci_validation_plan),
        governance_review_decision=None if args.governance_review_decision is None else _load(args.governance_review_decision),
        research_only_approval_packet=None if args.research_only_approval_packet is None else _load(args.research_only_approval_packet),
    )

    out_j = Path(args.out_json).expanduser().resolve()
    out_m = Path(args.out_md).expanduser().resolve()
    out_j.parent.mkdir(parents=True, exist_ok=True)
    out_m.parent.mkdir(parents=True, exist_ok=True)
    out_j.write_text(json.dumps(bundle, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_m.write_text(render_final_research_bundle_md(bundle=bundle), encoding="utf-8")
    print(f"final bundle json: {out_j}")
    print(f"final bundle md: {out_m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
