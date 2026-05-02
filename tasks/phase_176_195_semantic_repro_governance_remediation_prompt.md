# Phase 176–195 Prompt: Semantic Reproducibility + Governance True Violation Remediation

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 146–175 is complete and committed locally.

Latest known validation from Phase 146–175:

- `./.venv-qlib313/bin/python -m compileall cajas` passed.
- `./.venv-qlib313/bin/python -m pytest cajas/tests` passed with 258 tests.
- `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py` passed.
- `find cajas -path "*/init.py" -print` produced no output.
- `git ls-files | grep -E '(^|/)init\\.py$' || true` produced no output.
- `./.venv-qlib313/bin/python cajas/scripts/run_research_quality_loop_smoke.py --out-root tmp/research-quality-loop-smoke` passed.

Known top-level statuses:

- `final_readiness`: `blocked`
- `stable_reproducibility`: `not_stable_reproducible`
- `repro_explanation_classification`: `semantic_mismatch`
- `governance_remediation_suggested_status`: `fail`
- `offline_review / bundle_status`: `needs_governance_review`

## Phase 176–195 objective

Implement a focused remediation pass for the two real blockers:

1. **Semantic reproducibility mismatch**
2. **Governance true violations**

This phase should not add broad new features. It should diagnose, fix, and verify the blockers that keep the research stack in `blocked`.

Target outcome:

- Stable reproducibility should improve from `not_stable_reproducible` to one of:
  - `stable_reproducible`
  - `stable_reproducible_with_warnings`
- Governance remediation should improve from `fail` to one of:
  - `pass`
  - `warn`
  - `needs_manual_review`
- Final readiness should improve from `blocked` to one of:
  - `research_stack_ready_for_manual_review`
  - `needs_reproducibility_review`
  - `needs_manual_governance_review`

Do not force a passing status by hiding real problems. If true semantic mismatch or true governance violations remain, keep the conservative status and explain exactly why.

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

# Part A — Reproduce and localize current blockers

## A1. Add blocker localization report

Create:

- `cajas/reports/research_blocker_localizer.py`
- `cajas/scripts/localize_research_blockers.py`

Inputs:

- stable reproducibility report
- stable reproducibility explanation
- normalization coverage report
- governance audit report
- governance remediation report
- final readiness packet

Outputs:

- `research_blocker_localization.json`
- `research_blocker_localization.md`

The report should identify:

- exact files involved in stable reproducibility mismatch
- whether each mismatch is:
  - metric drift
  - artifact ordering drift
  - timestamp/path normalization gap
  - generated ID drift
  - unstable JSON key ordering
  - CSV row ordering drift
  - run metadata drift
  - governance-induced readiness block
  - unknown semantic drift
- exact governance findings classified as true violations
- whether a true violation is code, test fixture, docs, prompt, or generated output
- recommended fix per blocker
- expected status after fix

Suggested CLI:

```bash
./.venv-qlib313/bin/python cajas/scripts/localize_research_blockers.py \
  --stable-repro-report tmp/research-quality-loop-smoke/full_stack/stable_repro/stable_reproducibility_report.json \
  --repro-explanation tmp/research-quality-loop-smoke/repro_explain/stable_reproducibility_explanation.json \
  --normalization-coverage tmp/research-quality-loop-smoke/normalization/normalization_coverage_report.json \
  --governance-audit tmp/research-quality-loop-smoke/full_stack/governance/research_governance_audit.json \
  --governance-remediation tmp/research-quality-loop-smoke/governance/governance_remediation_report.json \
  --final-readiness tmp/research-quality-loop-smoke/final/final_readiness_packet.json \
  --out-json tmp/remediation-smoke/blockers/research_blocker_localization.json \
  --out-md tmp/remediation-smoke/blockers/research_blocker_localization.md
```

The CLI should tolerate missing optional inputs and report warnings, but should fail on missing required blocker evidence.

## A2. Add detailed artifact diff utility

Create:

- `cajas/reports/normalized_artifact_diff.py`
- `cajas/scripts/diff_normalized_artifacts.py`

It should compare normalized versions of two artifacts and report:

- changed JSON paths
- added/removed keys
- changed scalar values
- changed list lengths
- changed list item ordering
- markdown line diffs if applicable
- severity per difference:
  - `semantic`
  - `normalization_gap`
  - `ordering_only`
  - `metadata_only`
  - `unknown`

This utility should be used by the blocker localizer when possible.

---

# Part B — Fix semantic reproducibility drift

Use the blocker localization output to fix actual causes.

Likely causes to inspect:

- unstable timestamp fields not normalized
- absolute root paths embedded in semantic sections
- generated IDs based on wall-clock time
- non-deterministic ordering of dictionaries/lists
- registry JSONL line ordering
- file discovery ordering from `Path.rglob`
- set iteration ordering
- random seed not fixed in smoke dataset/model generation
- CSV output row ordering
- floating formatting inconsistencies
- aggregate hash includes files that are intentionally run-specific

Expected remediation patterns:

- Sort file discovery paths deterministically.
- Sort JSON keys for stable serialization.
- Sort registry/run catalog entries deterministically.
- Make generated smoke run IDs deterministic where they are only smoke identifiers.
- Normalize run root names and generated directory labels consistently.
- Exclude or normalize only explicitly non-semantic metadata.
- Preserve metrics, labels, columns, statuses, blocked actions, governance findings, and disabled capabilities.

Do not simply drop mismatching artifacts from the fingerprint unless there is a documented reason and a test proving the exclusion is non-semantic.

Update as needed:

- `cajas/reports/artifact_normalizer.py`
- `cajas/reports/normalization_rule_registry.py`
- `cajas/reports/stable_fingerprint.py`
- `cajas/reports/stable_reproducibility_check.py`
- `cajas/reports/stable_reproducibility_explainer.py`
- `cajas/reports/normalization_coverage_report.py`
- any smoke runner that creates unstable-but-non-semantic IDs

Add tests for each fixed drift cause.

---

# Part C — Fix governance true violations

Use the governance remediation output to determine whether findings are genuine.

Expected remediation rules:

- If a finding is real implementation-like execution behavior, remove or rename it.
- If a finding is documentation explicitly stating that execution is forbidden, classify or allowlist it.
- If a finding is a test fixture asserting forbidden behavior is blocked, classify as allowed test fixture.
- If a finding is a CLI flag/documentation phrase that could imply execution, rewrite it to a research-only wording.
- If a finding is generated output from a smoke run, ensure generated outputs clearly mark execution as disabled.

Update as needed:

- `cajas/audits/research_governance_audit.py`
- `cajas/audits/governance_finding_classifier.py`
- `cajas/audits/governance_remediation_report.py`
- docs and prompts if wording causes false positives
- tests that validate forbidden patterns

Do not weaken the audit so much that real execution patterns pass.

Add or update tests:

- true implementation violation remains fail
- boundary documentation is allowed
- forbidden capability in generated packet remains visible as blocked action
- test fixtures can be classified as allowed when they prove blocking
- ambiguous wording becomes manual review instead of pass

---

# Part D — Refine readiness after remediation

Update:

- `cajas/reports/final_readiness_packet.py`
- `cajas/reports/final_readiness_summary.py`
- `cajas/reports/offline_review_packet.py`
- `cajas/reports/final_research_bundle.py`

Readiness logic should reflect remediated evidence:

- If stable reproducibility is now `stable_reproducible` and governance is `pass` or `warn`, final readiness may become `research_stack_ready_for_manual_review`.
- If stable reproducibility is `stable_reproducible_with_warnings`, final readiness should be `needs_reproducibility_review` unless warnings are explicitly manual-review-only.
- If governance is `needs_manual_review`, final readiness should be `needs_manual_governance_review`.
- If any true execution violation remains, final readiness remains `blocked`.

All outputs must still include blocked execution actions:

- no broker
- no live trading
- no paper trading execution
- no order generation
- no order routing
- no PnL optimization
- no position sizing

Reviewer approval must still be offline-research-only.

---

# Part E — Remediation smoke runner

Create:

- `cajas/scripts/run_research_remediation_smoke.py`

It should orchestrate:

1. Run `run_research_quality_loop_smoke.py` or equivalent bounded flow.
2. Build blocker localization report.
3. Run normalized artifact diff for mismatching artifacts if available.
4. Rebuild stable fingerprints and stable reproducibility report after fixes.
5. Rebuild governance audit and governance remediation report.
6. Rebuild final readiness packet and summary.
7. Rebuild offline review packet and final research bundle if supported.
8. Print before/after status comparison.

Suggested command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_research_remediation_smoke.py --out-root tmp/research-remediation-smoke
```

Expected outputs:

- `tmp/research-remediation-smoke/quality_loop`
- `tmp/research-remediation-smoke/blockers/research_blocker_localization.json`
- `tmp/research-remediation-smoke/blockers/research_blocker_localization.md`
- `tmp/research-remediation-smoke/diffs/`
- `tmp/research-remediation-smoke/stable_repro/stable_reproducibility_report.json`
- `tmp/research-remediation-smoke/governance/research_governance_audit.json`
- `tmp/research-remediation-smoke/governance/governance_remediation_report.json`
- `tmp/research-remediation-smoke/final/final_readiness_packet.json`
- `tmp/research-remediation-smoke/final/final_readiness_summary.md`
- `tmp/research-remediation-smoke/review/offline_review_packet.json`
- `tmp/research-remediation-smoke/bundle/final_research_bundle.json`
- `tmp/research-remediation-smoke/bundle/final_research_bundle.md`

---

# Tests

Add focused tests for all new/modified modules and CLIs.

Expected test coverage:

## Blocker localization

- localizes reproducibility mismatches to artifact paths
- classifies timestamp/path drift as normalization gap
- classifies metric/status drift as semantic mismatch
- localizes governance true violations
- produces Markdown summary

## Normalized artifact diff

- reports JSON path changes
- reports added/removed keys
- reports ordering-only list differences
- preserves semantic scalar differences
- handles Markdown line differences

## Reproducibility remediation

- deterministic path discovery
- deterministic JSON output
- stable fingerprint equal for equivalent generated run roots
- stable fingerprint unequal for real metric/status changes
- stable reproducibility improves when only non-semantic drift exists

## Governance remediation

- real forbidden implementation remains violation
- documentation boundary statements are allowed
- generated blocked actions are not treated as execution implementation
- test fixture patterns are classified as allowed fixtures
- ambiguous findings require manual review

## Readiness

- final readiness moves out of blocked only when blockers are resolved or reduced to manual-review categories
- true execution violation keeps readiness blocked
- reviewer approval remains offline-research-only
- blocked actions remain present

## Smoke

- remediation smoke creates expected files
- remediation smoke prints top-level before/after statuses

Keep tests deterministic and lightweight.

---

# Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/data_examples/README.md` if reviewer example semantics changed

Add sections such as:

```markdown
## Research Remediation Workflow

## Semantic Reproducibility Blockers

## Governance True Violation Remediation

## Readiness Status After Remediation
```

Document:

- How to run the remediation smoke.
- How to interpret blocker localization.
- How to interpret normalized artifact diffs.
- How governance findings are classified.
- What statuses are acceptable for offline manual review.
- That no status enables broker/live/paper execution.

---

# Exports

Update package exports if appropriate:

- `cajas/reports/__init__.py`
- `cajas/audits/__init__.py`

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
./.venv-qlib313/bin/python cajas/scripts/run_research_remediation_smoke.py --out-root tmp/research-remediation-smoke
```

If `.venv-qlib313` is unavailable, use the active project Python environment and report exact commands.

---

# Commit guidance

After validation passes, create local commits. Suggested split:

1. `feat: localize research readiness blockers`
2. `fix: remediate stable reproducibility drift`
3. `fix: remediate governance true violation findings`
4. `feat: add research remediation smoke workflow`
5. `docs: document research remediation workflow`

Report:

- changed files
- validation results
- smoke output paths
- before/after top-level statuses
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
- Git commits
- Notes / risks
- Final status

Do not push from Codex unless explicitly instructed.
