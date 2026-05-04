# EURUSD 15m Research End-to-End Roadmap

## 1. Project Purpose

This project is a Qlib-based offline research platform for EURUSD 15m Bid K-line / candlestick pattern research.

The infrastructure work exists to make later market-structure research:

- reproducible
- auditable
- reviewable
- safe
- separated from trading execution

The real research objective is not to build an automatic trading bot immediately. The objective is to help the system and the human researcher understand EURUSD 15m price structure, candidate patterns, review quality, and later offline outcome behavior.

## 2. Scope Boundaries

This project is:

- offline research infrastructure
- EURUSD 15m Bid pattern research
- human-in-the-loop annotation and review
- reproducible dataset/report generation
- reviewer-friendly validation artifacts
- local GUI-assisted manual review

This project is not:

- live trading
- paper trading
- broker routing
- order generation
- position sizing
- portfolio optimization
- production investment advice
- Qlib core modification
- multi-timeframe aggregation by default
- production ML training yet

Non-negotiable constraints:

- Keep Qlib core unchanged.
- Keep raw data immutable.
- Keep EURUSD 15m Bid as the fixed research base.
- Do not aggregate to 1H/4H unless explicitly requested later.
- Do not introduce buy/sell/order/position/target-position semantics into research artifacts.
- GUI is the human review interface.
- CSV/JSONL remain durable storage/interchange formats.
- GitHub merge must be manual by the human user.

Local GUI run commands:

```bash
./scripts/reset_eurusd_review_batch.sh
./scripts/run_eurusd_review_gui.sh
./scripts/validate_eurusd_review_progress.sh
./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_pattern_review_app.py
```

Reset policy:
- reset only runs when `./scripts/reset_eurusd_review_batch.sh` is explicitly invoked
- `./scripts/run_eurusd_review_gui.sh` does not reset/delete review files on startup
- `./scripts/validate_eurusd_review_progress.sh` is read-only and must not reset/regenerate review artifacts

## 3. Repository Posture

The repository currently remains forked from `microsoft/qlib`.

Current decision:

- Keep the fork relationship for now.
- Do not remove fork relationship.
- Do not migrate to a new independent repository.
- Do not sync upstream unless explicitly requested later.

The active project is treated as a Qlib-based offline research/validation layer, not a Qlib core fork and not a trading execution system.

## 4. Data Inputs

Real local data files:

```text
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
```

Interpretation:

- symbol: `EURUSD`
- timeframe: `15m`
- price side: `Bid`
- raw files are immutable
- generated artifacts live under `tmp/`

## 5. Completed Infrastructure Path

### 5.1 Qlib Base validation foundation

The earlier work hardened the `cajas/` layer around:

- dataset quality reporting
- schema contracts
- golden fixtures
- drift detection
- integrated smoke/fast validation
- CI/reviewer guardrails
- data-source audit
- reproducible review bundles
- runtime budget monitoring
- release readiness reports
- milestone packets
- maintenance cadence reports

The infrastructure established that the project is offline validation automation only.

### 5.2 Canonical history and alias cleanup

The review-bundle manifest eventually standardized on:

- canonical field: `history`
- deprecated compatibility alias: `history_update`

Later phases removed active `history_update` alias emission while preserving legacy read normalization for archived manifests.

Current policy:

- producers emit canonical `history` only
- `history_update` should be absent from new manifests
- legacy read normalization remains preserved

### 5.3 Release readiness and post-merge validation

The project reached review-ready/routine maintenance status:

- release readiness: `ready`
- final reviewer packet: `ready_for_review`
- milestone packet: `watch` only as non-blocking governance context
- post-merge mainline validation: completed
- routine maintenance continuation: completed

Manual GitHub merge policy remains active.

## 6. EURUSD Research Path

### 6.1 EURUSD dataset contract and audit

Implemented reports:

```text
cajas/reports/validation_eurusd_dataset_contract.py
cajas/scripts/build_eurusd_dataset_contract_report.py
cajas/tests/test_validation_eurusd_dataset_contract.py

cajas/reports/validation_eurusd_dataset_audit.py
cajas/scripts/build_eurusd_dataset_audit_report.py
cajas/tests/test_validation_eurusd_dataset_audit.py
```

Findings:

- dataset contract status: `ready`
- combined coverage: `149724` rows
- date range: `2020-01-01T22:00:00+00:00` to `2025-12-31T21:45:00+00:00`
- file count: `2`
- raw dataset audit status: `blocked`
- reason: 10 invalid OHLC rows in the 2020–2024 raw file

Artifacts:

```text
tmp/validation-eurusd-dataset-contract.json
tmp/validation-eurusd-dataset-contract.md
tmp/validation-eurusd-dataset-audit.json
tmp/validation-eurusd-dataset-audit.md
```

### 6.2 OHLC anomaly triage and clean view

Implemented:

```text
cajas/reports/validation_eurusd_ohlc_anomaly_triage.py
cajas/scripts/build_eurusd_ohlc_anomaly_triage_report.py
cajas/tests/test_validation_eurusd_ohlc_anomaly_triage.py

cajas/reports/validation_eurusd_clean_dataset_view.py
cajas/scripts/build_eurusd_clean_dataset_view_report.py
cajas/tests/test_validation_eurusd_clean_dataset_view.py
```

Current data state:

- anomaly triage status: `blocked`
- anomaly row count: `10`
- earliest anomaly: `2024-10-09T23:45:00+00:00`
- latest anomaly: `2024-10-10T23:30:00+00:00`
- clean dataset view status: `watch`
- raw row count: `149724`
- quarantined rows: `10`
- clean rows: `149714`
- EURUSD research readiness: `ready_for_pattern_research_with_clean_view`

Artifacts:

```text
tmp/validation-eurusd-ohlc-anomaly-triage.json
tmp/validation-eurusd-ohlc-anomaly-triage.md
tmp/validation-eurusd-clean-dataset-view.json
tmp/validation-eurusd-clean-dataset-view.md
tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv
```

The raw CSV files were not modified.

## 7. Feature and Candidate Research

### 7.1 Feature scaffold

Implemented:

```text
cajas/research/eurusd_pattern_features.py
cajas/tests/test_eurusd_pattern_features.py
```

Feature categories:

- candle body
- absolute body
- upper wick
- lower wick
- candle range
- body ratio
- bullish/bearish/doji-like flags
- multi-horizon features over:
  - `3`
  - `5`
  - `8`
  - `13`
  - `21`
  - `34`
  - `55`
- rolling range position
- efficiency ratio
- ATR-like rolling range mean
- volatility-normalized movement

Constraints:

- deterministic
- no input mutation
- no trading/order/signal columns

### 7.2 Pattern candidate pack

Implemented:

```text
cajas/research/eurusd_pattern_candidates.py
cajas/tests/test_eurusd_pattern_candidates.py

cajas/reports/validation_eurusd_pattern_candidate_pack.py
cajas/scripts/build_eurusd_pattern_candidate_pack.py
cajas/tests/test_validation_eurusd_pattern_candidate_pack.py
```

Candidate types:

- `compression_candidate`
- `expansion_candidate`
- `short_trend_up_candidate`
- `short_trend_down_candidate`
- `mid_trend_up_candidate`
- `mid_trend_down_candidate`
- `upper_wick_rejection_candidate`
- `lower_wick_rejection_candidate`
- `doji_indecision_candidate`
- `possible_false_breakout_candidate`

Current output:

- candidate pack status: `ready`
- total candidates: `206492`
- balanced review samples: `500`
- sample count: `50` per type

Candidate counts by type:

```text
short_trend_up_candidate: 35289
short_trend_down_candidate: 32361
possible_false_breakout_candidate: 26987
lower_wick_rejection_candidate: 26751
upper_wick_rejection_candidate: 26419
doji_indecision_candidate: 17891
mid_trend_up_candidate: 15134
mid_trend_down_candidate: 14176
expansion_candidate: 8182
compression_candidate: 3302
```

Artifacts:

```text
tmp/eurusd/EURUSD_15m_pattern_candidates.csv
tmp/eurusd/EURUSD_15m_pattern_review_samples.csv
tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl
tmp/validation-eurusd-pattern-candidate-pack.json
tmp/validation-eurusd-pattern-candidate-pack.md
```

Candidate tags are review-only and are not trading signals.

## 8. Human Review Schema and Template

Implemented:

```text
cajas/reports/validation_eurusd_pattern_review_qa.py
cajas/scripts/build_eurusd_pattern_review_qa_report.py
cajas/tests/test_validation_eurusd_pattern_review_qa.py

cajas/reports/validation_eurusd_pattern_label_schema.py
cajas/scripts/build_eurusd_pattern_label_schema_report.py
cajas/tests/test_validation_eurusd_pattern_label_schema.py

cajas/reports/validation_eurusd_pattern_review_template.py
cajas/scripts/build_eurusd_pattern_review_template.py
cajas/tests/test_validation_eurusd_pattern_review_template.py
```

Current state:

- pattern review QA status: `ready`
- label schema status: `ready`
- schema version: `eurusd_15m_pattern_review_v1`
- review template status: `ready`
- review template row count: `500`

Artifacts:

```text
tmp/validation-eurusd-pattern-review-qa.json
tmp/validation-eurusd-pattern-review-qa.md
tmp/validation-eurusd-pattern-label-schema.json
tmp/validation-eurusd-pattern-label-schema.md
tmp/validation-eurusd-pattern-review-template.json
tmp/validation-eurusd-pattern-review-template.md
tmp/eurusd/EURUSD_15m_pattern_review_template.csv
tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl
```

### 8.1 Label fields

Main human review fields:

- `human_pattern_label`
- `market_context`
- `direction_context`
- `structure_quality`
- `follow_through_quality`
- `review_confidence`
- `review_notes`
- `review_status`

Allowed `human_pattern_label` values:

- `valid_pattern`
- `weak_pattern`
- `false_positive`
- `unclear`
- `skip_bad_context`

Allowed `market_context` values:

- `trend`
- `range`
- `pullback`
- `transition`
- `breakout`
- `reversal_attempt`
- `high_volatility`
- `low_volatility`
- `unclear`

Allowed `direction_context` values:

- `up`
- `down`
- `neutral`
- `mixed`
- `up_pullback`
- `down_pullback`
- `reversal_up`
- `reversal_down`
- `unclear`

Legacy compatibility:

- existing `direction_context=sideways` remains accepted during transition

Numeric ratings:

- `structure_quality`: 1–5
- `follow_through_quality`: 1–5
- `review_confidence`: 1–5

Allowed `review_status` values:

- `pending`
- `reviewed`
- `needs_recheck`
- `skip`

## 9. Review Feedback Intake and Summary

Implemented:

```text
cajas/reports/validation_eurusd_pattern_review_feedback.py
cajas/scripts/build_eurusd_pattern_review_feedback_report.py
cajas/tests/test_validation_eurusd_pattern_review_feedback.py

cajas/reports/validation_eurusd_pattern_review_summary.py

## Sampling Source Range Audit

Expected source scope for this research track:

- raw EURUSD 15m Bid source should cover years 2020–2024
- path: `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv`

Read-only source lineage audit:

- `PYTHONPATH=. ./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_sampling_source_range_report`
- outputs:
  - `tmp/validation-eurusd-sampling-source-range.json`
  - `tmp/validation-eurusd-sampling-source-range.md`

Coverage warnings should be treated as rebuild diagnostics only:

- do not auto-reset or auto-regenerate active review batch artifacts
- any rebuild remains explicit/manual
cajas/scripts/build_eurusd_pattern_review_summary_report.py
cajas/tests/test_validation_eurusd_pattern_review_summary.py
```

Current state:

- review feedback status: `awaiting_review_input`
- reviewed count: `0`
- pending count: `500`
- review summary status: `awaiting_review_input`
- EURUSD research readiness: `ready_for_pattern_research_with_clean_view`
- next recommended action: `complete_human_review_template`

Artifacts:

```text
tmp/validation-eurusd-pattern-review-feedback.json
tmp/validation-eurusd-pattern-review-feedback.md
tmp/validation-eurusd-pattern-review-summary.json
tmp/validation-eurusd-pattern-review-summary.md
```

Missing review input is a normal non-blocking state.

## 10. First Review Batch

Implemented:

```text
cajas/reports/validation_eurusd_pattern_review_batch.py
cajas/scripts/build_eurusd_pattern_review_batch.py
cajas/tests/test_validation_eurusd_pattern_review_batch.py

cajas/reports/validation_eurusd_pattern_review_guide.py
cajas/scripts/build_eurusd_pattern_review_guide.py
cajas/tests/test_validation_eurusd_pattern_review_guide.py

cajas/reports/validation_eurusd_pattern_review_batch_completion.py
cajas/scripts/build_eurusd_pattern_review_batch_completion_report.py
cajas/tests/test_validation_eurusd_pattern_review_batch_completion.py
```

Current state:

- first review batch status: `ready` or `watch` (watch is non-blocking when diversity fallback is used)
- batch row count: `100`
- 10 samples per candidate type
- default diversification policy:
  - `balanced_by_candidate_type=true`
  - `min_gap_bars_between_samples=8`
  - `max_samples_per_day=8`
  - `prefer_time_diversity=true`
- review batch report includes:
  - `diversification_settings`
  - `diversity_summary` (`unique_days`, `cluster_warning_count`, min/median time gaps)
- guide status: `ready`
- schema version: `eurusd_15m_pattern_review_v1`
- batch completion status: `awaiting_completed_batch`
- blocking: `false`
- reviewed count: `0`
- pending count: `100`
- next action: `fill_batch_001_review`

Artifacts:

```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl
tmp/validation-eurusd-pattern-review-batch-001.json
tmp/validation-eurusd-pattern-review-batch-001.md
tmp/validation-eurusd-pattern-review-guide.json
tmp/validation-eurusd-pattern-review-guide.md
tmp/validation-eurusd-pattern-review-batch-001-completion.json
tmp/validation-eurusd-pattern-review-batch-001-completion.md
```

The human reviewer should eventually save completed batch results to:

```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
```

## 11. Local GUI Review App

The desired review workflow is chart-first, not CSV-first.

Principle:

```text
GUI = human review interface
CSV/JSONL = durable storage/interchange format
```

Preferred local GUI stack:

- Streamlit
- Plotly

Expected files:

```text
cajas/apps/eurusd_pattern_review_app.py
cajas/research/eurusd_pattern_review_gui.py
cajas/tests/test_eurusd_pattern_review_gui.py

cajas/reports/validation_eurusd_pattern_review_gui.py
cajas/scripts/build_eurusd_pattern_review_gui_report.py
cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Expected run command:

```bash
./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_pattern_review_app.py
```

Optional GUI dependency install:

```bash
./.venv-qlib313/bin/python -m pip install streamlit plotly
```

Expected GUI behavior:

- load clean view CSV
- load review batch CSV
- show interactive candlestick chart around sample timestamp
- highlight target bar
- show candidate metadata and reason codes
- filter by candidate type and review status
- navigate previous/next sample
- fill label schema fields
- save/update completed CSV
- resume progress from existing completed CSV
- provide compact mode (enabled by default) for high-frequency manual review
- allow compact chart height adjustment from sidebar controls
- show compact one-line chart diagnostics with expandable detailed debug info
- use one-line compact `Review Notes` input in the main control row
- keep detailed debug info read-only and positioned below save/reset action buttons
- save actions contract: Save writes/updates current sample by `sample_id`, Save and Next saves first then advances, Reset Form resets visible controls only and does not delete saved CSV rows
- persistence status contract: after save/save-and-next, GUI status must show sample id, CSV path, JSONL path, insert/update result, and current sample index
- storage split contract: CSV is latest duplicate-safe completed state by `sample_id`; JSONL is append-friendly save-event history for audit/interchange
- JSONL append errors must be surfaced explicitly and must not silently invalidate successful CSV writes
- review completion closure contract: publish completion status (`awaiting_review_input|in_progress|ready_for_summary|warning|blocked`) with completed/pending sample ids, CSV/JSONL consistency checks, and explicit reviewer next action

Completed output path:

```text
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
```

No labels should be invented by automation. Only human-entered values are saved.

## 12. Completed Batch Intake and Merge

Expected future/next workflow:

```text
cajas/reports/validation_eurusd_pattern_review_batch_merge.py
cajas/scripts/build_eurusd_pattern_review_batch_merge_report.py
cajas/tests/test_validation_eurusd_pattern_review_batch_merge.py
```

Behavior:

- if completed batch is missing:
  - status: `awaiting_completed_batch`
  - non-blocking
- if completed batch exists:
  - validate schema
  - merge into:
    - `tmp/eurusd/EURUSD_15m_pattern_review_completed.csv`
  - avoid duplicate `sample_id`
  - regenerate feedback and summary

Expected artifacts:

```text
tmp/validation-eurusd-pattern-review-batch-001-merge.json
tmp/validation-eurusd-pattern-review-batch-001-merge.md
tmp/eurusd/EURUSD_15m_pattern_review_completed.csv
tmp/validation-eurusd-pattern-review-feedback.json
tmp/validation-eurusd-pattern-review-feedback.md
tmp/validation-eurusd-pattern-review-summary.json
tmp/validation-eurusd-pattern-review-summary.md
```

## 13. Future Outcome Analysis

Only after enough human-reviewed rows exist should outcome analysis begin.

Potential modules:

```text
cajas/research/eurusd_pattern_outcomes.py
cajas/reports/validation_eurusd_pattern_outcome_analysis.py
cajas/scripts/build_eurusd_pattern_outcome_analysis_report.py
cajas/tests/test_eurusd_pattern_outcomes.py
cajas/tests/test_validation_eurusd_pattern_outcome_analysis.py
```

Potential outcome windows:

- 4 bars
- 8 bars
- 16 bars
- 32 bars

Potential metrics:

- max favorable movement
- max adverse movement
- close-to-close move
- volatility-normalized movement
- follow-through consistency
- invalidation behavior

Important:

- outcome analysis is research only
- not a trading signal
- not strategy execution
- not PnL optimization yet

## 14. Future Offline Strategy Hypotheses

Only after:

1. enough human review
2. feedback summary
3. candidate-rule refinement
4. outcome analysis

should offline strategy hypotheses be considered.

Possible future reports:

```text
validation_eurusd_strategy_hypothesis_pack.py
validation_eurusd_strategy_hypothesis_backtest_readiness.py
```

Even then:

- no live trading
- no broker
- no paper execution
- no order routing
- no production deployment

## 15. Current Artifact Map

### Data

```text
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv
```

### Candidates and review

```text
tmp/eurusd/EURUSD_15m_pattern_candidates.csv
tmp/eurusd/EURUSD_15m_pattern_review_samples.csv
tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl
tmp/eurusd/EURUSD_15m_pattern_review_template.csv
tmp/eurusd/EURUSD_15m_pattern_review_template.jsonl
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.jsonl
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
tmp/eurusd/EURUSD_15m_pattern_review_completed.csv
```

### GUI

```text
cajas/apps/eurusd_pattern_review_app.py
cajas/research/eurusd_pattern_review_gui.py
tmp/validation-eurusd-pattern-review-gui.json
tmp/validation-eurusd-pattern-review-gui.md
```

### Reports

```text
tmp/validation-eurusd-dataset-contract.md
tmp/validation-eurusd-dataset-audit.md
tmp/validation-eurusd-ohlc-anomaly-triage.md
tmp/validation-eurusd-clean-dataset-view.md
tmp/validation-eurusd-pattern-candidate-pack.md
tmp/validation-eurusd-pattern-review-qa.md
tmp/validation-eurusd-pattern-label-schema.md
tmp/validation-eurusd-pattern-review-template.md
tmp/validation-eurusd-pattern-review-feedback.md
tmp/validation-eurusd-pattern-review-summary.md
tmp/validation-eurusd-pattern-review-batch-001.md
tmp/validation-eurusd-pattern-review-guide.md
tmp/validation-eurusd-pattern-review-batch-001-completion.md
tmp/validation-eurusd-research-readiness.md
```

## 16. How to Start Using the System

### 16.1 Install optional GUI dependencies

```bash
./.venv-qlib313/bin/python -m pip install streamlit plotly
```

### 16.2 Run local review GUI

```bash
./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_pattern_review_app.py
```

### 16.3 Review workflow

1. Open the local GUI.
2. Load or confirm paths:
   - clean view CSV
   - review batch CSV
   - label schema JSON
   - completed output CSV
3. Select a sample.
4. Inspect EURUSD 15m candlestick context around the sample timestamp.
5. Read candidate type, confidence score, review priority, reason codes, and supporting metrics.
6. Fill the human review fields.
7. Save.
8. Continue through the batch.
9. When enough rows are complete, run completed-batch intake/merge.
10. Review feedback summary.
11. Decide whether to refine rules, expand batches, or begin outcome analysis.

## 17. Daily Validation Commands

Fast validation:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

Hygiene:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

## 18. Git Workflow

For new work:

```bash
git checkout main
git pull origin main
git checkout -b phase-<name>
```

After validation:

```bash
git push origin phase-<name>
```

Then the human user opens a PR and merges manually on GitHub.

Do not perform automated merges.

## 19. How to Use This Roadmap

Use this roadmap in two ways.

### Audit mode

Ask an agent to compare the current repo to this roadmap and report:

- completed milestones
- missing milestones
- blocked states
- next safest phase

### Implementation mode

Ask an agent to implement one milestone at a time, with:

- focused tests
- generated artifacts
- fast validation
- hygiene checks
- manual GitHub merge

Do not implement the whole roadmap in one giant commit unless explicitly requested.

## 20. Final Target

The final practical target is:

- a stable local GUI where the human can inspect EURUSD 15m candlestick candidates visually
- label candidate quality and context
- save completed review data
- summarize human feedback
- refine pattern candidate rules
- later perform offline outcome analysis
- later consider offline strategy hypotheses

This is the bridge from raw market data to research evidence.

It is not a trading execution system.


## Candidate Audit Layer

Before scaling manual review, run a read-only candidate audit that validates:
- causality vs future-aware review-sampling filters
- selection explainability fields
- same-timestamp multi-label conflicts
- same-region/near-duplicate concentration
- year/month/session/volatility coverage

Commands:

```bash
PYTHONPATH=. ./.venv-qlib313/bin/python -m cajas.scripts.build_eurusd_candidate_audit_report
./scripts/validate_eurusd_candidate_audit.sh
```

Audit outputs:
- `tmp/validation-eurusd-candidate-audit.json`
- `tmp/validation-eurusd-candidate-audit.md`

This audit is read-only and does not reset or rebuild active review artifacts.
