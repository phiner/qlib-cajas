# 009 — Diversify EURUSD Review Batch Sample Ordering

## Context

We are working directly on `main` in the Qlib Base / `qlib-cajas` repository.

Current EURUSD 15m GUI behavior:
- GUI works.
- Save / Save and Next works.
- Previous / Next works.
- Chart gap compression works.
- CSV/JSONL persistence works.

User observed:
- The first several review samples are in the same or very nearby market region.
- Example samples:
  - `eurusd15m_000012`
  - `eurusd15m_000015`
  - `eurusd15m_000027`
  - `eurusd15m_000030`
- These samples show very similar chart windows / same local market area.
- This is not ideal for human review because it wastes effort on near-duplicate contexts.

User request:
- Improve or configure the batch so consecutive samples are not all from the same market region.
- Do not remove useful candidate density entirely, but make review order more diverse.
- Keep CSV/JSONL only.
- No SQLite.
- Work directly on `main`.
- Do not create branches.
- Do not push automatically.

## Objective

Improve EURUSD 15m review batch generation/order so the review workflow covers more diverse market regions.

The first review batch should avoid clustering many consecutive samples from the same local time window.

## Desired Behavior

Use a moderate spacing default suitable for manual review:

```text
min_gap_bars_between_samples=8   # 8 × 15m = 2 hours
```

This avoids reviewing many near-duplicate samples in the same local move while keeping enough nearby context density for pattern comparison.

The review batch should support configurable diversification.

A good default policy:

```text
balanced_by_candidate_type=true
min_gap_bars_between_samples=8
max_samples_per_day=8
prefer_time_diversity=true
```

Interpretation for EURUSD 15m:
- `min_gap_bars_between_samples=8` means roughly 2 hours between selected sample anchors on EURUSD 15m, where possible.
- `max_samples_per_day=8` prevents one day from dominating the first batch.
- Candidate type balance should remain so each pattern category is represented.
- If constraints are too strict, degrade gracefully and fill remaining rows from available candidates.

## Required Investigation

Find the current batch/template generation code.

Search:

```bash
grep -R "pattern_review_batch" -n cajas
grep -R "review_template" -n cajas
grep -R "pattern_review_template" -n cajas
grep -R "balanced" -n cajas/reports cajas/research cajas/scripts cajas/tests
```

Likely relevant artifacts:
- `tmp/eurusd/EURUSD_15m_pattern_review_template.csv`
- `tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv`
- `tmp/eurusd/EURUSD_15m_pattern_candidates.csv`
- review template/batch report modules/scripts/tests.

Do not change completed review CSV semantics.

## Implementation Requirements

### 1. Add pure diversification helper

Add deterministic helper(s), likely in an existing EURUSD review module or `cajas/research/eurusd_pattern_review_gui.py` if no better place exists.

Suggested helper:

```python
def diversify_review_samples(
    candidates,
    *,
    sample_id_col="sample_id",
    timestamp_col="timestamp",
    candidate_type_col="candidate_type",
    target_count=100,
    min_gap_bars=8,
    max_samples_per_day=8,
    balanced_by_candidate_type=True,
    seed=0,
) -> list[dict] | pd.DataFrame:
    ...
```

Behavior:
- Sort or bucket candidates deterministically.
- Prefer candidate type balance.
- Enforce minimum distance between selected sample timestamps where possible.
- Enforce per-day cap where possible.
- Degrade gracefully if not enough candidates satisfy constraints.
- Preserve original identity fields:
  - `sample_id`
  - `timestamp`
  - `candidate_type`
  - confidence/priority/reasons fields
- Do not invent labels.

### 2. Avoid near-duplicate local windows

Add a function to detect local clustering:

```python
def summarize_sample_time_diversity(samples, timestamp_col="timestamp") -> dict:
    ...
```

Output:
- `sample_count`
- `unique_days`
- `max_samples_per_day`
- `min_gap_minutes`
- `median_gap_minutes`
- `cluster_warning_count`
- `clustered_sample_pairs`
- `status`

Suggested status:
- `diverse`: constraints satisfied or mostly satisfied
- `warning`: some clusters remain because candidates are dense or fallback was needed
- `blocked`: invalid/missing timestamps

### 3. Integrate into review batch/template creation

Where `EURUSD_15m_pattern_review_batch_001.csv` or review template is generated:
- apply diversification by default
- write diversification settings into report/manifest JSON
- write diversity summary into report/manifest JSON and markdown

If the current batch file is generated from a static fixture, update generation logic and tests around it.

### 4. Add CLI options if appropriate

If there is a CLI that builds the batch/template, add options:

```text
--target-count 100
--min-gap-bars 24
--max-samples-per-day 8
--disable-time-diversity
--seed 0
```

Keep defaults backward compatible where possible, except that review batch order should now be more diverse.

### 5. Update GUI/readiness metadata

The GUI itself does not need to solve this during review, but it can show batch diversity status if easily available.

At minimum:
- update review batch/template report
- update readiness report to include:
  - review batch diversity status
  - `min_gap_bars_between_samples`
  - `max_samples_per_day`
  - `unique_days`
  - `cluster_warning_count`

### 6. Do not modify completed review data

Do not delete or rewrite:
- completed CSV
- completed JSONL events

If regenerating batch CSV:
- be careful that existing completed rows may refer to old sample IDs/order.
- Prefer building a new batch artifact version if there is any risk:
  - `EURUSD_15m_pattern_review_batch_002.csv`
  - or update only generation logic and leave existing completed files untouched.

If changing batch order only and sample IDs are stable:
- completed CSV can still reload by `sample_id`.

### 7. Documentation

Update relevant docs:
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- `tasks/prompts/` if committing prompt

Explain:
- review batches are time-diversified
- consecutive samples should avoid the same local region where possible
- constraints are best-effort, not hard data-quality guarantees

## Tests Required

Add tests for pure helpers and integration.

Suggested tests:

1. Dense same-region candidates:
   - many candidates with close timestamps
   - selected samples respect `min_gap_bars` where enough data exists

2. Per-day cap:
   - many candidates on one day and some on another
   - selected result does not exceed `max_samples_per_day` when possible

3. Candidate type balance:
   - multiple candidate types
   - result includes representation from each type when possible

4. Graceful fallback:
   - too few candidates to satisfy gap/cap constraints
   - still returns target count if enough total candidates exist
   - report status is warning, not crash

5. Determinism:
   - same input + same seed gives same output/order

6. Diversity summary:
   - identifies clustered samples
   - computes unique day count and min/median gap

7. Integration:
   - generated review batch first N samples are not all from same local window
   - e.g. first 10 samples should span more than one day or satisfy configured gap threshold where candidates allow it

8. Persistence regression:
   - GUI completed CSV reload by `sample_id` still works after batch order changes
   - no CSV/JSONL schema change

## Validation Commands

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_eurusd_pattern_review_gui.py cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run any new report/batch tests, for example:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_eurusd_pattern_review_template.py cajas/tests/test_validation_eurusd_pattern_review_batch.py
```

Adjust names to actual files.

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile cajas/apps/eurusd_pattern_review_app.py cajas/research/eurusd_pattern_review_gui.py
```

Compile any new/changed report/script/test files.

Regenerate review batch/report artifacts using the existing script(s), for example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_validation_eurusd_pattern_review_template.py
./.venv-qlib313/bin/python cajas/scripts/build_eurusd_research_readiness_report.py
```

Adjust script names to actual repo.

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

Manual GUI smoke:

```bash
./scripts/run_eurusd_review_gui.sh
```

Manual check:
1. Open batch from first sample.
2. Click Next several times.
3. Confirm samples are not all the same local market window.
4. Confirm Previous/Next works.
5. Confirm Save / Save and Next works.
6. Confirm completed values reload by `sample_id`.

## Commit Requirements

Work directly on `main`.

Suggested commit:

```bash
git add cajas tasks
git commit -m "feat: diversify EURUSD review batch samples"
```

Only add files that changed.

Do not push automatically.

## Final Response Required

Report:
- Active branch
- Work done on `main`: yes/no
- Commit hash
- Files changed
- Diversification settings
- First batch diversity result
- Whether first N samples now span multiple regions/days
- Whether sample IDs remain stable
- Whether completed CSV/JSONL compatibility is preserved
- Readiness/report updates
- Validation command results
- Manual GUI smoke result if run
- `git status --short`
- Push status: not pushed
- Manual push command:

```bash
git push origin main
```

## Hard Boundaries

Do not:
- add SQLite
- create branches
- push automatically
- merge automatically
- train models
- produce trading signals/orders
- modify Qlib core
- delete completed review CSV/JSONL data
- invent labels
