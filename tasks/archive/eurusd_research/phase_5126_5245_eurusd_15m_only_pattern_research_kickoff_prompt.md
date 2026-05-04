# Phase 5126–5245 — EURUSD Research Dataset Entry and Pattern Study Kickoff

## Context

The Qlib Base / qlib-cajas infrastructure is now in routine maintenance mode on `main`.

Important current baseline:

- Main branch is clean and synced.
- Release readiness is `ready`.
- Final reviewer packet is `ready_for_review`.
- Post-merge mainline validation is complete.
- Routine maintenance continuation is complete.
- Repo posture:
  - keep current GitHub fork relationship from `microsoft/qlib`
  - no upstream sync planned
  - no repo migration planned
  - manual GitHub merge policy remains
- Scope so far has been offline Qlib validation automation only.
- Do not modify Qlib core.
- Do not introduce broker routing, live trading, paper trading, order execution, or timeframe aggregation.

Now return to the original project objective:

Study EURUSD historical data to research market structure, K-line / candlestick patterns, regime behavior, and strategy hypotheses in an offline, reproducible research workflow.

This phase should be the bridge from infrastructure to actual EURUSD research. It should not train production models or execute trades yet.


## User-Provided EURUSD Data Paths

Use these real local dataset files as the initial EURUSD inputs:

```text
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
```

Interpretation:

- Symbol: `EURUSD`
- Timeframe: `15m`
- Price side: `Bid`
- Coverage:
  - 2020-01-01 through 2024-12-31
  - 2025-01-01 through 2025-12-31, or partial 2025 if the file only contains data available so far
- Initial audit should support multiple input CSV files and report combined coverage.
- Do not move or mutate the original files.
- If the existing audit CLI only accepts one path, add support for repeated `--input` or comma-separated input paths.
- If column names differ from the canonical schema, add a deterministic normalization layer and document the mapping.
- Use `15m` as the fixed research timeframe.
- Do not aggregate to 1H/4H in this phase or later phases unless the human user explicitly requests it.
- Pattern research, feature computation, sample review, and offline strategy hypotheses should focus on raw EURUSD 15m Bid structure.

## Goal

Create a minimal EURUSD 15m Bid research entry layer that:

1. Defines the expected EURUSD dataset location and schema.
2. Adds a dataset audit/report for EURUSD OHLCV/bar data.
3. Adds a pattern-study scaffold for multi-horizon K-line structure features.
4. Produces reviewer-friendly artifacts summarizing whether the EURUSD dataset is ready for research.
5. Keeps everything offline, non-trading, and fixed to 15m research.

## Required Work

### 1. Define EURUSD dataset contract

Add a small contract/spec module or documentation section for EURUSD research input data.

Expected canonical input shape for this phase:

- symbol: `EURUSD`
- timeframe: fixed to `15m` for this research track
- timestamp column:
  - required
  - parseable datetime
  - monotonic increasing after sort
- OHLC columns:
  - `open`
  - `high`
  - `low`
  - `close`
- optional columns:
  - `volume`
  - `spread`
  - `source`
- constraints:
  - `high >= max(open, close, low)`
  - `low <= min(open, close, high)`
  - no duplicated timestamp after normalization
  - missing OHLC rate reported
  - large gaps reported
  - timezone handling documented
  - price precision documented

Suggested files:

- `cajas/reports/validation_eurusd_dataset_contract.py`
- `cajas/scripts/build_eurusd_dataset_contract_report.py`
- `cajas/tests/test_validation_eurusd_dataset_contract.py`

Generated artifacts:

- `tmp/validation-eurusd-dataset-contract.json`
- `tmp/validation-eurusd-dataset-contract.md`

### 2. Add EURUSD dataset audit

Add an audit report that can inspect a local CSV dataset path, for example:

`data/eurusd/EURUSD_1H.csv`

Do not require the dataset file to exist for tests. Tests should use temporary fixture CSV files.

The audit should report:

- file path
- symbol
- timeframe
- row count
- start timestamp
- end timestamp
- inferred frequency / median bar interval
- duplicated timestamp count
- missing OHLC counts
- invalid OHLC relation count
- gap summary
- price range summary
- basic return summary:
  - close-to-close return count
  - mean
  - std
  - min
  - max
- status:
  - `ready`
  - `watch`
  - `blocked`

Suggested status rules:

- `ready`:
  - file exists
  - required columns present
  - row count above a small configurable minimum
  - no invalid OHLC rows
  - duplicated timestamps zero
- `watch`:
  - minor gaps or optional columns missing
- `blocked`:
  - file missing
  - required columns missing
  - invalid OHLC rows exist
  - too few rows

Suggested files:

- `cajas/reports/validation_eurusd_dataset_audit.py`
- `cajas/scripts/build_eurusd_dataset_audit_report.py`
- `cajas/tests/test_validation_eurusd_dataset_audit.py`

Generated artifacts:

- `tmp/validation-eurusd-dataset-audit.json`
- `tmp/validation-eurusd-dataset-audit.md`

### 3. Add multi-horizon K-line pattern feature scaffold

Create a first offline feature scaffold for pattern research. This is not a trading strategy yet.

Suggested module:

- `cajas/research/eurusd_pattern_features.py`

If `cajas/research/` does not exist, create it without adding `__init__.py` unless current project policy allows it. Respect the existing no-`init.py` hygiene rule.

Features should be deterministic and simple:

For each bar, compute or define functions for:

- candle body:
  - `body = close - open`
  - `body_abs`
  - `upper_wick`
  - `lower_wick`
  - `range = high - low`
  - `body_ratio = body_abs / range`
- direction:
  - bullish / bearish / doji-like
- multi-horizon slopes using close:
  - horizons: `3, 5, 8, 13, 21, 34, 55`
  - normalized slope or percent change over horizon
- rolling range position:
  - close position in rolling high-low window
- efficiency ratio:
  - net movement / total movement over horizon
- ATR-like range average:
  - simple rolling mean of high-low range
- volatility-normalized movement:
  - close change over horizon divided by ATR-like range

Add tests with small in-memory DataFrames or CSV fixtures.

Suggested tests:

- feature columns are produced
- no mutation of input data unless documented
- known small fixture has expected body/wick/slope values
- handles short datasets gracefully
- no trading signal/order output is produced

### 4. Add EURUSD pattern research readiness packet

Create a compact report that combines:

- Qlib Base maintenance continuation status
- EURUSD dataset contract status
- EURUSD dataset audit status
- feature scaffold status
- scope boundary

Suggested files:

- `cajas/reports/validation_eurusd_research_readiness.py`
- `cajas/scripts/build_eurusd_research_readiness_report.py`
- `cajas/tests/test_validation_eurusd_research_readiness.py`

Generated artifacts:

- `tmp/validation-eurusd-research-readiness.json`
- `tmp/validation-eurusd-research-readiness.md`

Expected statuses:

- `ready_for_pattern_research`
- `watch`
- `blocked`

Status should be `ready_for_pattern_research` only if:

- base maintenance continuation is ready/routine
- dataset contract is ready
- dataset audit is ready or watch with non-blocking gaps
- feature scaffold validation passes

### 5. Documentation

Update docs:

- `cajas/docs/dataset_quality_loop.md`
- `cajas/docs/current_qlib_base_stage_archive.md`
- `cajas/README.md`

Add a new short document if useful:

- `cajas/docs/eurusd_pattern_research_kickoff.md`

Document:

- why this phase exists
- expected EURUSD data location
- expected schema
- what the first pattern features are
- what is explicitly out of scope:
  - no live trading
  - no broker routing
  - no order generation
  - no production model training
  - no Qlib core changes
- next research path:
  1. validate EURUSD dataset
  2. compute pattern features
  3. create manual label/review examples
  4. test simple non-execution strategy hypotheses offline
  5. only later consider ML labels or model training

### 6. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_validation_eurusd_dataset_contract.py   cajas/tests/test_validation_eurusd_dataset_audit.py   cajas/tests/test_validation_eurusd_research_readiness.py
```

Run feature tests if separate:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_features.py
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

Start from latest `main`:

```bash
git checkout main
git pull origin main
git checkout -b phase-eurusd-pattern-research-kickoff
```

Suggested commits:

```bash
git add   cajas/reports/validation_eurusd_dataset_contract.py   cajas/scripts/build_eurusd_dataset_contract_report.py   cajas/tests/test_validation_eurusd_dataset_contract.py   cajas/reports/validation_eurusd_dataset_audit.py   cajas/scripts/build_eurusd_dataset_audit_report.py   cajas/tests/test_validation_eurusd_dataset_audit.py

git commit -m "feat: add EURUSD dataset research validation"

git add   cajas/research/eurusd_pattern_features.py   cajas/tests/test_eurusd_pattern_features.py   cajas/reports/validation_eurusd_research_readiness.py   cajas/scripts/build_eurusd_research_readiness_report.py   cajas/tests/test_validation_eurusd_research_readiness.py

git commit -m "feat: add EURUSD pattern research readiness scaffold"

git add   cajas/docs/current_qlib_base_stage_archive.md   cajas/docs/dataset_quality_loop.md   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/README.md   tasks/phase_5126_5245_eurusd_pattern_research_kickoff_prompt.md

git commit -m "docs: document EURUSD pattern research kickoff"
```

Do not perform automated merge operations.

If ready, push the branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

## Final Response Required

When finished, report:

- active branch
- commits created
- files changed
- generated artifacts
- EURUSD dataset contract status
- EURUSD dataset audit status
- EURUSD research readiness status
- feature scaffold summary
- release/base maintenance status if referenced
- validation results
- fast validation runtime
- push status
- manual GitHub merge instruction
- confirmation that no automated merge was performed


## Fixed-Timeframe Clarification

The user explicitly clarified that this research should not use 1H/4H aggregation.

Required interpretation:

- Research timeframe: `15m`
- Data side: `Bid`
- Symbol: `EURUSD`
- Do not add aggregation logic.
- Do not propose 1H/4H derived bars.
- Do not make aggregation a default future path.
- Any future timeframe expansion requires a separate explicit user request.

The first useful research outputs should be based on raw 15m behavior:

- 15m candle body / wick / range patterns
- 15m volatility-normalized movement
- 15m multi-horizon slopes over bar counts such as `3, 5, 8, 13, 21, 34, 55`
- 15m compression / expansion regimes
- 15m false-break / breakout / pullback candidates
- 15m manual review sample queues
