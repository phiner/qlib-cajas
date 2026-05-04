# Phase 586–605 Prompt: Final Fast Validation Overhead Trim + Commit/Push Readiness

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 566–585 completed delivery artifacts and bounded validation.

Latest status:

- Working tree is dirty only from Phase 566–585 delivery files.
- `git diff --check` is clean.
- Commit was not created in the previous pass.
- User may commit manually, but this phase may create the final delivery commit if allowed.

Files added/updated in Phase 566–585:

- `cajas/reports/validation_delivery_packet.py`
- `cajas/scripts/build_validation_delivery_packet.py`
- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/future_work_checklist.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/data_io_optimization_notes.md`
- `tasks/phase_546_565_commit_recovery_validation_delivery_prompt.md`
- `tasks/phase_566_585_final_validation_delivery_prompt.md`

Latest validation:

```text
PASS compileall
PASS path hygiene
PASS init.py checks
PASS data-source audit
PASS validation runtime audit
PASS fast subset pytest: 306 passed, 15 deselected in 81.58s
PASS run_fast_validation --tier fast: total 93.46s, pytest_fast 90.23s
PASS micro smoke: 11.46s
PASS validation delivery packet build
```

Latest data-source audit:

```text
reads_full_csv_likely_count = 2
no high-risk regression
```

Remaining issue:

- Direct fast subset is under 90s.
- `run_fast_validation.py --tier fast` total is still slightly above 90s because fixed hygiene overhead plus pytest variance.
- CLI/report tests still dominate slow slots.

## Phase objective

Implement **Final Fast Validation Overhead Trim + Commit/Push Readiness**.

This is a small final cleanup phase.

Primary goals:

1. Commit Phase 566–585 delivery files cleanly.
2. Trim `run_fast_validation.py --tier fast` overhead or stabilize it under/near 90s.
3. Do not make broad architecture changes.
4. Preserve fast subset under 90s.
5. Preserve micro smoke around 10–15s.
6. Preserve `reads_full_csv_likely_count <= 2`.
7. Produce final push-ready status.

## Non-negotiable boundaries

Do not:

- Modify Qlib core.
- Add broker/live/paper execution.
- Add order generation/routing.
- Add position sizing.
- Add PnL optimization.
- Add execution simulation.
- Add network calls.
- Add GPU/CUDA requirements.
- Add files named `init.py`.

All validation remains:

- CPU-only
- local
- deterministic where feasible
- no network
- no trading execution

---

# Part A — Commit current delivery artifacts

Start with:

```bash
git branch --show-current
git status --short
git diff --check
```

If the working tree only contains Phase 566–585 delivery files, commit them:

```bash
git add cajas/reports/validation_delivery_packet.py \
        cajas/scripts/build_validation_delivery_packet.py \
        cajas/docs/final_research_stack_index.md \
        cajas/docs/future_work_checklist.md \
        cajas/README.md \
        cajas/docs/qlib_integration_notes.md \
        cajas/docs/test_runtime_optimization_notes.md \
        cajas/docs/data_io_optimization_notes.md \
        tasks/phase_546_565_commit_recovery_validation_delivery_prompt.md \
        tasks/phase_566_585_final_validation_delivery_prompt.md

git commit -m "docs: add final validation delivery readiness pack"
```

If commit is blocked by platform/service error, do not retry repeatedly. Report the exact staged files and provide manual commands.

---

# Part B — Trim fixed fast validation overhead

Inspect:

- `cajas/scripts/run_fast_validation.py`

Current fast timing:

```text
pytest_fast around 90.23s
total around 93.46s
```

Look for low-risk overhead reductions only:

## B1. Avoid duplicated checks

If `run_fast_validation.py --tier fast` performs checks already covered by the pytest subset or other steps in the same run, avoid duplication only when safe.

Potential examples:

- repeated marker/audit checks inside pytest and external command
- repeated data-source audits, if any
- repeated compile path discovery
- redundant output directory scans

Do not remove:

- compileall
- path hygiene
- init.py checks
- pytest fast subset

unless moving them to explicit quick/fast modes is already documented and tested.

## B2. Add `--tier commit-fast` only if useful

If fast must remain comprehensive, optionally add a lower-overhead tier:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier commit-fast
```

Semantics:

- compileall
- path hygiene
- init.py checks
- pytest fast subset
- no extra audits or optional reporting

But do not confuse existing `fast` semantics.

## B3. Improve timing/reporting only if low risk

If total exceeds 90 due to variance, make documentation clear:

- direct fast subset target: under 90s
- `run_fast_validation --tier fast`: expected around 90–95s because it includes hygiene
- `quick`: for tight edit loop
- `micro smoke`: for final handoff

---

# Part C — Convert one or two remaining slow CLI/report tests if obvious

Run one duration report only:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests \
  -m "not smoke and not slow and not closure and not full and not integration" \
  --durations=30 -q
```

If there are obvious 2–4s subprocess-heavy CLI tests that can be safely converted in under a small change:

- convert to in-process `main(argv)` test
- or mark true subprocess test as `integration`
- do not broad-refactor many files

Candidates may include remaining `test_build_*_cli.py` or report CLI tests.

Keep coverage.

---

# Part D — Update delivery docs if needed

Update only if behavior changes:

- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/final_research_stack_index.md`
- `cajas/docs/future_work_checklist.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_586_605_final_fast_overhead_trim_prompt.md`

Document:

- final fast subset runtime
- final `run_fast_validation` runtime
- whether under-90 was reached for total or only direct pytest
- recommended daily command
- remaining runtime variance

---

# Part E — Final validation

Run bounded checks:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase586.json --out-md tmp/data-io-audit/data_source_audit_phase586.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase586.json --out-md tmp/validation-runtime-audit/validation_runtime_phase586.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase586.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/build_validation_delivery_packet.py --fast-timing tmp/validation-runtime-audit/fast_validation_phase586.json --data-source-audit tmp/data-io-audit/data_source_audit_phase586.json --runtime-audit tmp/validation-runtime-audit/validation_runtime_phase586.json --out-json tmp/validation-delivery/validation_delivery_packet.json --out-md tmp/validation-delivery/validation_delivery_packet.md --allow-missing-inputs
```

If a command exceeds a few minutes, stop and report exact bottleneck.

---

# Commit guidance

If additional code/docs changes were made after the first delivery commit, create a second small commit:

```bash
git add <changed files>
git commit -m "test: trim final fast validation overhead"
```

Final report should include:

- branch/status
- commits created
- validation results
- fast subset runtime
- run_fast_validation runtime
- micro smoke runtime
- data-source audit count
- validation delivery packet paths
- remaining risks
- manual push command

Manual push command:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Branch/status
- Files changed
- Validation
- Runtime summary
- Data-source audit
- Validation delivery packet paths
- Git commits
- Remaining risks
- Final status
- Manual push command

Do not push from Codex unless explicitly instructed.
