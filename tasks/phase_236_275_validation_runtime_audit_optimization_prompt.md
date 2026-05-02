# Phase 236–275 Prompt: Comprehensive Validation Runtime Audit + Test/Smoke Architecture Optimization

You are working on branch:

- `phase-next-mega-logic`

## Current problem

Validation runtime has grown too large and unpredictable.

Observed examples:

```bash
rtk ./.venv-qlib313/bin/python -m pytest cajas/tests
```

was still running after 16+ minutes and was stuck around heavy smoke tests such as:

```text
cajas/tests/test_run_full_research_stack_smoke.py
cajas/tests/test_run_research_quality_loop_smoke.py
```

After initial optimization attempts:

```bash
rtk ./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
```

completed but took about:

```text
total_runtime: 162.79s
```

And:

```bash
rtk ./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation-minimal
```

was still running after 11+ minutes, because `minimal` still invoked nested full closure/full-stack workflows.

This phase should do a **comprehensive audit and optimization** of validation runtime, not a superficial one-file fix.

## Big objective

Implement **Comprehensive Validation Runtime Audit + Test/Smoke Architecture Optimization**.

Goals:

1. Measure where validation time is going.
2. Classify tests into unit / integration / smoke / slow / closure / full.
3. Ensure daily validation is fast and predictable.
4. Ensure micro smoke is actually micro.
5. Ensure minimal smoke is bounded and representative, not nested full-stack.
6. Keep closure/full smoke available but explicit.
7. Avoid repeated nested mega-smokes inside pytest.
8. Add runtime budget checks and documentation.
9. Preserve correctness and all research safety boundaries.

## Target runtime intent

Do not promise exact wall-clock numbers, but design toward:

- `run_fast_validation.py`: ideally under 2 minutes on normal local dev hardware.
- `run_smoke_validation.py --tier micro`: ideally under 60 seconds.
- `run_smoke_validation.py --tier minimal`: bounded and clearly shorter than closure/full.
- `--tier closure` and `--tier full`: may be expensive, but must be explicitly requested.

If a target cannot be met, report why and identify the remaining expensive tests.

## Non-negotiable boundaries

Do not:

- Delete coverage just to reduce runtime.
- Hide real failures.
- Weaken safety/governance/reproducibility semantics.
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
- Add GPU/CUDA requirements.
- Add network calls.
- Add files named `init.py`; continue using `__init__.py`.

All validation remains:

- CPU-only.
- Local.
- Deterministic where feasible.
- No network.
- No broker/live/paper execution.

---

# Part A — Runtime audit

## A1. Add validation runtime audit tooling

Create:

- `cajas/reports/validation_runtime_audit.py`
- `cajas/scripts/audit_validation_runtime.py`

The audit should collect and summarize:

- pytest collection count
- tests by marker:
  - unmarked
  - smoke
  - slow
  - integration
  - closure
  - full
- tests matching heavy naming patterns:
  - `test_run_*_smoke.py`
  - tests invoking `run_*_smoke.py`
  - tests invoking subprocess for CLI workflows
- top slow tests using pytest duration output if feasible
- files with likely nested smoke calls
- recommended marker/action per test file

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py \
  --tests-root cajas/tests \
  --out-json tmp/validation-runtime-audit/validation_runtime_audit.json \
  --out-md tmp/validation-runtime-audit/validation_runtime_audit.md
```

Do not require running the full expensive suite to produce the audit. Use static inspection first. Add optional dynamic duration mode:

```bash
--run-durations
--durations 30
```

If dynamic mode is too slow, static mode should still work.

## A2. Add test runtime notes

Create or update:

- `cajas/docs/test_runtime_optimization_notes.md`

Include:

- current observed slow commands
- known heavy smoke test files
- marker policy
- validation tiers
- what developers should run daily
- what to run before merging
- what to run only for release/closure

---

# Part B — Pytest marker architecture

## B1. Configure markers

Add or update `pytest.ini` or equivalent project config.

Define markers:

```ini
markers =
    unit: fast unit-level tests
    integration: medium-cost integration tests
    smoke: end-to-end smoke workflows
    slow: runtime-heavy tests
    closure: latest closure/review smoke flows
    full: historical/full-stack mega smoke flows
```

Avoid pytest unknown marker warnings.

## B2. Mark heavy tests comprehensively

Mark all heavy smoke test files appropriately.

Likely heavy files include, but are not limited to:

- `cajas/tests/test_run_full_research_stack_smoke.py`
- `cajas/tests/test_run_research_quality_loop_smoke.py`
- `cajas/tests/test_run_research_remediation_smoke.py`
- `cajas/tests/test_run_final_reproducibility_closure_smoke.py`
- `cajas/tests/test_run_governance_review_closure_smoke.py`
- `cajas/tests/test_run_final_readiness_smoke.py`
- `cajas/tests/test_run_research_gate_smoke.py`
- `cajas/tests/test_run_qlib_model_bridge_smoke.py`
- `cajas/tests/test_run_qlib_dataset_handler_smoke.py`
- `cajas/tests/test_run_qlib_adapter_smoke.py`
- `cajas/tests/test_run_smoke_validation.py` if it executes real heavy tiers

Use file-level markers such as:

```python
import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.slow]
```

For latest closure flows, add:

```python
pytest.mark.closure
```

For full historical mega flows, add:

```python
pytest.mark.full
```

Do not over-mark pure unit tests.

## B3. Add tests enforcing marker policy

Create:

- `cajas/tests/test_validation_marker_policy.py`

It should statically inspect test files and verify:

- `test_run_*_smoke.py` files are marked smoke/slow, except explicitly allowlisted micro tests.
- full-stack smoke tests are marked full or closure.
- `pytest.ini` defines required markers.
- docs mention the fast command.
- `run_fast_validation.py` excludes smoke/slow.

Keep this test fast.

---

# Part C — Replace nested heavy pytest with unit-style orchestration tests

For tests of smoke runners, avoid invoking real heavy pipelines inside pytest by default.

Refactor tests where feasible to use:

- monkeypatch for subprocess calls
- fake command runner injection
- small fixture artifact directories
- direct builder calls with tiny JSON fixtures
- asserts on command construction, output paths, and status parsing

Suggested pattern:

- Keep real full smoke CLI command as a script-level validation outside default pytest.
- In pytest, test orchestration logic with fake runners.

If current smoke runner functions directly call `subprocess.run`, consider introducing a small helper abstraction:

- `cajas/scripts/command_runner.py`
- or local injectable `run_command` function in each script

Do not over-engineer. Keep simple.

---

# Part D — Fast validation script

Update or create:

- `cajas/scripts/run_fast_validation.py`

It should run only fast checks:

1. compileall
2. path hygiene
3. no `init.py`
4. pytest excluding smoke/slow/closure/full

Command should be:

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full"
```

Add options:

```bash
--skip-compileall
--durations 30
--pytest-extra-args "..."
```

It should:

- print each command
- print elapsed time per command
- print total runtime
- stop on failure
- never run smoke/closure/full tiers

---

# Part E — Smoke validation script with honest tiers

Update or create:

- `cajas/scripts/run_smoke_validation.py`

Support tiers:

```text
micro
minimal
closure
full
```

Default tier must be:

```text
micro
```

## E1. micro tier

Must be truly tiny.

It should not invoke any existing mega smoke runner.

Use static tiny fixtures under:

- `cajas/data_examples/validation_fixtures/`

Micro tier may run direct builder CLIs for tiny artifacts, such as:

- governance review decision builder
- research-only approval packet builder
- CI validation plan builder
- small final readiness summary builder
- runtime audit static mode

Expected output:

- `tmp/smoke-validation-micro/...`

## E2. minimal tier

Must be bounded and representative.

It can run a small curated path using tiny fixtures or a single latest non-nested smoke.

It must not call:

- full historical smoke
- full research stack smoke
- remediation smoke that internally calls full-stack twice
- governance closure smoke if that calls final repro closure, which calls remediation, which calls quality loop, which calls full-stack

If current latest closure smoke is nested and expensive, do not use it as minimal.

## E3. closure tier

Can run:

- latest governance review closure smoke
- final reproducibility closure smoke

Document as expensive.

## E4. full tier

Can run:

- historical full-stack / remediation / quality-loop smokes

Document as very expensive.

---

# Part F — Tiny deterministic validation fixtures

Create tiny static fixtures under:

- `cajas/data_examples/validation_fixtures/`

Suggested files:

- `stable_reproducibility_report_pass.json`
- `governance_remediation_needs_manual_review.json`
- `final_readiness_needs_manual_governance_review.json`
- `governance_review_decision_approve_offline_only.json`
- `offline_review_packet_tiny.json`
- `final_research_bundle_tiny.json`

Keep them minimal but schema-compatible with builders.

Add README notes in:

- `cajas/data_examples/README.md`

---

# Part G — CI validation plan update

Update:

- `cajas/reports/ci_validation_plan.py`
- `cajas/scripts/build_ci_validation_plan.py`

The plan should include tiers:

## Tier 0 — Hygiene

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
```

## Tier 1 — Fast local validation

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
```

## Tier 2 — Fast pytest only

```bash
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full"
```

## Tier 3 — Micro smoke

```bash
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

## Tier 4 — Minimal smoke

```bash
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation-minimal
```

## Tier 5 — Closure smoke

```bash
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier closure --out-root tmp/smoke-validation-closure
```

## Tier 6 — Full smoke

```bash
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier full --out-root tmp/smoke-validation-full
```

---

# Part H — Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/data_examples/README.md`
- `tasks/phase_236_275_validation_runtime_audit_optimization_prompt.md`

Document:

- why `pytest cajas/tests` can be expensive
- recommended daily command
- marker policy
- smoke tier definitions
- when to run closure/full
- how to run runtime audit
- what to do if a test becomes slow
- no broker/live/paper execution boundaries remain unchanged

Recommended daily command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
```

Micro smoke:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

---

# Part I — Tests

Add or update focused fast tests.

Required tests:

## Runtime audit

- static audit detects `test_run_*_smoke.py`
- static audit classifies marker coverage
- audit writes JSON and Markdown
- audit does not require running full pytest

## Marker policy

- required pytest markers are configured
- heavy smoke test files have smoke/slow markers
- closure/full files have appropriate marker when applicable
- fast validation excludes smoke/slow/closure/full

## Fast validation

- command plan excludes heavy markers
- supports `--durations`
- prints elapsed time structure
- does not invoke smoke validation

## Smoke validation

- default tier is micro
- micro tier does not invoke closure/full runners
- minimal tier does not invoke historical full-stack mega-smokes
- closure/full tiers are explicit
- output paths are created for micro tier

## Fixtures

- tiny validation fixtures are valid JSON
- fixture builders can consume tiny fixtures

## CI plan/docs

- CI plan includes fast/micro/minimal/closure/full tiers
- docs mention recommended daily command
- docs warn that full smoke is expensive

Keep tests deterministic and lightweight. Do not run heavy smoke inside these tests.

---

# Validation commands

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full"
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_audit.json --out-md tmp/validation-runtime-audit/validation_runtime_audit.md
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

Optional if time allows:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation-minimal
```

Do not require closure/full smoke in this phase.

---

# Commit guidance

After validation passes, create local commits. Suggested split:

1. `test: add validation runtime audit and marker policy`
2. `test: split fast validation from smoke tiers`
3. `feat: add micro smoke fixtures and validation tier runners`
4. `docs: document validation runtime optimization`

Report:

- changed files
- validation results
- runtime audit summary
- fast validation runtime
- micro smoke runtime
- minimal smoke runtime if run
- smoke output paths
- commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin phase-next-mega-logic
```

---

# Final response expected from Codex

Return a compact summary with:

- Summary
- Files changed
- Validation
- Runtime audit summary
- Runtime notes
- Smoke output paths
- Git commits
- Notes / risks
- Final status

Do not push from Codex unless explicitly instructed.

---

## Implementation Notes (local)

- Added static runtime audit tooling (`cajas/reports/validation_runtime_audit.py`, `cajas/scripts/audit_validation_runtime.py`).
- Expanded pytest marker policy (`unit`, `integration`, `smoke`, `slow`, `closure`, `full`).
- Classified heavy smoke tests with `closure`/`full` where applicable.
- Refactored validation runners to separate fast validation from `micro|minimal|closure|full` smoke tiers.
- Added tiny deterministic fixtures under `cajas/data_examples/validation_fixtures/`.
- Updated CI validation plan to explicit Tier 0-6 structure.
- Added fast policy/runtime tests without invoking heavy nested smoke inside default pytest.
