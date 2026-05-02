# Phase 546–565 Prompt: Commit Recovery Finalization + Validation Delivery Pack

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 516–545 completed implementation and validation, but local commits were still blocked by approval-service:

```text
503 Service Unavailable
```

Latest achieved runtime:

```text
fast subset pytest:
  306 passed, 15 deselected, 80.06s

run_fast_validation.py --tier fast:
  total: 83.77s
  pytest_fast: 80.88s

run_smoke_validation.py --tier micro:
  10.33s

data-source audit:
  reads_full_csv_likely_count = 2
  no new high-risk regression
```

Phase 516–545 changed:

- `cajas/tests/test_build_offline_review_packet_cli.py`
- `cajas/tests/test_build_qlib_adapter_contract_cli.py`
- `cajas/tests/test_build_ci_validation_plan_cli.py`
- `cajas/docs/test_runtime_optimization_notes.md`

Pending earlier Phase 456–515 changes are still staged/unstaged as expected.

Manual commit plan from previous phase:

```bash
git commit -m "test: refactor fast validation runner tests to injected execution"

git add cajas/scripts/run_baseline_disabled.py \
        cajas/tests/test_baseline_runner.py \
        cajas/tests/test_validate_qlib_handler_input_cli.py \
        cajas/tests/test_build_offline_review_packet_cli.py \
        cajas/tests/test_build_qlib_adapter_contract_cli.py \
        cajas/tests/test_build_ci_validation_plan_cli.py

git commit -m "test: convert remaining cli hotspots to fast in-process tests"

git add cajas/README.md \
        cajas/docs/qlib_integration_notes.md \
        cajas/docs/test_runtime_optimization_notes.md \
        tasks/phase_456_485_fast_validation_subprocess_hotspot_prompt.md \
        tasks/phase_486_515_fast_validation_under90_prompt.md \
        tasks/phase_516_545_commit_recovery_under90_fast_validation_prompt.md

git commit -m "docs: document consistent under-90 fast validation push"

git push origin phase-next-mega-logic
```

## Phase objective

Implement **Commit Recovery Finalization + Validation Delivery Pack**.

Primary goals:

1. Recover and create the pending commits if the approval service is available.
2. If commit is still blocked by `503`, do not keep retrying; generate a local handoff script with exact commands.
3. Run one final bounded validation pass.
4. Build a validation delivery packet summarizing current fast/micro/full tier status.
5. Preserve the under-90s fast validation result.
6. Preserve data-source audit stability.
7. Prepare the branch for user-side push or PR.

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

# Part A — Commit recovery

Start with:

```bash
git status --short
git diff --cached --name-only
git diff --name-only
git diff --check
```

If the staged A1 group is present, run:

```bash
./.venv-qlib313/bin/python -m pytest \
  cajas/tests/test_validation_runners.py \
  cajas/tests/test_validation_runtime_audit.py \
  cajas/tests/test_validation_marker_policy.py \
  -q
```

Then attempt the first commit once:

```bash
git commit -m "test: refactor fast validation runner tests to injected execution"
```

If it fails with approval-service `503`, stop commit attempts and move to Part B.

If it succeeds, continue with the next commit groups:

```bash
git add cajas/scripts/run_baseline_disabled.py \
        cajas/tests/test_baseline_runner.py \
        cajas/tests/test_validate_qlib_handler_input_cli.py \
        cajas/tests/test_build_offline_review_packet_cli.py \
        cajas/tests/test_build_qlib_adapter_contract_cli.py \
        cajas/tests/test_build_ci_validation_plan_cli.py

git commit -m "test: convert remaining cli hotspots to fast in-process tests"
```

Then docs:

```bash
git add cajas/README.md \
        cajas/docs/qlib_integration_notes.md \
        cajas/docs/test_runtime_optimization_notes.md \
        tasks/phase_456_485_fast_validation_subprocess_hotspot_prompt.md \
        tasks/phase_486_515_fast_validation_under90_prompt.md \
        tasks/phase_516_545_commit_recovery_under90_fast_validation_prompt.md

git commit -m "docs: document consistent under-90 fast validation push"
```

End with:

```bash
git status --short
```

---

# Part B — Commit handoff script if commit remains blocked

If commit is still blocked, create:

- `scripts/dev/commit_phase_456_545_recovery.sh`

The script should:

- be executable
- print current branch/status
- run `git diff --check`
- show staged files
- create the three intended commits using the exact groups above
- print final status
- print push command

Do not run the script automatically if commit service is blocked. Just create it for the user.

Also create:

- `cajas/docs/phase_456_545_commit_recovery_handoff.md`

Include:

- why commit was not completed
- exact commit groups
- validation already completed
- manual push command

---

# Part C — Validation delivery packet

Create:

- `cajas/reports/validation_delivery_packet.py`
- `cajas/scripts/build_validation_delivery_packet.py`

The packet should summarize:

- branch
- fast validation runtime
- fast pytest runtime
- micro smoke runtime
- data-source audit summary
- validation tier commands
- current blocked/pending commit state
- known remaining risks
- recommended user actions
- no-execution boundaries

Output:

- `validation_delivery_packet.json`
- `validation_delivery_packet.md`

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_validation_delivery_packet.py \
  --fast-timing tmp/validation-runtime-audit/fast_validation_phase516.json \
  --data-source-audit tmp/data-io-audit/data_source_audit_phase516_after.json \
  --runtime-audit tmp/validation-runtime-audit/validation_runtime_phase516.json \
  --out-json tmp/validation-delivery/validation_delivery_packet.json \
  --out-md tmp/validation-delivery/validation_delivery_packet.md
```

If some input files are missing, support `--allow-missing-inputs` and include warnings instead of failing.

---

# Part D — Final bounded validation

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/audit_data_sources.py --project-root cajas --data-root /home/phiner/projects/research/data --out-json tmp/data-io-audit/data_source_audit_phase546_after.json --out-md tmp/data-io-audit/data_source_audit_phase546_after.md
./.venv-qlib313/bin/python cajas/scripts/audit_validation_runtime.py --tests-root cajas/tests --out-json tmp/validation-runtime-audit/validation_runtime_phase546.json --out-md tmp/validation-runtime-audit/validation_runtime_phase546.md
./.venv-qlib313/bin/python -m pytest cajas/tests -m "not smoke and not slow and not closure and not full and not integration" --durations=30 -q
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/validation-runtime-audit/fast_validation_phase546.json
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
./.venv-qlib313/bin/python cajas/scripts/build_validation_delivery_packet.py --fast-timing tmp/validation-runtime-audit/fast_validation_phase546.json --data-source-audit tmp/data-io-audit/data_source_audit_phase546_after.json --runtime-audit tmp/validation-runtime-audit/validation_runtime_phase546.json --out-json tmp/validation-delivery/validation_delivery_packet.json --out-md tmp/validation-delivery/validation_delivery_packet.md
```

If a command exceeds a few minutes, stop and report the bottleneck.

---

# Part E — Documentation

Update:

- `cajas/docs/test_runtime_optimization_notes.md`
- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_546_565_commit_recovery_validation_delivery_prompt.md`

Document:

- final fast runtime result
- micro smoke result
- data-source audit result
- commit recovery state
- handoff script path if created
- validation delivery packet path
- remaining risks

Recommended commands:

```bash
# Daily
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast

# Tight loop
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier quick

# Micro smoke
./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro
```

---

# Commit guidance

If commit service works, suggested commits:

```bash
git commit -m "test: refactor fast validation runner tests to injected execution"
git commit -m "test: convert remaining cli hotspots to fast in-process tests"
git commit -m "feat: add validation delivery packet"
git commit -m "docs: document validation delivery and commit recovery"
```

If commit service does not work, report:

- exact staged files
- exact unstaged files
- handoff script path
- handoff doc path
- final validation results

Manual push command:

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
- Runtime summary
- Data-source audit
- Validation delivery packet paths
- Remaining risks
- Git commits or handoff script
- Final status

Do not push from Codex unless explicitly instructed.

Completion reference:

- delivery packet artifacts for this phase line:
  - `cajas/reports/validation_delivery_packet.py`
  - `cajas/scripts/build_validation_delivery_packet.py`
