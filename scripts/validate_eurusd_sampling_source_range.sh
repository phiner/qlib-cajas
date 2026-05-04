#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-./.venv-qlib313/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python"
fi

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_sampling_source_range_report
cat tmp/validation-eurusd-sampling-source-range.json
