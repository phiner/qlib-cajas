#!/usr/bin/env python3
"""Build validation profile matrix report."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from cajas.reports.validation_profile_matrix import (
    build_profile_matrix,
    render_profile_matrix_markdown,
)

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build validation profile matrix report")
    parser.add_argument("--bundle-root", required=True, type=Path, help="Path to existing review bundle root")
    parser.add_argument("--profile-config", type=Path, help="Path to CI profiles config")
    parser.add_argument("--out-json", type=Path, required=True, help="Output JSON path")
    parser.add_argument("--out-md", type=Path, required=True, help="Output Markdown path")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    bundle_root = args.bundle_root
    final_status_path = bundle_root / "final_status.json"
    
    if not final_status_path.exists():
        logger.error(f"Cannot build matrix. Missing final_status.json at {final_status_path}")
        return 1
        
    base_payload = json.loads(final_status_path.read_text(encoding="utf-8"))
    
    profile_config = None
    if args.profile_config and args.profile_config.exists():
        profile_config = json.loads(args.profile_config.read_text(encoding="utf-8"))

    logger.info(f"Building profile matrix from {final_status_path}")
    matrix_payload = build_profile_matrix(
        base_payload=base_payload,
        profile_config=profile_config,
    )

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(matrix_payload, indent=2), encoding="utf-8")
    logger.info(f"Wrote {args.out_json}")

    md_content = render_profile_matrix_markdown(matrix_payload)
    args.out_md.write_text(md_content, encoding="utf-8")
    logger.info(f"Wrote {args.out_md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
