#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.candidate_promotion_manifest import build_candidate_promotion_manifest


def _render_md(manifest: dict) -> str:
    return (
        "# Candidate Promotion Manifest\n\n"
        "Research-only candidate manifest for future manual review.\n\n"
        f"- status: `{manifest['status']}`\n"
        f"- label_variant_id: `{manifest['label_variant_id']}`\n"
        f"- feature_set_id: `{manifest['feature_set_id']}`\n"
        f"- target_name: `{manifest['target_name']}`\n"
        f"- horizon: `{manifest['horizon']}`\n"
        f"- model_family: `{manifest['model_family']}`\n"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build candidate promotion manifest from research decision packet.")
    p.add_argument("--decision-packet", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--label-variant-id", required=True)
    p.add_argument("--feature-set-id", required=True)
    p.add_argument("--target-name", required=True)
    p.add_argument("--horizon", required=True, type=int)
    p.add_argument("--model-family", required=True)
    args = p.parse_args(argv)

    out = Path(args.out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = build_candidate_promotion_manifest(
        decision_packet_path=args.decision_packet,
        out_dir=out,
        label_variant_id=args.label_variant_id,
        feature_set_id=args.feature_set_id,
        target_name=args.target_name,
        horizon=args.horizon,
        model_family=args.model_family,
    )
    (out / "candidate_promotion_manifest.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "candidate_promotion_manifest.md").write_text(_render_md(manifest), encoding="utf-8")
    print("Candidate promotion manifest completed.")
    print(f"output dir: {out}")
    print(f"status: {manifest['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
