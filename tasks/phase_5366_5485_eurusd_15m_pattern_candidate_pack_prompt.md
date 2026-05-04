# Phase 5366–5485 — EURUSD 15m Pattern Candidate Sample Pack

## Context

You are working in the Qlib Base / qlib-cajas repository.

The project objective is now focused on EURUSD 15m Bid pattern research.

Current baseline from Phase 5126–5245 and Phase 5246–5365:

- Branch currently used: `phase-eurusd-pattern-research-kickoff`
- Raw input data:
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv`
  - `/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv`
- Research timeframe: fixed to `15m`
- Price side: `Bid`
- Do not aggregate to 1H/4H.
- Do not introduce live trading, paper trading, broker routing, order generation, or Qlib core modifications.

Current data state:

- Raw anomaly triage status: `blocked`
- Raw anomaly row count: `10`
- Raw anomaly timestamp range:
  - earliest: `2024-10-09T23:45:00+00:00`
  - latest: `2024-10-10T23:30:00+00:00`
- Raw CSV files were not modified.
- Clean dataset view status: `watch`
- Raw row count: `149724`
- Quarantined row count: `10`
- Clean row count: `149714`
- Clean view path:
  - `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`
- Quarantine path:
  - `tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv`
- EURUSD research readiness:
  - `ready_for_pattern_research_with_clean_view`
- Feature scaffold already exists:
  - `cajas/research/eurusd_pattern_features.py`
  - candle geometry
  - direction flags
  - 15m multi-horizon features over `3,5,8,13,21,34,55`
- Prior validation:
  - focused EURUSD tests passed
  - fast validation passed
  - hygiene clean

Important: This phase should create research samples and candidate labels for human review. It should not create a trading strategy yet.

## Goal

Create a deterministic EURUSD 15m pattern candidate sample pack from the clean dataset view.

The output should help the human review real 15m market structures such as:

- compression / narrow range
- expansion / large range
- short-term trend continuation
- trend exhaustion
- false breakout candidate
- breakout pullback candidate
- long upper wick rejection
- long lower wick rejection
- doji-like indecision
- range-bound / chop candidate

This phase should produce reviewable sample artifacts, not trading orders or strategy execution.

## Required Work

### 1. Add EURUSD pattern candidate detector

Create:

`cajas/research/eurusd_pattern_candidates.py`

Use the existing feature scaffold from:

`cajas/research/eurusd_pattern_features.py`

Input:

- cleaned EURUSD 15m CSV path
- deterministic feature DataFrame

Output:

- candidate rows with pattern tags and supporting metrics

Candidate types should be rule-based and explainable, not ML-based.

Suggested candidate definitions:

1. `compression_candidate`
   - recent rolling range or ATR-like range is low relative to a longer rolling baseline
   - include compression ratio metric

2. `expansion_candidate`
   - current range is high relative to recent ATR-like range
   - include range expansion ratio

3. `short_trend_up_candidate`
   - slopes for 3/5/8 bars are positive
   - close position in recent range is high

4. `short_trend_down_candidate`
   - slopes for 3/5/8 bars are negative
   - close position in recent range is low

5. `mid_trend_up_candidate`
   - slopes for 13/21 bars positive
   - efficiency ratio above threshold

6. `mid_trend_down_candidate`
   - slopes for 13/21 bars negative
   - efficiency ratio above threshold

7. `upper_wick_rejection_candidate`
   - upper wick large relative to range/body
   - close below candle midpoint or bearish body

8. `lower_wick_rejection_candidate`
   - lower wick large relative to range/body
   - close above candle midpoint or bullish body

9. `doji_indecision_candidate`
   - body ratio small
   - range non-zero

10. `possible_false_breakout_candidate`
   - previous local high/low break followed by close back inside recent range
   - keep this conservative and explainable

Do not produce buy/sell signals. Candidate tags are for review only.

Each candidate row should include:

- timestamp
- source row index if available
- open/high/low/close
- candidate_type
- confidence_score between 0 and 1
- reason_codes list
- supporting metrics:
  - body_ratio
  - upper_wick_ratio
  - lower_wick_ratio
  - range
  - relevant slopes
  - efficiency ratio where applicable
  - rolling range position where applicable
- lookback bars used
- review_priority:
  - `high`
  - `medium`
  - `low`

### 2. Add candidate sample pack report

Create:

`cajas/reports/validation_eurusd_pattern_candidate_pack.py`

The report should summarize a candidate pack generated from the clean view.

Report fields:

- `status`
  - `ready` if candidates are generated and inputs are valid
  - `watch` if candidates are generated but some candidate types are sparse/missing
  - `blocked` if clean view is missing or invalid
- `input_clean_view_path`
- `row_count`
- `candidate_count`
- `candidate_count_by_type`
- `sample_count_by_type`
- `time_range`
- `horizons`
  - `[3,5,8,13,21,34,55]`
- `scope_boundary`
  - candidate review only
  - no trading signals
  - no order generation
  - no aggregation
- `output_paths`
- `recommendation`
  - `review_candidate_samples`

Generated artifacts:

- `tmp/validation-eurusd-pattern-candidate-pack.json`
- `tmp/validation-eurusd-pattern-candidate-pack.md`

### 3. Add CLI builder

Create:

`cajas/scripts/build_eurusd_pattern_candidate_pack.py`

CLI requirements:

- `--clean-view-csv`
  - default: `tmp/eurusd/EURUSD_15m_Bid_clean_view.csv`
- `--output-candidates-csv`
  - default: `tmp/eurusd/EURUSD_15m_pattern_candidates.csv`
- `--output-samples-csv`
  - default: `tmp/eurusd/EURUSD_15m_pattern_review_samples.csv`
- `--output-samples-jsonl`
  - default: `tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl`
- `--output-json`
  - default: `tmp/validation-eurusd-pattern-candidate-pack.json`
- `--output-md`
  - default: `tmp/validation-eurusd-pattern-candidate-pack.md`
- `--max-samples-per-type`
  - default: `50`
- `--min-confidence`
  - default: `0.6`

Behavior:

- read clean view
- compute features
- detect candidates
- write all candidates CSV
- write balanced review samples CSV/JSONL
- write report JSON/Markdown
- never mutate raw CSV or clean view
- no trading signal/order columns named `buy`, `sell`, `long`, `short`, `order`, `position`, or `target_position`

Note: Terms like trend up/down in candidate names are okay, but avoid action terms.

### 4. Add tests

Create:

- `cajas/tests/test_eurusd_pattern_candidates.py`
- `cajas/tests/test_validation_eurusd_pattern_candidate_pack.py`

Test scenarios:

1. Candidate detector returns expected columns.
2. Candidate detector produces deterministic output on a small fixture.
3. Compression/expansion candidates can be detected on synthetic data.
4. Wick rejection candidates can be detected on synthetic candles.
5. Candidate rows include reason codes and supporting metrics.
6. No trading/order/signal columns are produced.
7. Report returns `ready` when candidates exist and inputs are valid.
8. Report returns `blocked` when clean view file is missing.
9. Sample pack respects `max_samples_per_type`.
10. Markdown states candidate review only and no trading signals.

### 5. Integrate with EURUSD research readiness

Update:

- `cajas/reports/validation_eurusd_research_readiness.py`
- `cajas/scripts/build_eurusd_research_readiness_report.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Add optional input for pattern candidate pack report.

Expected behavior:

- If clean view is ready/watch non-blocking and candidate pack is ready/watch, readiness may include:
  - `pattern_candidate_pack_status`
  - `pattern_candidate_count`
  - `next_action=review_pattern_samples`
- Do not require the candidate pack for base data readiness unless explicitly provided.
- Do not downgrade a clean-view-ready state solely because candidate type distribution is sparse; use `watch` where appropriate.

### 6. Documentation

Update:

- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/README.md`

Document:

- clean view is the approved input for pattern sample generation
- raw data remains immutable
- candidate samples are for human review only
- candidate tags are not trading signals
- fixed timeframe remains EURUSD 15m Bid
- no aggregation to 1H/4H
- no broker/order/live trading scope

### 7. Generate real-data artifacts

Run against the clean view:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_pattern_candidate_pack.py   --clean-view-csv tmp/eurusd/EURUSD_15m_Bid_clean_view.csv   --output-candidates-csv tmp/eurusd/EURUSD_15m_pattern_candidates.csv   --output-samples-csv tmp/eurusd/EURUSD_15m_pattern_review_samples.csv   --output-samples-jsonl tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl   --output-json tmp/validation-eurusd-pattern-candidate-pack.json   --output-md tmp/validation-eurusd-pattern-candidate-pack.md   --max-samples-per-type 50   --min-confidence 0.6
```

Then regenerate EURUSD research readiness with the candidate pack report input.

Expected outputs:

- `tmp/eurusd/EURUSD_15m_pattern_candidates.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_samples.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_samples.jsonl`
- `tmp/validation-eurusd-pattern-candidate-pack.json`
- `tmp/validation-eurusd-pattern-candidate-pack.md`
- regenerated `tmp/validation-eurusd-research-readiness.json/.md`

### 8. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_eurusd_pattern_features.py   cajas/tests/test_eurusd_pattern_candidates.py   cajas/tests/test_validation_eurusd_pattern_candidate_pack.py   cajas/tests/test_validation_eurusd_research_readiness.py
```

Run fast validation:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

Run hygiene:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run py_compile for changed Python modules.

## Branch / Commit Guidance

Continue on the current EURUSD branch if Phase 5126–5365 has not been merged yet:

```bash
git checkout phase-eurusd-pattern-research-kickoff
git status --short --branch
```

If it has already been merged, start a new branch from latest main:

```bash
git checkout main
git pull origin main
git checkout -b phase-eurusd-15m-pattern-candidate-pack
```

Suggested commits:

```bash
git add   cajas/research/eurusd_pattern_candidates.py   cajas/tests/test_eurusd_pattern_candidates.py   cajas/reports/validation_eurusd_pattern_candidate_pack.py   cajas/scripts/build_eurusd_pattern_candidate_pack.py   cajas/tests/test_validation_eurusd_pattern_candidate_pack.py

git commit -m "feat: add EURUSD 15m pattern candidate pack"

git add   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: surface EURUSD pattern candidate readiness"

git add   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/README.md   tasks/phase_5366_5485_eurusd_15m_pattern_candidate_pack_prompt.md

git commit -m "docs: document EURUSD pattern candidate review"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

or, if using a new branch:

```bash
git push origin phase-eurusd-15m-pattern-candidate-pack
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- candidate pack status
- candidate count
- candidate counts by type
- sample counts by type
- sample output paths
- EURUSD research readiness status
- next recommended action
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that no trading signals/orders were produced
- confirmation that no automated merge was performed
