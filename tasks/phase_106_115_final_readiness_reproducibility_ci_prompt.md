# Phase 106–115 Prompt: Stability, Reproducibility, CI Pack, and Final Readiness

You are working in the `cajas/market-recognition-phase-0` branch of the cajas / Qlib research integration project.

## Current state

Completed phases:

- Phase 041–055: label variants, feature sets, research quality reports, Qlib readiness reports.
- Phase 056–065: research decision packet, candidate promotion manifest, report index, smoke runner.
- Phase 066–075: Qlib adapter contract, dry-run integration packet, compatibility report, adapter smoke runner.
- Phase 076–085: Qlib dataset contract, handler input builder, handler validation, offline ingestion smoke.
- Phase 086–095: CPU-only model/experiment bridge, baseline trainer, metrics, artifacts, model run registry, run comparison.
- Phase 096–105: research gate packet, no-broker dry-run packet, markdown gate summary, end-to-end research gate smoke.

Latest validation status:

- `./.venv-qlib313/bin/python -m compileall cajas` passed.
- `./.venv-qlib313/bin/python -m pytest cajas/tests` passed with 222 tests.
- `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py` passed with `issues: 0`.
- `find cajas -path "*/init.py" -print` produced no output.
- `git ls-files | grep -E '(^|/)init\.py$' || true` produced no output.
- `./.venv-qlib313/bin/python cajas/scripts/run_research_gate_smoke.py --out-root tmp/research-gate-smoke` passed.
- Current branch is `cajas/market-recognition-phase-0`.

## Phase 106–115 objective

Add a conservative **Stability, Reproducibility, CI Pack, and Final Readiness** layer.

The goal is to make the full research pipeline easy to validate repeatedly and safely before any future paper-trading phase.

This phase should not add new modeling ambition. It should make the existing Phase 41–105 workflow more reproducible, inspectable, and CI-friendly.

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
- Add heavy training by default.
- Rename existing public CLI commands unless tests/docs are updated and backward compatibility is preserved.
- Add files named `init.py`; continue using `__init__.py` only.

All validation must remain:

- CPU-only.
- Bounded.
- Deterministic where feasible.
- Suitable for local smoke tests and CI-style runs.

## Expected new modules and scripts

### 1. Pipeline manifest collector

Create:

- `cajas/reports/research_pipeline_manifest.py`
- `cajas/scripts/build_research_pipeline_manifest.py`

The manifest should collect metadata for a completed research run directory or smoke root.

It should include:

- phase coverage summary
- expected artifact paths
- existing artifact paths
- missing artifact paths
- artifact sizes
- SHA256 checksums for JSON/CSV/MD artifacts
- command summary if provided
- environment summary:
  - Python version
  - platform
  - working directory
  - optional package versions if safely available
- git summary if safely available:
  - branch
  - current commit
  - dirty status
- timestamp in UTC ISO format

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_research_pipeline_manifest.py \
  --root tmp/research-gate-smoke \
  --out tmp/final-readiness-smoke/manifest/research_pipeline_manifest.json
```

The script should not fail if git metadata is unavailable; represent it as warnings.

### 2. Reproducibility checker

Create:

- `cajas/reports/reproducibility_check.py`
- `cajas/scripts/check_reproducibility.py`

The checker should compare two manifest files or two run roots.

It should report:

- matching artifacts
- missing artifacts
- checksum mismatches
- known intentionally variable fields
- stable fields
- unstable fields
- final reproducibility status:
  - `reproducible`
  - `reproducible_with_warnings`
  - `not_reproducible`

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_reproducibility.py \
  --left tmp/final-readiness-smoke/run_a/manifest/research_pipeline_manifest.json \
  --right tmp/final-readiness-smoke/run_b/manifest/research_pipeline_manifest.json \
  --out tmp/final-readiness-smoke/repro/reproducibility_report.json
```

Do not require byte-perfect equality for fields that are expected to vary, such as timestamps, absolute temporary paths, and runtime duration.

### 3. CI validation plan

Create:

- `cajas/reports/ci_validation_plan.py`
- `cajas/scripts/build_ci_validation_plan.py`

The plan should produce a machine-readable and human-readable list of validation commands grouped by tier:

- Tier 0: path hygiene and compile
- Tier 1: focused unit tests
- Tier 2: full test suite
- Tier 3: bounded smoke flows
- Tier 4: optional heavier research runs

Include estimated intent, not wall-clock guarantees.

Suggested outputs:

- `ci_validation_plan.json`
- `ci_validation_plan.md`

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_ci_validation_plan.py \
  --out-dir tmp/final-readiness-smoke/ci
```

The plan must include the current known validation commands:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_research_gate_smoke.py --out-root tmp/research-gate-smoke
```

### 4. Final readiness packet

Create:

- `cajas/reports/final_readiness_packet.py`
- `cajas/scripts/build_final_readiness_packet.py`

The packet should combine:

- research gate packet summary
- no-broker dry-run packet summary
- pipeline manifest summary
- reproducibility report summary
- CI validation plan summary
- known boundaries
- blocked actions
- permitted next actions
- manual review checklist
- final readiness status

Suggested readiness statuses:

- `research_stack_ready_for_manual_review`
- `needs_reproducibility_review`
- `needs_artifact_review`
- `blocked`

This is not approval for trading. It is only readiness for manual review and possible future planning.

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_final_readiness_packet.py \
  --gate-packet tmp/research-gate-smoke/gate/research_gate_packet.json \
  --no-broker-packet tmp/research-gate-smoke/no_broker/no_broker_dry_run_packet.json \
  --manifest tmp/final-readiness-smoke/manifest/research_pipeline_manifest.json \
  --reproducibility-report tmp/final-readiness-smoke/repro/reproducibility_report.json \
  --ci-plan tmp/final-readiness-smoke/ci/ci_validation_plan.json \
  --out tmp/final-readiness-smoke/final/final_readiness_packet.json
```

### 5. Final readiness Markdown report

Create:

- `cajas/reports/final_readiness_summary.py`
- `cajas/scripts/build_final_readiness_summary.py`

Generate:

- `final_readiness_summary.md`

Include:

- final readiness status
- research gate status
- reproducibility status
- CI tiers
- required artifacts
- missing artifacts
- manual checklist
- explicitly blocked execution actions
- recommended next phase options

### 6. End-to-end final readiness smoke runner

Create:

- `cajas/scripts/run_final_readiness_smoke.py`

It should orchestrate:

1. Run the existing research gate smoke twice under separate roots:
   - `tmp/final-readiness-smoke/run_a`
   - `tmp/final-readiness-smoke/run_b`
2. Build manifests for both runs.
3. Compare reproducibility.
4. Build CI validation plan.
5. Build final readiness packet.
6. Build final readiness markdown summary.
7. Print output paths.

Suggested command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_final_readiness_smoke.py --out-root tmp/final-readiness-smoke
```

Expected output paths:

- `tmp/final-readiness-smoke/run_a`
- `tmp/final-readiness-smoke/run_b`
- `tmp/final-readiness-smoke/manifests/run_a_manifest.json`
- `tmp/final-readiness-smoke/manifests/run_b_manifest.json`
- `tmp/final-readiness-smoke/repro/reproducibility_report.json`
- `tmp/final-readiness-smoke/ci/ci_validation_plan.json`
- `tmp/final-readiness-smoke/ci/ci_validation_plan.md`
- `tmp/final-readiness-smoke/final/final_readiness_packet.json`
- `tmp/final-readiness-smoke/final/final_readiness_summary.md`

## Tests

Add focused tests for all new modules and CLIs.

Expected tests include:

- manifest builder records expected artifacts and checksums
- manifest builder handles missing artifacts with warnings
- reproducibility checker handles matching manifests
- reproducibility checker handles checksum mismatch
- CI validation plan includes required commands
- final readiness packet preserves blocked execution boundaries
- final readiness summary contains final status and blocked actions
- CLI scripts write outputs
- final readiness smoke creates expected files

Keep tests deterministic and lightweight.

## Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`

Add a section such as:

```markdown
## Final Readiness, Reproducibility, and CI Validation
```

Document:

- What final readiness means.
- What it does not mean.
- How to run the smoke command.
- How to interpret reproducibility warnings.
- Why no trading execution exists in this phase.
- How this prepares the project for future manual review.

## Exports

Update package exports if appropriate:

- `cajas/reports/__init__.py`

Do not create any `init.py` files.

## Validation commands

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_final_readiness_smoke.py --out-root tmp/final-readiness-smoke
```

If `.venv-qlib313` is unavailable, use the active project Python environment, but report the exact command used.

## Commit guidance

After validation passes, create local commits. Suggested split:

1. `feat: add research pipeline manifest and reproducibility checks`
2. `feat: add ci validation plan and final readiness packet`
3. `docs: document final readiness workflow`

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
