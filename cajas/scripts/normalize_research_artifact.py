#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.artifact_normalizer import normalize_json_artifact, normalize_markdown_artifact


def main() -> int:
    p = argparse.ArgumentParser(description="Normalize research artifact for stable comparison.")
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    inp = Path(args.input).expanduser().resolve()
    if inp.suffix.lower() == ".json":
        rep = normalize_json_artifact(input_path=inp, output_path=args.out)
    elif inp.suffix.lower() == ".md":
        rep = normalize_markdown_artifact(input_path=inp, output_path=args.out)
    else:
        raise SystemExit("unsupported artifact type")
    print(json.dumps({"output": rep["output_path"], "normalized_fields": rep["normalized_fields"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
