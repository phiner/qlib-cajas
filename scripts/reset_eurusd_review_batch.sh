#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-./.venv-qlib313/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python"
fi

BATCH_SIZE=100
PER_TYPE_TARGET=10
MIN_GAP_BARS=8
MAX_SAMPLES_PER_DAY=8
BACKUP_OLD=0
DRY_RUN=0

usage() {
  cat <<USAGE
Usage: ./scripts/reset_eurusd_review_batch.sh [options]

Options:
  --backup-old                 Backup old review files before reset
  --batch-size <N>             Batch size (default: 100)
  --min-gap-bars <N>           Min gap bars between samples (default: 8)
  --max-samples-per-day <N>    Max samples per day (default: 8)
  --dry-run                    Print planned actions only
  -h, --help                   Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup-old)
      BACKUP_OLD=1
      shift
      ;;
    --batch-size)
      BATCH_SIZE="$2"
      shift 2
      ;;
    --min-gap-bars)
      MIN_GAP_BARS="$2"
      shift 2
      ;;
    --max-samples-per-day)
      MAX_SAMPLES_PER_DAY="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

TEMPLATE_CSV="tmp/eurusd/EURUSD_15m_pattern_review_template.csv"
LABEL_SCHEMA="tmp/validation-eurusd-pattern-label-schema.json"
PATTERN_CANDIDATES_CSV="tmp/eurusd/EURUSD_15m_pattern_candidates.csv"
PATTERN_SAMPLES_CSV="tmp/eurusd/EURUSD_15m_pattern_review_samples.csv"
PATTERN_SAMPLES_JSONL="tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl"
PATTERN_CANDIDATE_PACK_JSON="tmp/validation-eurusd-pattern-candidate-pack.json"
PATTERN_CANDIDATE_PACK_MD="tmp/validation-eurusd-pattern-candidate-pack.md"
TEMPLATE_JSON="tmp/validation-eurusd-pattern-review-template.json"
TEMPLATE_MD="tmp/validation-eurusd-pattern-review-template.md"
OUTPUT_BATCH_CSV="tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"
OUTPUT_BATCH_JSONL="tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl"
OUTPUT_JSON="tmp/validation-eurusd-pattern-review-batch-001.json"
OUTPUT_MD="tmp/validation-eurusd-pattern-review-batch-001.md"
COMPLETED_CSV="tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv"
COMPLETED_EVENTS_JSONL="tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl"
COMPLETED_PROGRESS_JSON="tmp/validation-eurusd-completed-review-progress.json"
COMPLETED_PROGRESS_MD="tmp/validation-eurusd-completed-review-progress.md"
SUMMARY_CURRENT_JSON="tmp/validation-eurusd-review-summary-current.json"
SUMMARY_CURRENT_MD="tmp/validation-eurusd-review-summary-current.md"
REJECTED_JSON="tmp/validation-eurusd-rejected-samples.json"
REJECTED_MD="tmp/validation-eurusd-rejected-samples.md"
REJECTED_CSV="tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples.csv"
REJECTED_EVENTS_JSONL="tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples_events.jsonl"
SOURCE_RANGE_JSON="tmp/validation-eurusd-sampling-source-range.json"
SOURCE_RANGE_MD="tmp/validation-eurusd-sampling-source-range.md"
RESET_JSON="tmp/validation-eurusd-review-batch-reset.json"
RESET_MD="tmp/validation-eurusd-review-batch-reset.md"

TARGET_FILES=(
  "${OUTPUT_BATCH_CSV}"
  "${OUTPUT_BATCH_JSONL}"
  "${OUTPUT_JSON}"
  "${OUTPUT_MD}"
  "${COMPLETED_CSV}"
  "${COMPLETED_EVENTS_JSONL}"
  "${COMPLETED_PROGRESS_JSON}"
  "${COMPLETED_PROGRESS_MD}"
  "${SUMMARY_CURRENT_JSON}"
  "${SUMMARY_CURRENT_MD}"
)

if [[ ! -f "${TEMPLATE_CSV}" ]]; then
  echo "Missing template CSV: ${TEMPLATE_CSV}" >&2
  exit 3
fi

if [[ ! -f "${LABEL_SCHEMA}" ]]; then
  echo "Missing label schema JSON: ${LABEL_SCHEMA}" >&2
  exit 4
fi

BACKUP_DIR=""
if [[ "${BACKUP_OLD}" -eq 1 ]]; then
  BACKUP_DIR="tmp/eurusd/review_reset_backups/$(date +%Y%m%d_%H%M%S)"
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "[dry-run] python: ${PYTHON_BIN}"
  echo "[dry-run] backup_old: ${BACKUP_OLD}"
  echo "[dry-run] backup_dir: ${BACKUP_DIR:-<none>}"
  echo "[dry-run] would remove/rebuild target files:"
  for f in "${TARGET_FILES[@]}"; do
    echo "  - ${f}"
  done
  echo "[dry-run] would rebuild candidates/template/batch with:"
  echo "  --batch-size ${BATCH_SIZE} --per-type-target ${PER_TYPE_TARGET} --min-gap-bars ${MIN_GAP_BARS} --max-samples-per-day ${MAX_SAMPLES_PER_DAY}"
  mkdir -p "$(dirname "${RESET_JSON}")"
  PYTHONPATH=. "${PYTHON_BIN}" - <<'PY' "${RESET_JSON}" "${RESET_MD}" "${BACKUP_OLD}" "${BACKUP_DIR}" "${MIN_GAP_BARS}" "${MAX_SAMPLES_PER_DAY}" "${OUTPUT_BATCH_CSV}" "${OUTPUT_BATCH_JSONL}"
import json
import sys
from pathlib import Path

reset_json, reset_md, backup_old, backup_dir, min_gap_bars, max_samples_per_day, batch_csv, batch_jsonl = sys.argv[1:9]
payload = {
    "status": "dry_run",
    "reset_mode": "fresh",
    "backup_enabled": backup_old == "1",
    "backup_dir": backup_dir or None,
    "removed_files": [],
    "generated_files": [],
    "diversification_settings": {
        "balanced_by_candidate_type": True,
        "min_gap_bars_between_samples": int(min_gap_bars),
        "max_samples_per_day": int(max_samples_per_day),
        "prefer_time_diversity": True,
    },
    "batch_csv": batch_csv,
    "batch_jsonl": batch_jsonl,
    "completed_csv_removed": False,
    "completed_events_jsonl_removed": False,
    "first10_unique_days": None,
    "first10_min_gap_minutes": None,
    "first10_samples": [],
    "next_action": "run_without_dry_run",
}
Path(reset_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
md = [
    "# EURUSD Review Batch Reset",
    "",
    f"- status: `{payload['status']}`",
    f"- backup_enabled: `{payload['backup_enabled']}`",
    f"- backup_dir: `{payload['backup_dir']}`",
    f"- next_action: `{payload['next_action']}`",
]
Path(reset_md).write_text("\\n".join(md) + "\\n", encoding="utf-8")
PY
  exit 0
fi

removed_files=()
if [[ "${BACKUP_OLD}" -eq 1 ]]; then
  mkdir -p "${BACKUP_DIR}"
fi

for f in "${TARGET_FILES[@]}"; do
  if [[ -f "${f}" ]]; then
    if [[ "${BACKUP_OLD}" -eq 1 ]]; then
      cp -f "${f}" "${BACKUP_DIR}/"
    fi
    rm -f "${f}"
    removed_files+=("${f}")
  fi
done

mkdir -p tmp/eurusd tmp

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_pattern_candidate_pack \
  --clean-view-csv "tmp/eurusd/EURUSD_15m_Bid_clean_view.csv" \
  --output-candidates-csv "${PATTERN_CANDIDATES_CSV}" \
  --output-samples-csv "${PATTERN_SAMPLES_CSV}" \
  --output-samples-jsonl "${PATTERN_SAMPLES_JSONL}" \
  --output-json "${PATTERN_CANDIDATE_PACK_JSON}" \
  --output-md "${PATTERN_CANDIDATE_PACK_MD}" \
  --max-samples-per-type 50 \
  --min-confidence 0.6

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_pattern_review_template \
  --samples-csv "${PATTERN_SAMPLES_CSV}" \
  --label-schema "${LABEL_SCHEMA}" \
  --output-template-csv "${TEMPLATE_CSV}" \
  --output-template-jsonl "tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl" \
  --output-json "${TEMPLATE_JSON}" \
  --output-md "${TEMPLATE_MD}"

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_pattern_review_batch \
  --template-csv "${TEMPLATE_CSV}" \
  --label-schema "${LABEL_SCHEMA}" \
  --batch-id "eurusd_15m_pattern_review_batch_001" \
  --batch-size "${BATCH_SIZE}" \
  --per-type-target "${PER_TYPE_TARGET}" \
  --min-gap-bars "${MIN_GAP_BARS}" \
  --max-samples-per-day "${MAX_SAMPLES_PER_DAY}" \
  --output-batch-csv "${OUTPUT_BATCH_CSV}" \
  --output-batch-jsonl "${OUTPUT_BATCH_JSONL}" \
  --output-json "${OUTPUT_JSON}" \
  --output-md "${OUTPUT_MD}"

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_sampling_source_range_report \
  --output-json "${SOURCE_RANGE_JSON}" \
  --output-md "${SOURCE_RANGE_MD}"

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_completed_review_progress_report \
  --output-json "${COMPLETED_PROGRESS_JSON}" \
  --output-md "${COMPLETED_PROGRESS_MD}"

PYTHONPATH=. "${PYTHON_BIN}" -m cajas.scripts.build_eurusd_rejected_samples_report \
  --rejected-csv "${REJECTED_CSV}" \
  --rejected-events-jsonl "${REJECTED_EVENTS_JSONL}" \
  --output-json "${REJECTED_JSON}" \
  --output-md "${REJECTED_MD}"

PYTHONPATH=. "${PYTHON_BIN}" - <<'PY' "${RESET_JSON}" "${RESET_MD}" "${OUTPUT_BATCH_CSV}" "${OUTPUT_BATCH_JSONL}" "${COMPLETED_CSV}" "${COMPLETED_EVENTS_JSONL}" "${BACKUP_OLD}" "${BACKUP_DIR}" "${MIN_GAP_BARS}" "${MAX_SAMPLES_PER_DAY}" "${BATCH_SIZE}" "${removed_files[*]:-}"
import json
import sys
from pathlib import Path
import pandas as pd

(
    reset_json,
    reset_md,
    batch_csv,
    batch_jsonl,
    completed_csv,
    completed_events,
    backup_old,
    backup_dir,
    min_gap_bars,
    max_samples_per_day,
    batch_size,
    removed_joined,
) = sys.argv[1:13]

removed_files = [f for f in removed_joined.split(" ") if f]
batch_df = pd.read_csv(batch_csv)
ts = pd.to_datetime(batch_df["timestamp"], utc=True, errors="coerce")
first10 = batch_df.head(10).copy()
first10_ts = pd.to_datetime(first10["timestamp"], utc=True, errors="coerce")
first10_unique_days = int(first10_ts.dt.strftime("%Y-%m-%d").nunique()) if len(first10) else 0
if len(first10_ts.dropna()) > 1:
    first10_min_gap = float((first10_ts.sort_values().diff().dropna().dt.total_seconds() / 60.0).min())
else:
    first10_min_gap = None

first10_samples = first10[["sample_id", "timestamp", "candidate_type"]].to_dict(orient="records")

payload = {
    "status": "reset_complete",
    "reset_mode": "fresh",
    "backup_enabled": backup_old == "1",
    "backup_dir": backup_dir if backup_old == "1" else None,
    "removed_files": removed_files,
    "generated_files": [
        "tmp/eurusd/EURUSD_15m_pattern_candidates.csv",
        "tmp/eurusd/EURUSD_15m_pattern_review_samples.csv",
        "tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl",
        "tmp/validation-eurusd-pattern-candidate-pack.json",
        "tmp/validation-eurusd-pattern-candidate-pack.md",
        "tmp/eurusd/EURUSD_15m_pattern_review_template.csv",
        "tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl",
        "tmp/validation-eurusd-pattern-review-template.json",
        "tmp/validation-eurusd-pattern-review-template.md",
        batch_csv,
        batch_jsonl,
        "tmp/validation-eurusd-pattern-review-batch-001.json",
        "tmp/validation-eurusd-pattern-review-batch-001.md",
        "tmp/validation-eurusd-sampling-source-range.json",
        "tmp/validation-eurusd-sampling-source-range.md",
        "tmp/validation-eurusd-completed-review-progress.json",
        "tmp/validation-eurusd-completed-review-progress.md",
        "tmp/validation-eurusd-rejected-samples.json",
        "tmp/validation-eurusd-rejected-samples.md",
    ],
    "diversification_settings": {
        "balanced_by_candidate_type": True,
        "min_gap_bars_between_samples": int(min_gap_bars),
        "max_samples_per_day": int(max_samples_per_day),
        "prefer_time_diversity": True,
    },
    "batch_csv": batch_csv,
    "batch_jsonl": batch_jsonl,
    "completed_csv_removed": completed_csv in removed_files,
    "completed_events_jsonl_removed": completed_events in removed_files,
    "first10_unique_days": first10_unique_days,
    "first10_min_gap_minutes": first10_min_gap,
    "first10_samples": first10_samples,
    "next_action": "run_gui_review",
}

Path(reset_json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
lines = [
    "# EURUSD Review Batch Reset",
    "",
    f"- status: `{payload['status']}`",
    f"- backup_enabled: `{payload['backup_enabled']}`",
    f"- backup_dir: `{payload['backup_dir']}`",
    f"- batch_csv: `{payload['batch_csv']}`",
    f"- batch_jsonl: `{payload['batch_jsonl']}`",
    f"- first10_unique_days: `{payload['first10_unique_days']}`",
    f"- first10_min_gap_minutes: `{payload['first10_min_gap_minutes']}`",
    f"- completed_csv_removed: `{payload['completed_csv_removed']}`",
    f"- completed_events_jsonl_removed: `{payload['completed_events_jsonl_removed']}`",
    f"- next_action: `{payload['next_action']}`",
]
Path(reset_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

echo "Reset complete."
echo "Batch CSV: ${OUTPUT_BATCH_CSV}"
echo "Batch JSONL: ${OUTPUT_BATCH_JSONL}"
echo "Reset JSON: ${RESET_JSON}"
echo "Reset MD: ${RESET_MD}"
