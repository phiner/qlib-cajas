# Phase 146–175 Prompt: Close the Research Quality Loop — Stable Reproducibility, Governance Remediation, and Readiness Review

You are working on the new branch:

- `phase-next-mega-logic`

The previous branch `cajas/market-recognition-phase-0` completed Phase 116–145 and should already be committed/pushed.

## Current known state

The full research stack exists and validates:

- normalization
- stable fingerprinting
- stable reproducibility check
- governance audit
- artifact lineage
- research run catalog
- offline review packet
- final research bundle
- mega smoke runner

Known latest validation:

- `./.venv-qlib313/bin/python -m compileall cajas` passed
- `./.venv-qlib313/bin/python -m pytest cajas/tests` passed with 250 tests
- `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py` passed with `issues: 0`
- `find cajas -path "*/init.py" -print` produced no output
- `git ls-files | grep -E '(^|/)init\.py$' || true` produced no output
- `./.venv-qlib313/bin/python cajas/scripts/run_full_research_stack_smoke.py --out-root tmp/full-hardening-smoke` completed

Known top-level conservative statuses from Phase 116–145:

- stable reproducibility: `not_stable_reproducible`
- final readiness: `blocked`
- governance audit: `fail`

These are not runtime failures, but Phase 146–175 should make them actionable and, where appropriate, remediated.

## Big objective

Implement **Research Quality Loop Closure**.

This phase should take the existing hardening stack and make it operationally useful:

1. Explain exactly why stable reproducibility is failing.
2. Separate real semantic mismatches from normalization gaps.
3. Add a remediation report for reproducibility.
4. Reduce governance audit false positives without weakening forbidden-boundary checks.
5. Add governance remediation suggestions.
6. Make final readiness status more informative and evidence-based.
7. Add a reviewer decision workflow for approving research-only readiness.
8. Add one end-to-end smoke runner that produces a clear “what remains blocked and why” report.

This is still research-only. Do not add execution capability.

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

# Part A — Stable reproducibility diagnosis

## A1. Reproducibility diff explainer

Create:

- `cajas/reports/stable_reproducibility_explainer.py`
- `cajas/scripts/explain_stable_reproducibility.py`

The explainer should take:

- left stable fingerprint
- right stable fingerprint
- stable reproducibility report
- optional raw manifests

It should output:

- `stable_reproducibility_explanation.json`
- `stable_reproducibility_explanation.md`

The explanation should include:

- top-level status
- mismatch categories
- files that match after normalization
- files that mismatch after normalization
- fields likely responsible for mismatch
- whether mismatch appears semantic or normalizer-related
- recommended remediation
- whether final readiness should remain blocked

Suggested statuses:

- `semantic_mismatch`
- `normalization_gap`
- `missing_artifact`
- `unsupported_artifact_type`
- `expected_variability_not_normalized`
- `unknown`

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/explain_stable_reproducibility.py \
  --left-fingerprint tmp/full-hardening-smoke/fingerprints/run_a_stable_fingerprint.json \
  --right-fingerprint tmp/full-hardening-smoke/fingerprints/run_b_stable_fingerprint.json \
  --stable-repro-report tmp/full-hardening-smoke/stable_repro/stable_reproducibility_report.json \
  --out-json tmp/research-quality-loop-smoke/repro_explain/stable_reproducibility_explanation.json \
  --out-md tmp/research-quality-loop-smoke/repro_explain/stable_reproducibility_explanation.md
```

## A2. Normalization rule coverage report

Create:

- `cajas/reports/normalization_coverage_report.py`
- `cajas/scripts/build_normalization_coverage_report.py`

It should scan normalized artifacts and report:

- supported file types
- skipped file types
- normalized field paths
- preserved field paths
- high-frequency variable fields
- candidate new normalization rules
- risky normalization candidates that should not be normalized automatically

Output:

- `normalization_coverage_report.json`
- `normalization_coverage_report.md`

This should help decide whether a mismatch is a real semantic drift or just a missing normalization rule.

---

# Part B — Reproducibility remediation

## B1. Normalization rule registry

Create:

- `cajas/reports/normalization_rule_registry.py`

The registry should centralize normalization rules used by:

- `artifact_normalizer.py`
- `stable_fingerprint.py`
- coverage reports

It should document each rule with:

- rule id
- description
- target pattern/path
- risk level
- whether enabled by default
- examples

Refactor existing normalization code to use the registry if feasible without large risk.

## B2. Conservative additional normalization

Add conservative normalization only for clearly non-semantic variability found in current smoke outputs, such as:

- generated run root labels like `run_a` / `run_b`
- absolute temp output roots
- per-run manifest file paths
- generated artifact parent directories
- timestamp-like fields
- local working directory
- environment-specific cache paths

Do not normalize:

- metrics
- labels
- feature columns
- target columns
- row counts
- status values
- check names
- governance findings
- blocked actions
- disabled capabilities
- model config values

## B3. Stable reproducibility remediation smoke

Create:

- `cajas/scripts/run_reproducibility_remediation_smoke.py`

It should:

1. Run or reuse two bounded research stack runs.
2. Build fingerprints.
3. Build stable reproducibility report.
4. Build explanation.
5. Build normalization coverage report.
6. Print whether remaining mismatch is semantic or normalization-related.

Expected output paths:

- `tmp/research-quality-loop-smoke/run_a`
- `tmp/research-quality-loop-smoke/run_b`
- `tmp/research-quality-loop-smoke/fingerprints/run_a_stable_fingerprint.json`
- `tmp/research-quality-loop-smoke/fingerprints/run_b_stable_fingerprint.json`
- `tmp/research-quality-loop-smoke/stable_repro/stable_reproducibility_report.json`
- `tmp/research-quality-loop-smoke/repro_explain/stable_reproducibility_explanation.json`
- `tmp/research-quality-loop-smoke/repro_explain/stable_reproducibility_explanation.md`
- `tmp/research-quality-loop-smoke/normalization/normalization_coverage_report.json`
- `tmp/research-quality-loop-smoke/normalization/normalization_coverage_report.md`

Command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_reproducibility_remediation_smoke.py --out-root tmp/research-quality-loop-smoke
```

---

# Part C — Governance remediation

## C1. Governance finding classifier

Create:

- `cajas/audits/governance_finding_classifier.py`

It should classify governance findings into:

- `true_violation`
- `allowed_boundary_documentation`
- `allowed_test_fixture`
- `allowed_cli_argument_name`
- `needs_manual_review`
- `false_positive_candidate`

Use conservative rules.

Do not hide findings. Reclassify and explain them.

## C2. Governance remediation report

Create:

- `cajas/audits/governance_remediation_report.py`
- `cajas/scripts/build_governance_remediation_report.py`

Inputs:

- `research_governance_audit.json`

Outputs:

- `governance_remediation_report.json`
- `governance_remediation_report.md`

Include:

- original governance status
- finding classification counts
- true violations
- allowed boundary documentation
- false positive candidates
- manual review findings
- suggested code/doc remediation
- suggested allowlist updates with justification
- final suggested status:
  - `pass`
  - `warn`
  - `fail`
  - `needs_manual_review`

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_governance_remediation_report.py \
  --governance-audit tmp/full-hardening-smoke/governance/research_governance_audit.json \
  --out-json tmp/research-quality-loop-smoke/governance/governance_remediation_report.json \
  --out-md tmp/research-quality-loop-smoke/governance/governance_remediation_report.md
```

## C3. Optional governance audit tuning

If current governance audit is failing only due to documentation that explicitly says forbidden actions are blocked, tune the audit allowlist conservatively.

Allowed examples:

- “no broker”
- “broker is forbidden”
- “do not add live trading”
- “paper trading execution is blocked”
- “PnL optimization is forbidden”

Still flag implementation-like usage, such as:

- creating broker clients
- sending orders
- route_order
- submit_order
- position sizing functions
- live market data connection
- secrets/credentials

---

# Part D — Readiness status refinement

Update:

- `cajas/reports/final_readiness_packet.py`
- `cajas/reports/final_readiness_summary.py`
- corresponding CLIs

Add optional inputs:

```bash
--stable-reproducibility-explanation ...
--governance-remediation-report ...
--normalization-coverage-report ...
```

Final readiness should include:

- raw reproducibility status
- stable reproducibility status
- reproducibility explanation status
- governance audit status
- governance remediation suggested status
- unresolved true violations
- unresolved semantic mismatches
- unresolved normalization gaps
- manual review items

Suggested final readiness statuses:

- `research_stack_ready_for_manual_review`
- `needs_manual_governance_review`
- `needs_reproducibility_review`
- `needs_normalization_review`
- `blocked`

Decision rules:

- Any true execution violation => `blocked`.
- Any semantic reproducibility mismatch => `needs_reproducibility_review` or `blocked`, depending severity.
- Only normalization gaps with no semantic mismatch => `needs_normalization_review`.
- Governance fail caused only by allowed boundary documentation may become `needs_manual_governance_review` or `research_stack_ready_for_manual_review`, depending other checks.
- Never remove blocked execution actions from packet or summary.

---

# Part E — Reviewer decision workflow

Create:

- `cajas/reports/reviewer_decision_packet.py`
- `cajas/scripts/build_reviewer_decision_packet.py`

The reviewer decision packet should support a human-readable decision input file, not interactive prompts.

Input YAML or JSON example:

```json
{
  "reviewer": "manual",
  "decision": "research_review_approved",
  "notes": "Approved for continued offline research only.",
  "accepted_risks": [
    "Governance documentation findings reviewed as boundary statements."
  ],
  "rejected_actions": [
    "broker integration",
    "live trading",
    "paper trading execution"
  ]
}
```

Allowed decisions:

- `research_review_approved`
- `needs_changes`
- `rejected`

The generated packet should include:

- reviewer decision
- source final readiness packet
- source governance remediation report
- source reproducibility explanation
- accepted risks
- rejected actions
- next allowed steps
- still-forbidden steps

Create a sample decision file:

- `cajas/data_examples/reviewer_decision_example.json`

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_reviewer_decision_packet.py \
  --decision cajas/data_examples/reviewer_decision_example.json \
  --final-readiness-packet tmp/research-quality-loop-smoke/final/final_readiness_packet.json \
  --out tmp/research-quality-loop-smoke/reviewer/reviewer_decision_packet.json
```

---

# Part F — End-to-end research quality loop smoke

Create:

- `cajas/scripts/run_research_quality_loop_smoke.py`

It should orchestrate:

1. Run full research stack smoke or equivalent bounded flow.
2. Build reproducibility explanation.
3. Build normalization coverage report.
4. Build governance remediation report.
5. Build refined final readiness packet.
6. Build refined final readiness summary.
7. Build reviewer decision packet from example decision file.
8. Build final research bundle if existing bundle builder supports updated inputs.
9. Print top-level statuses and output paths.

Command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_research_quality_loop_smoke.py --out-root tmp/research-quality-loop-smoke
```

Expected outputs:

- `tmp/research-quality-loop-smoke/full_stack`
- `tmp/research-quality-loop-smoke/repro_explain/stable_reproducibility_explanation.json`
- `tmp/research-quality-loop-smoke/repro_explain/stable_reproducibility_explanation.md`
- `tmp/research-quality-loop-smoke/normalization/normalization_coverage_report.json`
- `tmp/research-quality-loop-smoke/normalization/normalization_coverage_report.md`
- `tmp/research-quality-loop-smoke/governance/governance_remediation_report.json`
- `tmp/research-quality-loop-smoke/governance/governance_remediation_report.md`
- `tmp/research-quality-loop-smoke/final/final_readiness_packet.json`
- `tmp/research-quality-loop-smoke/final/final_readiness_summary.md`
- `tmp/research-quality-loop-smoke/reviewer/reviewer_decision_packet.json`
- `tmp/research-quality-loop-smoke/bundle/final_research_bundle.json`
- `tmp/research-quality-loop-smoke/bundle/final_research_bundle.md`

---

# Tests

Add focused tests for all new or modified modules and CLIs.

Expected test coverage:

## Reproducibility explanation

- explains matching fingerprints
- explains hash mismatches
- classifies missing artifacts
- identifies normalization gaps
- preserves semantic mismatch classification

## Normalization coverage

- reports normalized fields
- reports preserved fields
- suggests candidate rules for variable path/timestamp fields
- does not suggest normalizing metrics/statuses

## Governance remediation

- classifies boundary documentation as allowed
- classifies implementation-like forbidden patterns as true violations
- produces remediation suggestions
- does not suppress findings silently

## Final readiness refinement

- true governance violation remains blocked
- normalization-only mismatch leads to normalization review
- stable reproducible plus clean governance can reach manual-review readiness
- blocked actions remain present in all statuses

## Reviewer decision

- accepts valid decision file
- rejects invalid decision values
- preserves forbidden actions
- records accepted risks

## Smoke

- research quality loop smoke creates expected outputs

Keep tests deterministic and lightweight.

---

# Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/data_examples/README.md` if appropriate

Add sections such as:

```markdown
## Research Quality Loop Closure

## Reproducibility Explanation and Normalization Coverage

## Governance Remediation

## Reviewer Decision Packet
```

Document:

- Why blocked/fail statuses are useful.
- How to inspect stable reproducibility failure.
- How to interpret governance remediation.
- How a human reviewer can approve offline research only.
- That reviewer approval does not permit trading execution.
- How to run the quality loop smoke command.

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
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_research_quality_loop_smoke.py --out-root tmp/research-quality-loop-smoke
```

If `.venv-qlib313` is unavailable, use the active project Python environment and report exact commands.

---

# Commit guidance

After validation passes, create local commits. Suggested split:

1. `feat: explain and harden stable reproducibility`
2. `feat: add governance remediation workflow`
3. `feat: refine readiness and reviewer decision workflow`
4. `docs: document research quality loop closure`

Report:

- changed files
- validation results
- smoke output paths
- top-level statuses
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
- Top-level statuses
- Git commits
- Notes / risks
- Final status

Do not push from Codex unless explicitly instructed.
