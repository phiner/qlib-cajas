#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-./.venv-qlib313/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python"
fi

SKIP_FAST_VALIDATION=0
JSON_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-fast-validation)
      SKIP_FAST_VALIDATION=1
      shift
      ;;
    --json-only)
      JSON_ONLY=1
      shift
      ;;
    -h|--help)
      cat <<USAGE
Usage: ./scripts/validate_eurusd_review_progress.sh [--skip-fast-validation] [--json-only]
USAGE
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_completed_review_progress_report
PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_review_summary_current_report

if [[ -f tmp/validation-routine-maintenance-continuation.json && -f tmp/validation-eurusd-dataset-contract.json && -f tmp/validation-eurusd-dataset-audit.json ]]; then
  PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_research_readiness_report \
    --base-maintenance-continuation-report tmp/validation-routine-maintenance-continuation.json \
    --dataset-contract-report tmp/validation-eurusd-dataset-contract.json \
    --dataset-audit-report tmp/validation-eurusd-dataset-audit.json \
    --clean-dataset-view-report tmp/validation-eurusd-clean-dataset-view.json \
    --review-batch-report tmp/validation-eurusd-pattern-review-batch-001.json \
    --review-guide-report tmp/validation-eurusd-pattern-review-guide.json \
    --review-completion-closure-report tmp/validation-eurusd-pattern-review-completion-closure.json \
    --completed-review-progress-report tmp/validation-eurusd-completed-review-progress.json \
    --review-summary-current-report tmp/validation-eurusd-review-summary-current.json \
    --out-json tmp/validation-eurusd-research-readiness-current.json \
    --out-md tmp/validation-eurusd-research-readiness-current.md
fi

if [[ "${SKIP_FAST_VALIDATION}" -eq 0 ]]; then
  "${PYTHON_BIN}" caixas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
fi

if [[ "${JSON_ONLY}" -eq 1 ]]; then
  cat tmp/validation-eurusd-completed-review-progress.json
  exit 0
fi

PYTHONPATH=. "${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
p=Path('tmp/validation-eurusd-completed-review-progress.json')
s=Path('tmp/validation-eurusd-review-summary-current.json')
if p.exists():
    progress=json.loads(p.read_text(encoding='utf-8'))
    print('progress_status:',progress.get('status'))
    print('completed_count:',progress.get('completed_count'))
    print('pending_count:',progress.get('pending_count'))
    print('completion_ratio:',progress.get('completion_ratio'))
    print('next_action:',progress.get('next_action'))
if s.exists():
    summary=json.loads(s.read_text(encoding='utf-8'))
    print('summary_status:',summary.get('status'))
    print('reviewed_count:',summary.get('reviewed_count'))
PY
