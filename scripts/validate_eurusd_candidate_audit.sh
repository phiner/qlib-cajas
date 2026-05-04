#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-./.venv-qlib313/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python"
fi

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_candidate_audit_report

PYTHONPATH=. "${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
p = Path("tmp/validation-eurusd-candidate-audit.json")
if p.exists():
    payload = json.loads(p.read_text(encoding="utf-8"))
    print("candidate_audit_status:", payload.get("status"))
    print("next_actions:", payload.get("next_actions"))
PY
