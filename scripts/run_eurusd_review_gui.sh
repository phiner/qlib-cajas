#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

# Intentionally no automatic review reset here.
# Reset only happens when the user explicitly runs:
#   ./scripts/reset_eurusd_review_batch.sh
PYTHON_BIN="${PYTHON_BIN:-./.venv-qlib313/bin/python}"
APP_PATH="cajas/apps/eurusd_pattern_review_app.py"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python not found or not executable: ${PYTHON_BIN}" >&2
  echo "Set PYTHON_BIN or create ./.venv-qlib313 first." >&2
  exit 1
fi

if ! "${PYTHON_BIN}" -c "import streamlit, plotly" >/dev/null 2>&1; then
  echo "Missing GUI dependencies (streamlit/plotly)." >&2
  echo "Install with:" >&2
  echo "  ./.venv-qlib313/bin/python -m pip install streamlit plotly" >&2
  exit 1
fi

exec "${PYTHON_BIN}" -m streamlit run "${APP_PATH}" "$@"
