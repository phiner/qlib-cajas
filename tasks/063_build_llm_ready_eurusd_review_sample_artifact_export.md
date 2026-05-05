# Task 063 — Build LLM-Ready EURUSD Review Sample Artifact Export

## Context

Task 061 established the bilingual boundary policy:

- English runtime identifiers.
- Chinese-authoritative semantic reasoning.

Task 062 promoted Chinese rationale fields to first-class review-record fields:

- `human_rationale_zh`
- `human_counterexample_zh`
- `human_uncertainty_reason_zh`
- `human_context_notes_zh`

Now the next step is to create a deterministic, LLM-ready sample artifact export.

Important boundaries:

- Do not add live LLM API calls.
- Do not ask an LLM to inspect raw CSVs or infer basic OHLC facts.
- Deterministic code must prepare the review package first.
- LLM will eventually read only this clean artifact package.
- No trading signals, no orders, no position sizing, no model training.

## Goal

Add a deterministic export path that produces structured LLM-ready review sample artifacts from the active EURUSD 15m review workflow.

The artifact should combine:

1. Machine-facing stable identifiers and sample facts.
2. Deterministically computed chart/context diagnostics.
3. Human review labels and first-class Chinese rationale fields.
4. Bilingual policy/standard metadata.
5. Explicit forbidden-output boundary for future LLM use.

## Required Artifact Shape

Create one JSONL row per sample or reviewed sample. Recommended schema:

```json
{
  "artifact_version": "eurusd_llm_review_sample_v0",
  "sample_id": "...",
  "symbol": "EURUSD",
  "timeframe": "15m",
  "candidate_type": "...",
  "standard_version": "eurusd_15m_review_standard_v0",
  "language_policy": {
    "runtime_language": "en",
    "semantic_language": "zh",
    "zh_fields_authoritative": true
  },
  "target_candle": {
    "timestamp": "...",
    "open": 0.0,
    "high": 0.0,
    "low": 0.0,
    "close": 0.0
  },
  "context_window": {
    "lookback_bars": 72,
    "forward_bars": 48,
    "target_index": 60,
    "window_bar_count": 121,
    "gap_count": 0,
    "largest_gap_hours": null
  },
  "deterministic_diagnostics": {
    "display_axis": "compressed_time_axis|real_time_axis|unknown",
    "exact_match": true,
    "fallback_used": false
  },
  "human_review": {
    "human_label": "valid|invalid|uncertain|...",
    "human_confidence": "low|medium|high|...",
    "human_rationale_zh": "...",
    "human_counterexample_zh": "...",
    "human_uncertainty_reason_zh": "...",
    "human_context_notes_zh": "..."
  },
  "future_llm_boundary": {
    "role": "second_reviewer",
    "allowed_tasks": [
      "review_pattern_validity",
      "identify_supporting_observations",
      "identify_counter_observations",
      "flag_uncertainty",
      "recommend_human_review"
    ],
    "forbidden_outputs": [
      "trade_signal",
      "entry",
      "exit",
      "position_size",
      "pnl_prediction",
      "order_recommendation",
      "execution_instruction"
    ]
  }
}
```

Do not require every human rationale field to be non-empty yet.

## CLI / Report Requirements

Add a script that exports artifacts from current review inputs.

Suggested files:

- `cajas/reports/validation_eurusd_llm_review_artifacts.py`
- `cajas/scripts/build_eurusd_llm_review_artifacts.py`
- `cajas/tests/test_validation_eurusd_llm_review_artifacts.py`

Suggested outputs:

- `tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl`
- `tmp/validation-eurusd-llm-review-artifacts.json`
- `tmp/validation-eurusd-llm-review-artifacts.md`

Report should include:

- `report_status`: `llm_review_artifacts_ready|blocked`
- artifact version
- row count
- reviewed row count if available
- rationale field presence
- language boundary presence
- forbidden output boundary presence
- schema key language check
- missing required field count

## Deterministic Data Rules

- Use existing batch/review artifacts where possible.
- CSV remains authoritative for latest review state by `sample_id`.
- JSONL remains audit history and should not replace latest-state CSV.
- Do not migrate old data.
- Do not add compatibility wrappers.
- If completed review CSV is absent, artifact export may still produce sample rows with empty human review fields and report that reviewed count is 0.

## Implementation Targets

Inspect and update as appropriate:

- `cajas/research/eurusd_review_schema.py`
- `cajas/research/eurusd_pattern_review_gui.py`
- `cajas/reports/validation_eurusd_pattern_review_gui.py`
- `cajas/reports/validation_eurusd_zh_rationale_fields.py`
- `cajas/docs/eurusd_review_language_policy.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`

Add tests for:

- artifact rows include `_zh` human rationale fields
- artifact rows use English keys only
- artifact includes language policy metadata
- artifact includes forbidden LLM outputs
- reviewed rows merge latest CSV state by `sample_id`
- export works when completed review CSV is absent
- report status is ready when artifact generation succeeds

## Validation Commands

Run focused tests:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_llm_review_artifacts.py   cajas/tests/test_eurusd_review_schema.py   cajas/tests/test_validation_eurusd_zh_rationale_fields.py
```

Run compile and report build:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m py_compile   cajas/reports/validation_eurusd_llm_review_artifacts.py   cajas/scripts/build_eurusd_llm_review_artifacts.py

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/build_eurusd_llm_review_artifacts.py   --output-json tmp/validation-eurusd-llm-review-artifacts.json   --output-md tmp/validation-eurusd-llm-review-artifacts.md   --output-jsonl tmp/eurusd/EURUSD_15m_llm_review_samples.jsonl
```

Run hygiene:

```bash
git diff --check

PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py

find cajas -path '*/init.py' -print
```

Run fast validation if practical, but do not block this task on the already-known unrelated 6 legacy failures. Clearly report whether failures are unchanged or new:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py   --tier fast   --timing-json tmp/fast_validation_latest.json
```

## Expected Final State

- Deterministic LLM-ready sample artifact export exists.
- Future LLM will have a clean artifact to read instead of raw CSV/GUI state.
- Chinese human rationale fields are preserved in artifact rows.
- English runtime/schema boundary is preserved.
- Forbidden trading outputs are explicitly encoded.
- No live LLM calls.
- No trading signals, no orders, no position sizing, no model training.
- Commit directly on `main`.
