#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.stable_reproducibility_explainer import (
    build_stable_reproducibility_explanation,
    render_stable_reproducibility_explanation_md,
)


def _load(path: str | Path | None) -> dict | None:
    if path is None:
        return None
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Explain stable reproducibility mismatch causes.")
    p.add_argument("--left-fingerprint", required=True)
    p.add_argument("--right-fingerprint", required=True)
    p.add_argument("--stable-repro-report", required=True)
    p.add_argument("--left-manifest", default=None)
    p.add_argument("--right-manifest", default=None)
    p.add_argument("--out-json", required=True)
    p.add_argument("--out-md", required=True)
    args = p.parse_args()

    explanation = build_stable_reproducibility_explanation(
        left_fingerprint=_load(args.left_fingerprint) or {},
        right_fingerprint=_load(args.right_fingerprint) or {},
        stable_repro_report=_load(args.stable_repro_report) or {},
        left_manifest=_load(args.left_manifest),
        right_manifest=_load(args.right_manifest),
    )
    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(explanation, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_stable_reproducibility_explanation_md(explanation=explanation), encoding="utf-8")
    print(f"output json: {out_json}")
    print(f"output md: {out_md}")
    print(f"classification: {explanation['classification']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

