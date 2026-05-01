#!/usr/bin/env python3
"""Check repository path hygiene for known typo patterns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.quality.path_hygiene import check_path_hygiene


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check path hygiene.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-taskdocs", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    patterns = ("caixas/",) if args.allow_taskdocs else ("caixas/", "taskDocs/")
    report = check_path_hygiene(root=args.root, forbidden_patterns=patterns)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=True, indent=2))
    else:
        print(f"checked files: {report.checked_files}")
        print(f"issues: {len(report.issues)}")
        for issue in report.issues:
            print(
                f"{issue.path}:{issue.line} pattern={issue.pattern} message={issue.message}"
            )

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
