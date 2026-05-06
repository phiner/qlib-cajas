#!/usr/bin/env bash
set -euo pipefail

if ! PYTHONPATH=. ./.venv-qlib313/bin/python -c "import streamlit" >/dev/null 2>&1; then
  echo "Streamlit is not installed in .venv-qlib313."
  echo "Install with: ./.venv-qlib313/bin/python -m pip install streamlit"
  exit 1
fi

PYTHONPATH=. ./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_micro_pattern_review_app.py
