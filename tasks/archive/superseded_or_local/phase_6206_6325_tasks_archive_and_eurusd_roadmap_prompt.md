# Phase 6206–6325 — Task Prompt Archive Cleanup and EURUSD Research End-to-End Roadmap

## Context

You are working in the Qlib Base / qlib-cajas repository.

Current branch context:

- Most active work has been on `phase-eurusd-pattern-research-kickoff`.
- The project has moved from infrastructure hardening into the original objective:
  - EURUSD 15m Bid pattern research
  - clean dataset view
  - candidate generation
  - human review workflow
  - local GUI review app

Current important project decisions:

- Research timeframe is fixed to EURUSD `15m`.
- Price side is `Bid`.
- Do not aggregate to 1H/4H unless explicitly requested later.
- Do not introduce live trading, paper trading, broker routing, order generation, production model training, or Qlib core modifications.
- CSV/JSONL remain durable storage/interchange formats.
- GUI is the human review interface.
- User will manually install GUI optional dependencies:
  - `streamlit`
  - `plotly`
- GitHub merge policy remains manual: do not perform automated merge operations.

Problem to solve now:

- `tasks/` contains too many historical `phase_*.md` prompt files.
- Many are temporary execution prompts from earlier phases.
- Keeping all of them in the active tree makes navigation noisy and can cause accidental untracked/tracked confusion.
- The user wants obsolete prompt docs removed or archived.
- The user also wants one comprehensive Markdown archive explaining the whole project path from zero to the current EURUSD review GUI goal.

## Goal

Clean up the phase prompt archive and create a single end-to-end roadmap document that preserves the important history and current operating model.

This phase should:

1. Audit `tasks/phase_*.md` files.
2. Move or remove obsolete prompt files safely.
3. Preserve the latest/important prompt history in a compact archive.
4. Add one comprehensive end-to-end roadmap Markdown document.
5. Avoid touching source behavior except docs/tasks organization.
6. Keep the repo easy to navigate.

## Required Work

### 1. Audit tasks prompt files

Inspect:

```bash
find tasks -maxdepth 1 -type f -name "phase_*.md" | sort
```

Classify files into groups:

1. Historical infrastructure prompts:
   - Qlib Base validation hardening
   - maintenance readiness
   - alias migration
   - runtime/release readiness
   - post-merge validation

2. EURUSD research prompts:
   - dataset audit
   - anomaly triage
   - clean view
   - pattern candidates
   - review schema/template
   - review feedback
   - review batch
   - GUI review app

3. Current/next active prompts:
   - latest GUI-related phase
   - latest cleanup/archive phase

4. Obsolete duplicate/local-only prompts:
   - superseded prompt variants
   - temporary generated prompts that are not referenced by docs
   - old prompts no longer needed as standalone files

Do not delete anything blindly.

### 2. Create task archive structure

Create a small archive structure under `tasks/`, for example:

```text
tasks/archive/
tasks/archive/qlib_base_infrastructure/
tasks/archive/eurusd_research/
```

Move older phase prompts into archive directories instead of deleting them, unless the file is clearly duplicate/untracked temporary content.

Recommended policy:

- Keep active root `tasks/` small.
- Root `tasks/` should contain only:
  - current phase prompt
  - maybe one immediate next phase prompt
  - one master roadmap/archive document
- Historical prompt files should live under `tasks/archive/...`.
- If a prompt has already been superseded but still useful as history, move it to archive, do not delete.
- If a file is duplicate of a newer prompt variant, remove only after verifying identical or clearly obsolete.

Important:

- Be careful with tracked vs untracked files.
- Use `git status --short` before and after moves.
- Prefer `git mv` for tracked files.
- For untracked old prompt files, either move and add intentionally, or delete only if clearly unnecessary.
- Do not accidentally remove needed current prompts.

### 3. Create master roadmap/archive document

Create:

`tasks/eurusd_15m_research_end_to_end_roadmap.md`

This should be a readable, comprehensive Markdown document for the human user.

It should explain the project from zero to current target.

Required sections:

#### A. Project purpose

Explain:

- The project started as Qlib Base / qlib-cajas infrastructure.
- The real goal is EURUSD 15m Bid pattern research.
- The infrastructure exists to make research reproducible, auditable, and safe.
- It is not a live trading system.

#### B. Scope boundaries

Must state:

- offline research only
- no Qlib core edits
- no live trading
- no paper trading
- no broker routing
- no order generation
- no timeframe aggregation by default
- EURUSD 15m Bid is the fixed research base
- GUI review app is for annotation/research only

#### C. Main phases completed

Summarize, compactly:

1. Qlib Base infrastructure hardening
   - dataset quality
   - contracts
   - drift
   - runtime budget
   - release readiness
   - reviewer packets
   - maintenance continuation

2. Post-merge validation and maintenance baseline
   - mainline validated
   - release readiness ready
   - fork relationship kept
   - no upstream sync planned

3. EURUSD dataset entry
   - raw data files
   - 15m Bid fixed
   - contract ready
   - raw audit blocked due 10 OHLC anomalies

4. Clean dataset view
   - raw files immutable
   - 10 rows quarantined
   - clean view created
   - readiness became ready with clean view

5. Feature scaffold
   - candle geometry
   - wick/body/range
   - multi-horizon 3/5/8/13/21/34/55 features
   - no signals/orders

6. Pattern candidate pack
   - candidate types
   - 206492 candidates
   - balanced 500 review samples
   - candidate tags are review-only

7. Review schema/template
   - schema version `eurusd_15m_pattern_review_v1`
   - 500-row review template
   - QA ready

8. Feedback intake/summary
   - awaiting human input
   - no labels invented
   - non-blocking until human completes review

9. First review batch
   - 100-row batch
   - 10 samples per candidate type
   - guide ready
   - completion awaiting completed batch

10. Local GUI direction
   - CSV is storage
   - GUI is human interface
   - Streamlit/Plotly local app
   - completed CSV output path

#### D. Current artifact map

Include important paths:

Data:

```text
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2020.01.01_2024.12.31.csv
/home/phiner/projects/research/data/EURUSD_15 Mins_Bid_2025.01.01_2025.12.31.csv
tmp/eurusd/EURUSD_15m_Bid_clean_view.csv
tmp/eurusd/EURUSD_15m_Bid_quarantined_rows.csv
```

Candidates/review:

```text
tmp/eurusd/EURUSD_15m_pattern_candidates.csv
tmp/eurusd/EURUSD_15m_pattern_review_samples.csv
tmp/eurusd/EURUSD_15m_pattern_review_template.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
```

GUI:

```text
cajas/apps/eurusd_pattern_review_app.py
tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv
```

Reports:

```text
tmp/validation-eurusd-dataset-contract.md
tmp/validation-eurusd-dataset-audit.md
tmp/validation-eurusd-clean-dataset-view.md
tmp/validation-eurusd-pattern-candidate-pack.md
tmp/validation-eurusd-pattern-review-qa.md
tmp/validation-eurusd-pattern-label-schema.md
tmp/validation-eurusd-pattern-review-template.md
tmp/validation-eurusd-pattern-review-feedback.md
tmp/validation-eurusd-pattern-review-summary.md
tmp/validation-eurusd-pattern-review-batch-001.md
tmp/validation-eurusd-pattern-review-guide.md
tmp/validation-eurusd-research-readiness.md
```

#### E. How to start using the system

Include practical commands:

Install GUI dependencies:

```bash
./.venv-qlib313/bin/python -m pip install streamlit plotly
```

Run GUI:

```bash
./.venv-qlib313/bin/python -m streamlit run cajas/apps/eurusd_pattern_review_app.py
```

Review workflow:

1. Open local GUI.
2. Load clean view and batch.
3. Inspect chart around each sample timestamp.
4. Fill label fields.
5. Save.
6. Completed rows go to:
   - `tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv`
7. Run completed-batch intake/merge.
8. Review summary.
9. Decide whether to refine candidate rules, expand review, or begin outcome analysis.

#### F. Label schema summary

Explain fields:

- `human_pattern_label`
- `market_context`
- `direction_context`
- `structure_quality`
- `follow_through_quality`
- `review_confidence`
- `review_notes`
- `review_status`

Allowed values should match current schema.

#### G. Next research path

Describe the next steps after GUI is usable:

1. Complete first 100-sample review batch.
2. Merge completed batch.
3. Generate feedback summary.
4. Identify:
   - highest quality pattern types
   - highest false-positive pattern types
   - unclear types
5. Refine candidate rules.
6. Generate second batch if needed.
7. Only after enough reviewed examples:
   - outcome analysis
   - simple offline strategy hypotheses
   - ML-assisted labeling later
8. Still no live execution.

#### H. Git workflow

State:

- start from latest main for new branches
- push branch
- user merges manually on GitHub
- no automated merge

### 4. Update README/docs links

Update:

- `cajas/README.md`
- `cajas/docs/eurusd_pattern_research_kickoff.md`
- `cajas/docs/current_qlib_base_stage_archive.md`

Add links/references to:

- `tasks/eurusd_15m_research_end_to_end_roadmap.md`
- task archive structure

### 5. Add archive manifest

Create:

`tasks/archive/README.md`

It should explain:

- why prompts were archived
- where infrastructure prompts live
- where EURUSD research prompts live
- root tasks should stay small
- master roadmap is the human-facing archive

### 6. Validation

Run docs/hygiene checks:

```bash
git status --short
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Run fast validation if code files are not changed? Since this phase is docs/tasks only, fast validation is optional but recommended:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

If fast validation is skipped because only docs/tasks moved, state that explicitly.

## Branch / Commit Guidance

Continue on current branch if this is still before merging EURUSD research branch:

```bash
git checkout phase-eurusd-pattern-research-kickoff
git status --short --branch
```

Suggested commits:

```bash
git add tasks cajas/README.md cajas/docs/eurusd_pattern_research_kickoff.md cajas/docs/current_qlib_base_stage_archive.md

git commit -m "docs: archive phase prompts and add EURUSD roadmap"
```

If many prompt moves are included, one commit is acceptable.

Do not perform automated merge operations.

If ready, push branch and tell the human user to merge manually on GitHub:

```bash
git push origin phase-eurusd-pattern-research-kickoff
```

## Final Response Required

When finished, report:

- active branch
- files moved/archived
- files deleted, if any, and why
- new master roadmap path
- archive manifest path
- docs updated
- validation/hygiene results
- fast validation runtime if run
- push status
- manual GitHub merge instruction
- confirmation that no source behavior was changed except docs/tasks organization
- confirmation that no automated merge was performed
