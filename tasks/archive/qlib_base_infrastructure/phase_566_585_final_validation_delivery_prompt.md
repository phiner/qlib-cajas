# Phase 566–585 Prompt: Final Validation Baseline + Delivery Readiness Pack

You are working on branch:

- `phase-next-mega-logic`

## Current state

The user has manually committed all pending changes.

Important:

- Working tree is clean.
- Previous commit-blocking issue is resolved manually.
- Do not assume there are staged/unstaged changes.
- Start by verifying current branch and clean status.

Latest known achieved state from previous phases:

```text
fast pytest subset: about 80s
run_fast_validation.py --tier fast: about 83–84s
run_smoke_validation.py --tier micro: about 10–11s
reads_full_csv_likely_count: 2
high-risk data-source candidates: 0
```

Major completed work includes:

- Research stack hardening.
- Stable reproducibility closure.
- Manual governance / research-only approval workflow.
- Validation runtime split.
- Fast/micro/closure/full validation tiers.
- Data I/O audit and large CSV readiness.
- CSV loading policy and chunked reader utilities.
- Full-read CSV risk reduction.
- Fast validation subprocess hotspot optimization.

## Phase objective

Implement **Final Validation Baseline + Delivery Readiness Pack**.

This is a stabilization and delivery phase, not a feature expansion phase.

Primary goals:

1. Confirm branch state and current validation baseline.
2. Build a final validation delivery packet if not already present or update it if stale.
3. Create a concise final docs index for the research/validation/data I/O workflow.
4. Create a handoff checklist for future work.
5. Run bounded final validations.
6. Preserve fast validation under 90s if possible.
7. Preserve micro smoke around 10–15s if possible.
8. Preserve data-source audit result with no high-risk regressions.
9. Produce a clean commit with final delivery artifacts.

## Non-negotiable boundaries

Do not:

- Modify Qlib core.
- Add broker adapters.
- Add live trading.
- Add paper trading execution.
- Add order generation.
- Add order routing.
- Add position sizing.
- Add portfolio optimization.
- Add PnL optimization.
- Add execution simulation.
- Add network calls.
- Add GPU/CUDA requirements.
- Add files named `init.py`; continue using `__init__.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no network
- no broker/live/paper execution

---

# Part A — Verify clean baseline

Run:

```bash
git branch --show-current
git status --short
git log --oneline -8
```

Expected:

- branch is `phase-next-mega-logic`
- status is clean before new work

If the working tree is not clean, stop and report exact files before proceeding.

---

# Part B — Final validation delivery packet

If these files already exist from a previous phase, update them. If they do not exist, create them:

- `cajas/reports/validation_delivery_packet.py`
- `cajas/scripts/build_validation_delivery_packet.py`

The delivery packet should summarize:

- branch
- git commit
- fast validation runtime
- fast pytest runtime
- micro smoke runtime
- data-source audit summary
- validation runtime audit summary
- validation tier commands
- data I/O guardrail status
- known remaining risks
- recommended next actions
- explicit no-execution boundaries

Outputs:

- `validation_delivery_packet.json`
- `validation_delivery_packet.md`

Suggested command:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_validation_delivery_packet.py \
  --fast-timing tmp/validation-runtime-audit/fast_validation_phase566.json \
  --data-source-audit tmp/data-io-audit/data_source_audit_phase566.json \
  --runtime-audit tmp/validation-runtime-audit/validation_runtime_phase566.json \
  --out-json tmp/validation-delivery/validation_delivery_packet.json \
  --out-md tmp/validation-delivery/validation_delivery_packet.md \
  --allow-missing-inputs
```

The script should tolerate missing optional inputs and record warnings.

---

# Part C — Final documentation index

Create:

- `cajas/docs/final_research_stack_index.md`

This should be a concise index, not a huge duplicated document.

Include links/sections for:

## Research stack status

- research gate
- final readiness
- research-only approval
- no broker/live/paper execution boundary

## Validation workflow

- fast validation
- quick validation
- micro smoke
- minimal smoke
- closure/full smoke
- when to run each

## Data I/O workflow

- data source audit
- I/O runtime audit
- large CSV metadata inspection
- dataset file manifest
- chunked CSV reader
- cache/index/columnar fallback
- rules for real data access

## Current recommended commands

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_latest.json --out-md tmp/data-io-audit/data_source_audit_latest.md
```

## Remaining known risks

- fast validation timing variance
- remaining low-risk / false-positive full-read candidates
- integration/slow tests are explicit
- full/closure smoke is intentionally expensive

---

# Part D — Future work checklist

Create:

- `cajas/docs/future_work_checklist.md`

Keep it practical.

Sections:

## Immediate next work

- keep fast validation stable under 90s
- convert remaining CLI artifact tests if runtime regresses
- monitor data-source audit count
- keep real-data access explicit

## Data I/O future work

- optional parquet/arrow cache when dependency is available
- chunked feature extraction for real multi-GB files
- manifest-based incremental processing
- cache invalidation tests

## Research future work

- offline-only experiment comparison
- manual governance review decisions
- research-only approval refresh
- no trading execution until explicitly designed in a future separate branch

## Hard blockers before paper/live work

- no broker code
- no order generation
- no position sizing
- no PnL optimization
- no execution simulation
- no live data connection

---

# Part E — Update main docs

Update if needed:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/data_io_optimization_notes.md`
- `tasks/phase_566_585_final_validation_delivery_prompt.md`

Add references to:

- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/future_work_checklist.md`
- validation delivery packet command

Do not duplicate all content.

---

# Part F — Final bounded validation

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase566.json --out-md tmp/data-io-audit/data_source_audit_phase566.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase566.json --out-md tmp/validation-runtime-audit/validation_runtime_phase566.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase566.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/build_validation_delivery_packet.py --fast-timing tmp/validation-runtime-audit/fast_validation_phase566.json --data-source-audit tmp/data-io-audit/data_source_audit_phase566.json --runtime-audit tmp/validation-runtime-audit/validation_runtime_phase566.json --out-json tmp/validation-delivery/validation_delivery_packet.json --out-md tmp/validation-delivery/validation_delivery_packet.md --allow-missing-inputs
```

If a command exceeds a few minutes, stop and report exact bottleneck.

---

# Part G — Commit guidance

Suggested commit:

```bash
git add cajas/reports/validation_delivery_packet.py \
        cajas/scripts/build_validation_delivery_packet.py \
        cajas/docs/final_research_stack_index.md \
        cajas/docs/future_work_checklist.md \
        cajas/README.md \
        cajas/docs/qlib_integration_notes.md \
        cajas/docs/test_runtime_optimization_notes.md \
        cajas/docs/data_io_optimization_notes.md \
        tasks/phase_566_585_final_validation_delivery_prompt.md

git commit -m "docs: add final validation delivery readiness pack"
```

If code files already exist and only docs changed, adjust the add list accordingly.

Final push command:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Branch/status
- Files changed
- Validation results
- Runtime summary
- Data-source audit summary
- Validation delivery packet paths
- Remaining risks
- Git commits
- Final status
- Manual push command

Do not push from Codex unless explicitly instructed.

Completion reference:

- expected delivery artifacts:
  - `cajas/reports/validation_delivery_packet.py`
  - `cajas/scripts/build_validation_delivery_packet.py`
  - `cajas/docs/final_research_stack_index.md`
  - `cajas/docs/future_work_checklist.md`
