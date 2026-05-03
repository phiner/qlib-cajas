#!/usr/bin/env python3
"""Update validation review bundle history."""

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_review_bundle_history import (
    create_snapshot_from_bundle,
    append_snapshot,
    read_snapshots,
    generate_history_summary_markdown,
)


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update validation review bundle history")
    parser.add_argument("--bundle-root", type=Path, required=True, help="Bundle root directory")
    parser.add_argument("--history-jsonl", type=Path, required=True, help="History JSONL file path")
    parser.add_argument("--out-json", type=Path, help="Output JSON summary path")
    parser.add_argument("--out-md", type=Path, help="Output Markdown summary path")
    parser.add_argument("--last-n", type=int, default=10, help="Number of recent snapshots to show")
    parser.add_argument("--branch", help="Override git branch")
    parser.add_argument("--commit", help="Override git commit")
    parser.add_argument("--created-at", help="Override created timestamp")

    args = parser.parse_args(argv)

    try:
        # Create snapshot from bundle
        snapshot = create_snapshot_from_bundle(
            bundle_root=args.bundle_root,
            branch=args.branch,
            commit=args.commit,
            created_at=args.created_at,
        )

        # Append to history
        append_snapshot(args.history_jsonl, snapshot)

        # Read all snapshots
        snapshots = read_snapshots(args.history_jsonl)

        # Generate summary
        summary = {
            "snapshot_count": len(snapshots),
            "latest_snapshot": {
                "created_at": snapshot.created_at,
                "branch": snapshot.branch,
                "commit": snapshot.commit,
                "delivery_packet_status": snapshot.delivery_packet_status,
                "runtime_budget_status": snapshot.runtime_budget_status,
                "fast_total_seconds": snapshot.fast_total_seconds,
            },
        }

        # Write JSON summary
        if args.out_json:
            args.out_json.parent.mkdir(parents=True, exist_ok=True)
            with open(args.out_json, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

        # Write Markdown summary
        if args.out_md:
            args.out_md.parent.mkdir(parents=True, exist_ok=True)
            markdown = generate_history_summary_markdown(snapshots, last_n=args.last_n)
            with open(args.out_md, "w", encoding="utf-8") as f:
                f.write(markdown)

        print(json.dumps({"status": "ok", "snapshot_count": len(snapshots)}))
        return 0

    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
