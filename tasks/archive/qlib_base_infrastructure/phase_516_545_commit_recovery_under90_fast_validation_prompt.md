# Phase 516–545 Prompt: Commit Recovery + Consistent Under-90s Fast Validation Hardening

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 486–515 completed implementation and validation, but local commit creation was blocked by approval-service error:

```text
503 Service Unavailable
```

Do not push from Codex.

Latest Phase 486–515 results:

- Recovered and validated the Phase 456–485 staged fast-validation group.
- Optimized `test_validate_qlib_handler_input_cli` by removing real subprocess usage.
- Fast-tier pytest is now near the 90s boundary:
  - `85.83s`
  - `89.67s`
  - `89.81s`
- `run_fast_validation.py --tier fast` remains slightly above 90s because of fixed hygiene overhead:
  - pytest step around `91.00s`
  - total around `94.06s`
- Micro smoke remains fast:
  - around `11.21s`
- Data-source audit remains stable:
  - `reads_full_csv_likely_count = 2`
  - no new high-risk regression

Current git state from previous phase:

- Commits were not created.
- Working tree has intended split:
  - staged fast-validation runner/test/audit group
  - unstaged baseline/docs/handler-cli optimization group
  - untracked phase prompts
- `git diff --check` was clean.

Known remaining runtime risks:

- Fast tier is close to the 90s threshold and may exceed it with normal variance.
- Remaining hotspots are many CLI artifact/report tests around `2.1–2.5s` each.
- Further improvement likely requires converting several more `test_build_*_cli.py` / report CLI tests to in-process entrypoint tests or marking true subprocess tests as `integration`.

## Phase objective

Implement **Commit Recovery + Consistent Under-90s Fast Validation Hardening**.

Primary goals:

1. Recover and commit the pending Phase 456–515 changes in clean groups.
2. Preserve the validated staged/unstaged split.
3. Convert 2–4 additional CLI/report fast-tier hotspots away from real subprocess execution.
4. Keep data-source audit stable at `reads_full_csv_likely_count <= 2`.
5. Make fast pytest consistently below 90s.
6. Make `run_fast_validation.py --tier fast` closer to or below 90s including overhead.
7. Keep micro smoke around ~10–15s.
8. Preserve all research-only/no-execution boundaries.

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

# Part A — Commit recovery first

Start with:

```bash
git status --short
git diff --cached --name-only
git diff --name-only
git diff --check
```

Do not revert valid Phase 456–515 work.

## A1. Commit fast validation runner/test/audit group

Likely staged files:

- `cajas/scripts/run_fast_validation.py`
- `cajas/reports/validation_runtime_audit.py`
- `cajas/tests/test_validation_runners.py`
- `cajas/tests/test_validation_runtime_audit.py`
- `cajas/tests/test_validation_marker_policy.py`

Run targeted validation:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_validation_runners.py cajas/tests/test_validation_runtime_audit.py cajas/tests/test_validation_marker_policy.py -q
```

Commit:

```bash
git add cajas/scripts/run_fast_validation.py \
        cajas/reports/validation_runtime_audit.py \
        cajas/tests/test_validation_runners.py \
        cajas/tests/test_validation_runtime_audit.py \
        cajas/tests/test_validation_marker_policy.py

git commit -m "test: refactor fast validation runner tests to injected execution"
```

If commit is blocked again by approval-service 503, stop commit attempts and continue coding only if safe; report exact staged files.

## A2. Commit baseline + handler CLI test optimization group

Likely files:

- `cajas/scripts/run_baseline_disabled.py`
- `cajas/tests/test_baseline_runner.py`
- `cajas/tests/test_validate_qlib_handler_input_cli.py`

Run:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests/test_baseline_runner.py cajas/tests/test_validate_qlib_handler_input_cli.py -q
```

Commit:

```bash
git add cajas/scripts/run_baseline_disabled.py \
        cajas/tests/test_baseline_runner.py \
        cajas/tests/test_validate_qlib_handler_input_cli.py

git commit -m "test: optimize baseline and handler cli fast tests"
```

## A3. Commit docs and phase prompts

Likely files:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `tasks/phase_456_485_fast_validation_subprocess_hotspot_prompt.md`
- `tasks/phase_486_515_fast_validation_under90_prompt.md`

Commit:

```bash
git add cajas/README.md \
        cajas/docs/qlib_integration_notes.md \
        cajas/docs/test_runtime_optimization_notes.md \
        tasks/phase_456_485_fast_validation_subprocess_hotspot_prompt.md \
        tasks/phase_486_515_fast_validation_under90_prompt.md

git commit -m "docs: document fast validation under-90 push"
```

End recovery with:

```bash
git status --short
```

If unrelated files remain, leave them untouched and report them.

---

# Part B — Identify remaining fast-tier CLI/report hotspots

Run one duration report:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests \
  -m "not smoke and not slow and not closure and not full and not integration" \
  --durations=50 -q
```

Capture top slow tests in:

- `cajas/docs/test_runtime_optimization_notes.md`

Look especially for:

- `test_build_*_cli.py`
- `test_*_cli.py`
- report builder CLI tests
- artifact writer tests
- validation runner tests
- tests that spawn subprocess
- tests that build temp artifact trees

Do not run the whole fast subset repeatedly while coding. Use targeted files after the initial duration report.

---

# Part C — Convert 2–4 remaining CLI/report hotspots

For each chosen hotspot, use the safest approach.

## C1. Prefer in-process entrypoint tests

Where CLI scripts already have `main(argv)` or can expose one with minimal change:

- call `main([...])` directly
- use tiny fixtures
- assert output file exists and schema is valid
- avoid `subprocess.run`
- avoid invoking Python interpreter as child process

## C2. Split CLI behavior

For tests that need to verify CLI wiring:

- fast test: direct `main(argv)` or builder function
- integration test: real subprocess invocation, marked `integration`

## C3. Use monkeypatch for expensive dependencies

For script runners that orchestrate other scripts:

- monkeypatch command runner
- verify command plan and output paths
- do not run nested commands in fast tier

## C4. Mark true end-to-end CLI tests as integration

If a test is valuable but inherently subprocess-heavy:

```python
import pytest

pytestmark = [pytest.mark.integration]
```

or function-level marker.

Make sure marker policy tests understand this.

Do not remove coverage.

---

# Part D — Candidate hotspot areas

Likely candidate tests may include, but are not limited to:

- `test_build_qlib_*_cli.py`
- `test_build_*_packet_cli.py`
- `test_build_*_report_cli.py`
- `test_register_*_cli.py`
- `test_compare_*_cli.py`
- `test_validate_*_cli.py`
- `test_*_runner.py`
- `test_*_validation*.py`

Use actual duration report as the source of truth.

---

# Part E — Keep audits stable

Run after changes:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py \
  --project-root cajas \
  --data-root /home/phiner/projects/research/data \
  --out-json tmp/data-io-audit/data_source_audit_phase516_after.json \
  --out-md tmp/data-io-audit/data_source_audit_phase516_after.md
```

Expected:

- `reads_full_csv_likely_count <= 2`
- no high-risk candidates
- no real-data read regression

Run runtime audit:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py \
  --tests-root cajas/tests \
  --out-json tmp/validation-runtime-audit/validation_runtime_phase516.json \
  --out-md tmp/validation-runtime-audit/validation_runtime_phase516.md
```

Expected:

- fewer unmarked subprocess-heavy fast-tier tests
- clear recommendations for remaining slow tests

---

# Part F — Add regression guards

Update if needed:

- `cajas/reports/validation_runtime_audit.py`
- `cajas/tests/test_validation_runtime_audit.py`
- `cajas/tests/test_validation_marker_policy.py`

Guards should catch:

- unmarked fast-tier tests using `subprocess.run`
- unmarked tests invoking `python cajas/scripts/...`
- unmarked tests invoking validation/smoke runners
- unmarked tests building large temp artifact trees

Do not make the policy so strict that tiny direct `main(argv)` tests are blocked.

---

# Part G — Validation commands

Use targeted tests first for changed hotspot files.

Then run final bounded validation:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase516_after.json --out-md tmp/data-io-audit/data_source_audit_phase516_after.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase516.json --out-md tmp/validation-runtime-audit/validation_runtime_phase516.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase516.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

If a command exceeds a few minutes, stop and report exact bottleneck.

---

# Part H — Documentation

Update:

- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/docs/data_io_optimization_notes.md` only if data-source audit changes
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_516_545_commit_recovery_under90_fast_validation_prompt.md`

Document:

- commit recovery outcome
- fast runtime before/after
- tests converted to in-process
- tests marked integration
- remaining top slow tests
- data-source audit stability
- recommended commands

Recommended commands:

```bash
# Daily
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast

# Tight loop
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick

# Explicit integration tests
./.venv-qlib313/bin/python -m pytest cajas/tests -m "integration and not slow and not smoke"

# Micro smoke
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

---

# Commit guidance

Suggested commits:

```bash
git commit -m "chore: recover pending fast validation commits"
git commit -m "test: convert remaining cli hotspots to fast in-process tests"
git commit -m "docs: document consistent under-90 fast validation push"
```

Final report should include:

- commit recovery result
- files changed
- validation results
- fast pytest runtime before/after
- run_fast_validation runtime before/after
- data-source audit result
- remaining top slow tests
- commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return compact summary:

- Summary
- Commit recovery result
- Files changed
- Validation
- Runtime before/after
- Data-source audit
- Remaining risks
- Git commits
- Final status

Do not push from Codex unless explicitly instructed.
