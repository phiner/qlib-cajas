#!/usr/bin/env python3
"""Build history alias migration readiness report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_history_alias_migration import (
    build_history_alias_migration_report,
    render_history_alias_migration_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build history alias migration readiness report")
    parser.add_argument("--default-bundle-root", required=True, type=Path, help="Default (alias) bundle root")
    parser.add_argument("--no-alias-bundle-root", type=Path, help="No-alias bundle root (legacy argument)")
    parser.add_argument("--alias-fallback-bundle-root", type=Path, help="Alias-fallback bundle root")
    parser.add_argument("--out-json", required=True, type=Path, help="Output JSON report path")
    parser.add_argument("--out-md", required=True, type=Path, help="Output Markdown report path")
    args = parser.parse_args(argv)

    compare_root = args.alias_fallback_bundle_root or args.no_alias_bundle_root
    if compare_root is None:
        parser.error("one of --no-alias-bundle-root or --alias-fallback-bundle-root is required")

    payload = build_history_alias_migration_report(
        default_bundle_root=args.default_bundle_root,
        no_alias_bundle_root=compare_root,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.out_md.write_text(render_history_alias_migration_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.out_json), "out_md": str(args.out_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
