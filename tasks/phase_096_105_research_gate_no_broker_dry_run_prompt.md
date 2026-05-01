# Phase 096–105 Prompt: Research Gate + No-Broker Dry Run Packet

You are working in the `cajas/market-recognition-phase-0` branch of the cajas / Qlib research integration project.

## Current state

Previous phases are complete:

- Phase 041–055: label variants, feature sets, research quality reports, Qlib readiness reports.
- Phase 056–065: research decision packet, candidate promotion manifest, report index, smoke runner.
- Phase 066–075: Qlib adapter contract, dry-run integration packet, compatibility report, adapter smoke runner.
- Phase 076–085: Qlib dataset contract, handler input builder, handler validation, offline ingestion smoke.
- Phase 086–095: CPU-only model/experiment bridge, baseline trainer, metrics, artifacts, model run registry, run comparison.

Recent validation status:

- `./.venv-qlib313/bin/python -m compileall cajas` passed.
- `./.venv-qlib313/bin/python -m pytest cajas/tests` passed with 213 tests.
- `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py` passed with `issues: 0`.
- `find cajas -path "*/init.py" -print` produced no output.
- `git ls-files | grep -E '(^|/)init\.py$' || true` produced no output.
- `./.venv-qlib313/bin/python cajas/scripts/run_qlib_model_bridge_smoke.py --out-root tmp/qlib-model-bridge-smoke` passed.

## Phase 096–105 objective

Add a conservative **Research Gate + No-Broker Dry Run Packet** layer.

This phase should transform model bridge artifacts into a research-only gate decision packet that answers:

1. Is this model run eligible for deeper offline review?
2. Which checks passed, warned, or failed?
3. Which artifacts support the decision?
4. What is explicitly blocked from execution?
5. What manual review actions are required before any later paper-trading phase?

This phase must not introduce broker, live trading, order submission, portfolio optimization, or PnL-driven strategy optimization.

## Hard boundaries

Do not:

- Modify Qlib core.
- Add broker adapters.
- Add live trading.
- Add paper trading execution.
- Add order generation.
- Add position sizing.
- Add PnL optimization.
- Add GPU/CUDA requirements.
- Add network calls.
- Rename existing public CLI commands unless tests/docs are updated and backward compatibility is preserved.
- Add files named `init.py`; continue using `__init__.py` only.

All training or smoke work must remain:

- CPU-only.
- Bounded.
- Deterministic where feasible.
- Suitable for local smoke tests.

## Expected new modules

Add these modules, or equivalent clean names if the existing code structure strongly suggests better names:

### 1. Research gate schema

Create:

- `cajas/reports/research_gate_schema.py`

It should define dataclasses / typed structures for:

- gate input summary
- metric threshold rule
- artifact presence rule
- data quality rule
- split quality rule
- registry/comparison rule
- gate check result
- gate decision
- manual review item
- blocked action
- final gate packet

Suggested decision values:

- `pass`
- `warn`
- `fail`
- `blocked`

Suggested final status values:

- `offline_review_ready`
- `needs_manual_review`
- `blocked`

Use stable JSON-serializable structures.

### 2. Research gate builder

Create:

- `cajas/reports/research_gate_builder.py`

It should read and combine artifacts such as:

- model training contract JSON
- experiment manifest JSON
- metrics JSON
- predictions CSV metadata or row count
- registry JSONL
- comparison JSON
- optional handler smoke report
- optional compatibility report
- optional research decision packet

The builder should produce a research gate packet JSON with:

- source artifact paths
- source artifact existence checks
- metrics summary
- threshold checks
- split checks
- prediction availability checks
- registry/comparison checks
- known boundary constraints
- blocked actions list
- manual review checklist
- final status

The builder should be conservative:

- Missing required artifacts should fail or block.
- Missing optional artifacts should warn.
- Empty predictions should fail.
- Missing metrics should fail.
- Invalid metric values should fail.
- Unknown metrics should be represented as warnings, not silently ignored.
- No PnL metrics should be required.

Suggested default metric rules:

- `macro_f1 >= 0.20` as a weak smoke threshold, warn/fail configurable.
- `accuracy >= 0.20` as a weak smoke threshold, warn/fail configurable.
- Non-empty train/valid/test splits if split metadata exists.
- At least one registry record if registry path is provided.
- Comparison file must identify a top run if comparison path is provided.

Keep thresholds intentionally weak. This is not a profitability gate.

### 3. Research gate CLI

Create:

- `cajas/scripts/build_research_gate_packet.py`

Suggested arguments:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_research_gate_packet.py \
  --contract tmp/qlib-model-bridge-smoke/contract/qlib_model_training_contract.json \
  --experiment-dir tmp/qlib-model-bridge-smoke/experiment \
  --registry tmp/qlib-model-bridge-smoke/registry/model_run_registry.jsonl \
  --comparison tmp/qlib-model-bridge-smoke/comparison/model_run_comparison.json \
  --out tmp/research-gate-smoke/gate/research_gate_packet.json
```

Support optional flags for:

- `--handler-smoke-report`
- `--compatibility-report`
- `--research-decision-packet`
- `--min-macro-f1`
- `--min-accuracy`

The CLI should:

- Create parent directories.
- Write deterministic pretty JSON.
- Exit non-zero only for invalid CLI usage or unreadable required inputs.
- Do not exit non-zero merely because the gate status is `blocked`; blocked status should be encoded in the output packet.

### 4. No-broker dry-run packet

Create:

- `cajas/reports/no_broker_dry_run_packet.py`
- `cajas/scripts/build_no_broker_dry_run_packet.py`

This packet should explicitly represent a dry-run review bundle that cannot execute trades.

It should include:

- gate packet summary
- selected model/run metadata
- artifact references
- explicit disabled capabilities:
  - no broker
  - no order routing
  - no live market data
  - no paper trading execution
  - no portfolio sizing
  - no PnL optimization
- review checklist
- next permitted actions
- next blocked actions

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_no_broker_dry_run_packet.py \
  --gate-packet tmp/research-gate-smoke/gate/research_gate_packet.json \
  --out tmp/research-gate-smoke/no_broker/no_broker_dry_run_packet.json
```

### 5. Research gate summary report

Create:

- `cajas/reports/research_gate_summary.py`
- `cajas/scripts/build_research_gate_summary.py`

Generate a compact human-readable Markdown report from the gate packet and no-broker packet.

Suggested output:

- `research_gate_summary.md`

It should include:

- final status
- passed/warned/failed/blocked check counts
- metric summary
- required artifacts
- optional artifacts
- manual review checklist
- blocked actions
- next allowed steps

### 6. End-to-end smoke runner

Create:

- `cajas/scripts/run_research_gate_smoke.py`

It should orchestrate a bounded smoke flow:

1. Reuse or invoke the existing model bridge smoke flow to create model artifacts under the given out root.
2. Build the research gate packet.
3. Build the no-broker dry-run packet.
4. Build the Markdown summary.
5. Print output paths.

Suggested command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_research_gate_smoke.py --out-root tmp/research-gate-smoke
```

Expected output directories:

- `tmp/research-gate-smoke/model_bridge`
- `tmp/research-gate-smoke/gate`
- `tmp/research-gate-smoke/no_broker`
- `tmp/research-gate-smoke/summary`

## Tests

Add focused tests for all new modules and CLIs.

Expected tests include:

- schema serialization / round trip
- builder with complete artifacts
- builder with missing required artifact
- builder with weak metric pass
- builder with metric fail but JSON still written
- no-broker packet explicitly blocks execution capabilities
- summary Markdown contains final status and blocked actions
- CLI writes output files
- smoke runner creates expected outputs

Keep tests deterministic and lightweight.

## Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`

Add a section such as:

```markdown
## Research Gate and No-Broker Dry Run Workflow
```

Document:

- What the gate packet means.
- What it does not mean.
- How to run the smoke command.
- Why this is still research-only.
- Why blocked status is represented as data rather than a crashing CLI.
- That no broker/live/paper execution exists in this phase.

## Exports

Update package exports if appropriate:

- `cajas/reports/__init__.py`
- `cajas/baseline/__init__.py` only if needed

Do not create any `init.py` files.

## Validation commands

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_research_gate_smoke.py --out-root tmp/research-gate-smoke
```

If `.venv-qlib313` is unavailable, use the active project Python environment, but report the exact command used.

## Commit guidance

After validation passes, create local commits. Suggested split:

1. `feat: add research gate packet workflow`
2. `feat: add no-broker dry-run review packet`
3. `docs: document research gate workflow`

Report:

- changed files
- validation results
- smoke output paths
- commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Final response expected from Codex

Return a compact summary with:

- Summary
- Files changed
- Validation
- Smoke output paths
- Git commits
- Notes / risks
- Final status

Do not push from Codex unless explicitly instructed.
