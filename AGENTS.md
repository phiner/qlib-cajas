# AGENTS.md

This repository is `qlib-cajas`, a personal research fork of Microsoft Qlib.

The purpose of this repo is to explore Qlib-based market recognition workflows for forex / K-line research. It is **not** a live trading system, not an automated order execution system, and not financial advice.

## 1. Core Principles

- Do **not** modify Qlib core unless explicitly requested.
- Prefer adding project-specific code under `cajas/`.
- Keep upstream compatibility with `microsoft/qlib` where practical.
- Treat this repository as a research sandbox for market recognition, dataset preparation, labeling, model experiments, and evaluation.
- Do not introduce live trading, broker API integration, account login, real-money order submission, or automatic execution logic.
- Do not commit raw market data files unless explicitly approved.

## 2. Current Research Direction

The current direction is:

- Build a lightweight `cajas/` research layer inside the Qlib fork.
- Start with EURUSD 15-minute bid data.
- Prepare cleaned OHLCV datasets.
- Generate basic K-line features.
- Generate a first supervised label: `future_direction_8`.
- Use Qlib as a research foundation, not as a live trading engine.

Initial dataset example:

```text
~/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
```

Expected raw CSV columns:

```text
Time (UTC),Open,High,Low,Close,Volume
```

Example timestamp format:

```text
2025.01.01 22:00:00
```

## 3. Directory Rules

Preferred project-specific structure:

```text
cajas/
  README.md
  scripts/
    prepare_fx_dataset.py
  configs/
    fx_eurusd_15m_lightgbm_future_direction_8.yaml
  data_examples/
    README.md
```

Documentation and task prompts may be stored under:

```text
taskDocs/
```

`taskDocs/` should be ignored by Git unless the user explicitly decides to version selected task documents.

Do not place raw CSV market data inside tracked repo paths.

Recommended local-only paths:

```text
data/
tmp/
outputs/
artifacts/
```

These should generally remain ignored unless the user explicitly requests otherwise.

## 4. Git Rules

### Branching

Use descriptive branches. Examples:

```bash
git checkout -b cajas/market-recognition-phase-0
git checkout -b cajas/fx-dataset-prep
git checkout -b cajas/lightgbm-baseline-config
```

Do not work directly on `main` unless the user explicitly says so.

### Remote Safety

This repo usually has:

```text
origin   git@github.com:phiner/qlib-cajas.git
upstream https://github.com/microsoft/qlib.git
```

`origin` is the user's fork.

`upstream` is Microsoft Qlib.

Do not push to upstream. It is recommended to disable upstream push:

```bash
git remote set-url --push upstream DISABLE
```

## Codex Communication and Push Policy

- Codex must communicate with the user in English only.
- Codex must not use Chinese in progress updates, questions, or completion reports unless explicitly requested by the user.
- Codex must not run `git push`.
- Codex may create local commits after validation.
- After local commits, Codex must stop and report:
  - commit hashes
  - `git status --short`
  - exact `git push` command for the user to run manually.

### Commit Style

Use small, focused commits.

Preferred commit prefixes:

```text
docs:      documentation only
feat:      new feature or scaffold
fix:       bug fix
refactor:  code movement without semantic change
test:      tests or validation only
chore:     repo maintenance
config:    config files only
data:      schema/sample data docs only, not raw large data
```

Examples:

```bash
git commit -m "docs: add cajas research layer overview"
git commit -m "feat: add EURUSD 15m dataset preparation script"
git commit -m "config: add first future direction experiment draft"
git commit -m "chore: ignore local task docs"
```

### Commit Boundaries

Avoid mixing unrelated changes.

Good split:

1. `.gitignore` update
2. `cajas/README.md`
3. dataset preparation script
4. config draft
5. docs for data examples

Bad split:

- editing Qlib core, adding dataset script, changing examples, and adding model outputs in one commit.

### Before Committing

Run at least:

```bash
git status
python -m py_compile cajas/scripts/prepare_fx_dataset.py
```

If tests exist or are added, run the relevant tests.

If a script is changed, run its `--help` if available:

```bash
python cajas/scripts/prepare_fx_dataset.py --help
```

## 5. Coding Rules

## Python Package Init Policy

- Python package initializer files must always be named `__init__.py`.
- Never create package initializer files named `init.py`.
- If a new Python package directory is added and package imports are needed, create `__init__.py`.
- Before every local commit, run:

```bash
find cajas -path "*/init.py" -print
```

- The command above must produce no output.
- If any `cajas/**/init.py` file exists, fix it with `git mv`:

```bash
git mv path/to/init.py path/to/__init__.py
```

- Do not report package init cleanup as complete while any `cajas/**/init.py` file remains.

### Python

- Prefer standard library plus existing project dependencies.
- Avoid adding heavy dependencies unless clearly needed.
- Use `argparse` for scripts.
- Scripts should have clear `--input`, `--output`, `--symbol`, and `--timeframe` arguments where applicable.
- Fail with clear error messages when input files or required columns are missing.
- Do not silently overwrite important outputs unless the behavior is documented.
- Keep scripts reproducible and deterministic.

### Data Preparation

For EURUSD 15m data preparation:

- Read raw CSV with columns:
  - `Time (UTC)`
  - `Open`
  - `High`
  - `Low`
  - `Close`
  - `Volume`
- Normalize column names to lowercase snake case.
- Parse timestamp as UTC-aware or consistently documented UTC timestamp.
- Sort by timestamp ascending.
- Drop or report invalid rows.
- Generate basic K-line features such as:
  - return
  - candle body
  - upper shadow
  - lower shadow
  - high-low range
  - close-open change
  - rolling returns / volatility where appropriate
- Generate label:
  - `future_direction_8`
  - based on close price after 8 bars
  - use stable, documented class names
  - do not use future information in feature columns

Recommended first label semantics:

```text
future_return_8 = close.shift(-8) / close - 1
future_direction_8:
  up      if future_return_8 > threshold
  down    if future_return_8 < -threshold
  flat    otherwise
```

Default threshold may be conservative and documented, for example:

```text
0.0002
```

Do not claim this label is profitable or tradable. It is only a first market-recognition target.

## 6. Qlib Core Boundary

Do not edit these unless explicitly requested:

```text
qlib/
examples/
scripts/
tests/
```

Exceptions:

- Reading files for understanding is allowed.
- Adding isolated `cajas/` files is preferred.
- Adding `cajas`-specific examples may be allowed under `cajas/`, not Qlib's original examples, unless requested.

If a Qlib core change seems necessary, stop and document:

1. why it seems necessary,
2. what alternative extension points were checked,
3. what minimal patch would be needed,
4. how it affects upstream compatibility.

## 7. Data Safety Rules

Do not commit:

- raw EURUSD CSV files,
- large generated datasets,
- model artifacts,
- broker/account credentials,
- API keys,
- personal secrets,
- `.env` files.

Use `.gitignore` for local data and outputs.

Suggested ignored paths:

```gitignore
taskDocs/
data/
tmp/
outputs/
artifacts/
*.parquet
*.feather
*.pkl
*.joblib
*.onnx
.env
```

Small documentation examples may be committed if they contain no sensitive or licensed data.

## 8. Documentation Rules

Every new research layer should include a short README explaining:

- purpose,
- current scope,
- what is intentionally excluded,
- how to run the script,
- input format,
- output format,
- validation notes.

Avoid overstating results.

Use wording like:

```text
market recognition experiment
research dataset
first supervised target
baseline config draft
```

Avoid wording like:

```text
profitable strategy
automated trading system
guaranteed signal
production trading model
```

## 9. Validation Rules

For Phase 0 scaffold, minimum validation:

```bash
python -m py_compile cajas/scripts/prepare_fx_dataset.py
python cajas/scripts/prepare_fx_dataset.py --help
```

If the input CSV exists, also run a small real-data smoke test:

```bash
python cajas/scripts/prepare_fx_dataset.py \
  --input "$HOME/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv" \
  --output tmp/cajas/eurusd_15m_future_direction_8.csv \
  --symbol EURUSD \
  --timeframe 15m
```

Then inspect:

```bash
head tmp/cajas/eurusd_15m_future_direction_8.csv
```

## 10. Reporting Format for Codex / AI Agent

When finishing a task, report in this format:

```text
Summary:
- ...

Files changed:
- ...

Validation:
- [pass/fail] command ...

Notes / risks:
- ...

Next suggested step:
- ...
```

Do not produce long essays unless the user asks for one.

## 11. Current Phase 0 Goal

Implement the first scaffold for Qlib-based market recognition research:

- Add `.gitignore` entry for `taskDocs/`.
- Add `cajas/README.md`.
- Add `cajas/scripts/prepare_fx_dataset.py`.
- Add `cajas/configs/fx_eurusd_15m_lightgbm_future_direction_8.yaml`.
- Add `cajas/data_examples/README.md`.
- Do not modify Qlib core.
- Do not commit raw data.
- Validate the script with `py_compile`, `--help`, and a real-data smoke test if the CSV path exists.
