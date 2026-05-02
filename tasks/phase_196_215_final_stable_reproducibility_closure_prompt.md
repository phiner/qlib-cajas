# Phase 196–215 Prompt: Final Stable Reproducibility Closure

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 176–195 completed and committed locally.

Latest known validation:

- `./.venv-qlib313/bin/python -m compileall cajas` passed.
- `./.venv-qlib313/bin/python -m pytest cajas/tests` passed with 263 tests.
- `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py` passed.
- `find cajas -path "*/init.py" -print` produced no output.
- `git ls-files | grep -E '(^|/)init\\.py$' || true` produced no output.
- `./.venv-qlib313/bin/python cajas/scripts/run_research_remediation_smoke.py --out-root tmp/research-remediation-smoke` passed.

Latest top-level status changes:

Before Phase 176–195:

- `final_readiness`: `blocked`
- `stable_reproducibility`: `not_stable_reproducible`
- `governance_remediation_suggested_status`: `fail`

After Phase 176–195:

- `final_readiness`: `needs_reproducibility_review`
- `stable_reproducibility`: `not_stable_reproducible`
- `governance_remediation_suggested_status`: `needs_manual_review`

Important interpretation:

- Governance is no longer a hard fail; it is now a manual-review item.
- Final readiness moved out of `blocked`.
- The remaining blocker is stable reproducibility.
- Phase 196–215 should focus narrowly on closing the exact reproducibility mismatches reported by blocker localization.

## Phase 196–215 objective

Implement **Final Stable Reproducibility Closure**.

Target outcome:

- Stable reproducibility should move from:

```text
not_stable_reproducible
```

to one of:

```text
stable_reproducible_with_warnings
stable_reproducible
```

Final readiness should move from:

```text
needs_reproducibility_review
```

to one of:

```text
needs_manual_governance_review
research_stack_ready_for_manual_review
```

Do not force passing statuses. If true semantic mismatch remains, keep the conservative status and explain exactly why.

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
- Add slippage/fill simulation.
- Add network calls.
- Add GPU/CUDA requirement.
- Add secrets or credentials handling.
- Add heavy training by default.
- Rename existing public CLIs unless preserving backwards compatibility.
- Add files named `init.py`; continue using `__init__.py`.

All validation must remain:

- CPU-only.
- Bounded.
- Deterministic where feasible.
- Suitable for local smoke tests and CI-style runs.

---

# Part A — Inspect current mismatch evidence

Start by running or reusing:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_research_remediation_smoke.py --out-root tmp/research-remediation-smoke
```

Inspect:

- `tmp/research-remediation-smoke/blockers/research_blocker_localization.json`
- `tmp/research-remediation-smoke/blockers/research_blocker_localization.md`
- `tmp/research-remediation-smoke/stable_repro/stable_reproducibility_report.json`
- `tmp/research-remediation-smoke/quality_loop/repro_explain/stable_reproducibility_explanation.json`
- any generated diff files under `tmp/research-remediation-smoke/diffs/`, if present

Identify exact mismatch artifacts and classify each one as:

- true semantic mismatch
- ordering-only drift
- timestamp/path/run-root drift
- generated ID drift
- JSONL line ordering drift
- CSV row ordering drift
- file discovery ordering drift
- normalizer coverage gap
- unsupported artifact type
- aggregate hash design issue
- unknown

Do not guess. Use the existing reports first.

---

# Part B — Close deterministic artifact drift

Fix only causes supported by evidence.

Likely safe remediation areas:

## B1. Deterministic file discovery

Ensure all directory scans use deterministic ordering:

- sort `Path.rglob(...)` results
- sort included artifact lists
- sort skipped artifact lists
- sort warning lists when order is not semantically meaningful

Likely files:

- `cajas/reports/stable_fingerprint.py`
- `cajas/reports/research_pipeline_manifest.py`
- `cajas/reports/artifact_lineage.py`
- `cajas/reports/research_run_catalog.py`
- any bundle/catalog/lineage scanners

## B2. Deterministic JSON / JSONL serialization

Ensure JSON writes use deterministic serialization where appropriate:

- `sort_keys=True`
- stable indentation
- stable list ordering if list is not semantically ordered
- stable float representation if needed

For JSONL:

- normalize line objects
- sort JSONL records by stable key when records are unordered
- normalize run-specific IDs only when non-semantic
- preserve semantic values such as metrics, labels, statuses, and blocked actions

Likely files:

- `cajas/reports/artifact_normalizer.py`
- `cajas/reports/stable_fingerprint.py`
- registry/catalog/bundle builders

## B3. Normalize remaining non-semantic run identity

Normalize only explicitly non-semantic fields:

- run root labels such as `run_a` / `run_b`
- temporary output root paths
- generated smoke IDs based only on output path
- generated artifact parent directory names
- manifest local paths
- timestamps
- current working directory
- cache path / local environment metadata

Do not normalize:

- metrics
- model config
- row counts
- feature columns
- label columns
- status fields
- decision values
- blocked actions
- disabled capabilities
- governance true finding content
- reviewer decision content

Likely files:

- `cajas/reports/artifact_normalizer.py`
- `cajas/reports/normalization_rule_registry.py`
- `cajas/reports/normalization_coverage_report.py`

## B4. CSV and Markdown stability

If mismatch comes from CSV or Markdown:

- For CSV metadata-only comparisons, compare stable schema/row count/checksum after normalizing run-root paths.
- Sort rows only if the CSV represents unordered records.
- Do not sort time-series rows or prediction rows if order is semantic.
- For Markdown summaries, normalize only path/timestamp/run-root lines.
- Preserve status sections and reviewer decisions.

---

# Part C — Improve mismatch explanation quality

Update:

- `cajas/reports/stable_reproducibility_explainer.py`
- `cajas/reports/research_blocker_localizer.py`
- `cajas/reports/normalized_artifact_diff.py`

The reports should clearly state:

- which mismatch was fixed
- which mismatch remains
- whether remaining mismatch is semantic or normalization-only
- exact artifact paths
- exact JSON paths or line locations where possible
- recommended next action

If stable reproducibility remains `not_stable_reproducible`, the explanation must identify the exact remaining blocker and why it is not safe to normalize automatically.

---

# Part D — Readiness transition after reproducibility closure

Update as needed:

- `cajas/reports/final_readiness_packet.py`
- `cajas/reports/final_readiness_summary.py`
- `cajas/reports/offline_review_packet.py`
- `cajas/reports/final_research_bundle.py`

Decision rules:

- If stable reproducibility becomes `stable_reproducible` and governance is `needs_manual_review`, final readiness should become `needs_manual_governance_review`.
- If stable reproducibility becomes `stable_reproducible_with_warnings`, final readiness should become `needs_reproducibility_review` or `needs_manual_governance_review`, depending warning severity.
- If stable reproducibility becomes `stable_reproducible` and governance becomes `pass` or `warn`, final readiness may become `research_stack_ready_for_manual_review`.
- Any true execution violation still keeps readiness blocked.
- All outputs must preserve explicit blocked execution actions.

Blocked actions must still include:

- no broker
- no live trading
- no paper trading execution
- no order generation
- no order routing
- no PnL optimization
- no position sizing

Reviewer approval remains offline-research-only.

---

# Part E — Final reproducibility closure smoke

Create or update:

- `cajas/scripts/run_final_reproducibility_closure_smoke.py`

It should orchestrate:

1. Run the current remediation smoke.
2. Read blocker localization.
3. Build stable fingerprints for equivalent bounded runs.
4. Build stable reproducibility report.
5. Build reproducibility explanation.
6. Build normalization coverage report.
7. Build governance remediation report.
8. Build final readiness packet and summary.
9. Build offline review packet and final research bundle.
10. Print before/after status summary.

Suggested command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_final_reproducibility_closure_smoke.py --out-root tmp/final-repro-closure-smoke
```

Expected outputs:

- `tmp/final-repro-closure-smoke/remediation`
- `tmp/final-repro-closure-smoke/fingerprints/run_a_stable_fingerprint.json`
- `tmp/final-repro-closure-smoke/fingerprints/run_b_stable_fingerprint.json`
- `tmp/final-repro-closure-smoke/stable_repro/stable_reproducibility_report.json`
- `tmp/final-repro-closure-smoke/repro_explain/stable_reproducibility_explanation.json`
- `tmp/final-repro-closure-smoke/repro_explain/stable_reproducibility_explanation.md`
- `tmp/final-repro-closure-smoke/normalization/normalization_coverage_report.json`
- `tmp/final-repro-closure-smoke/normalization/normalization_coverage_report.md`
- `tmp/final-repro-closure-smoke/governance/governance_remediation_report.json`
- `tmp/final-repro-closure-smoke/final/final_readiness_packet.json`
- `tmp/final-repro-closure-smoke/final/final_readiness_summary.md`
- `tmp/final-repro-closure-smoke/review/offline_review_packet.json`
- `tmp/final-repro-closure-smoke/bundle/final_research_bundle.json`
- `tmp/final-repro-closure-smoke/bundle/final_research_bundle.md`

---

# Tests

Add focused tests for all new/modified behavior.

Required coverage:

## Determinism

- directory scanning produces stable included/skipped file order
- stable fingerprint aggregate hash is independent of file discovery order
- JSON output is stable across equivalent inputs
- JSONL normalization handles unordered non-semantic records
- run-root path differences normalize to equal fingerprints

## Semantic preservation

- metric differences still produce mismatched fingerprint
- status differences still produce mismatched fingerprint
- blocked action differences still produce mismatched fingerprint
- governance true finding differences still produce mismatched fingerprint
- reviewer decision differences still produce mismatched fingerprint

## Explanation/localization

- blocker localizer identifies exact artifact mismatch
- normalized artifact diff reports JSON paths
- explanation distinguishes semantic mismatch from normalization gap
- remaining blocker is documented when not safe to normalize

## Readiness

- stable reproducible + governance manual review leads to `needs_manual_governance_review`
- stable reproducible + governance pass/warn can lead to `research_stack_ready_for_manual_review`
- stable reproducible with warnings does not over-promote readiness
- execution-related blocked actions remain present in all outputs

## Smoke

- final reproducibility closure smoke creates expected files
- smoke reports top-level statuses
- smoke does not require GPU/CUDA/network

Keep tests deterministic and lightweight.

---

# Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `tasks/phase_196_215_final_stable_reproducibility_closure_prompt.md`

Add sections such as:

```markdown
## Final Stable Reproducibility Closure

## Deterministic Artifact Fingerprints

## Readiness After Reproducibility Closure
```

Document:

- How to run final reproducibility closure smoke.
- How to interpret stable reproducibility status.
- Which fields are safe to normalize.
- Which fields must remain semantic.
- How readiness may move to manual governance review.
- That no readiness status enables broker/live/paper execution.

---

# Exports

Update package exports if appropriate:

- `cajas/reports/__init__.py`
- `cajas/audits/__init__.py` only if needed

Do not create any `init.py` files.

---

# Validation commands

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_final_reproducibility_closure_smoke.py --out-root tmp/final-repro-closure-smoke
```

If `.venv-qlib313` is unavailable, use the active project Python environment and report exact commands.

---

# Commit guidance

After validation passes, create local commits. Suggested split:

1. `fix: close deterministic stable reproducibility drift`
2. `feat: improve reproducibility blocker explanations`
3. `feat: add final reproducibility closure smoke`
4. `docs: document final reproducibility closure`

Report:

- changed files
- validation results
- smoke output paths
- before/after top-level statuses
- remaining blockers, if any
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
- Smoke output paths
- Before/after top-level statuses
- Remaining blockers
- Git commits
- Notes / risks
- Final status

Do not push from Codex unless explicitly instructed.
