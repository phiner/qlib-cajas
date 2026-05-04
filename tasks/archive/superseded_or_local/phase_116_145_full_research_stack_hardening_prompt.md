# Phase 116–145 Prompt: Full Research Stack Hardening, Reproducibility, Governance, and Offline Review Pack

You are working in the `cajas/market-recognition-phase-0` branch of the cajas / Qlib research integration project.

## Current state

Completed phases:

- Phase 041–055: label variants, feature sets, research quality reports, Qlib readiness reports.
- Phase 056–065: research decision packet, candidate promotion manifest, report index, smoke runner.
- Phase 066–075: Qlib adapter contract, dry-run integration packet, compatibility report, adapter smoke runner.
- Phase 076–085: Qlib dataset contract, handler input builder, handler validation, offline ingestion smoke.
- Phase 086–095: CPU-only model/experiment bridge, baseline trainer, metrics, artifacts, model run registry, run comparison.
- Phase 096–105: research gate packet, no-broker dry-run packet, markdown gate summary, end-to-end research gate smoke.
- Phase 106–115: research pipeline manifest, reproducibility checker, CI validation plan, final readiness packet, final readiness smoke.

Latest validation status:

- `./.venv-qlib313/bin/python -m compileall cajas` passed.
- `./.venv-qlib313/bin/python -m pytest cajas/tests` passed with 234 tests.
- `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py` passed with `issues: 0`.
- `find cajas -path "*/init.py" -print` produced no output.
- `git ls-files | grep -E '(^|/)init\.py$' || true` produced no output.
- `./.venv-qlib313/bin/python cajas/scripts/run_final_readiness_smoke.py --out-root tmp/final-readiness-smoke` passed.
- Current branch is `cajas/market-recognition-phase-0`.

Known current issue:

- Final readiness smoke currently reports raw reproducibility as `not_reproducible`.
- This is expected because generated artifacts include path, timestamp, and run-root variability.
- The next task should harden reproducibility and complete as much offline research governance logic as reasonable in one large implementation pass.

## Big-task objective

Implement a comprehensive **Full Research Stack Hardening, Reproducibility, Governance, and Offline Review Pack**.

This is intentionally a large task. Do as much of the remaining non-execution research logic as practical in one pass.

Primary goals:

1. Normalize artifacts so semantically equivalent smoke runs can be compared.
2. Build stable fingerprints and stable reproducibility reports.
3. Integrate stable reproducibility into final readiness.
4. Add governance/audit policy checks for forbidden capabilities.
5. Add artifact lineage graph/reporting.
6. Add experiment/run catalog summary across generated outputs.
7. Add offline review checklist and reviewer decision packet.
8. Add consolidated final research bundle with JSON + Markdown outputs.
9. Add one end-to-end mega smoke runner that exercises the full bounded research path.
10. Keep everything research-only and deterministic enough for local validation.

## Non-negotiable hard boundaries

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
- Add slippage, execution simulation, or broker fill logic.
- Add GPU/CUDA requirements.
- Add network calls.
- Add secrets or credentials handling.
- Add heavy training by default.
- Rename existing public CLI commands unless tests/docs are updated and backward compatibility is preserved.
- Add files named `init.py`; continue using `__init__.py` only.

All validation must remain:

- CPU-only.
- Bounded.
- Deterministic where feasible.
- Suitable for local smoke tests and CI-style runs.

If the implementation gets too large, prefer completing coherent vertical slices with tests over leaving many half-finished modules.

---

# Part A — Stable artifact normalization and fingerprinting

## A1. Artifact normalizer

Create:

- `cajas/reports/artifact_normalizer.py`
- `cajas/scripts/normalize_research_artifact.py`

Support JSON and Markdown at minimum.

For JSON:

- Load JSON.
- Recursively normalize:
  - absolute paths
  - known temporary root path segments
  - timestamps
  - generated output root names
  - environment-specific working directories
  - git dirty text if environment-specific
  - command invocation paths rooted in temp dirs
- Preserve semantic values:
  - status fields
  - metric values
  - row counts
  - column names
  - model config
  - disabled capabilities
  - blocked actions
  - check names
  - decision reasons

For Markdown:

- Normalize known path/timestamp lines.
- Preserve checklist content, statuses, headings, and blocked actions.

Output:

- normalized file
- normalization metadata
- normalized field list
- preserved field list
- warning list

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/normalize_research_artifact.py \
  --input tmp/final-readiness-smoke/final/final_readiness_packet.json \
  --out tmp/full-hardening-smoke/normalized/final_readiness_packet.normalized.json
```

## A2. Stable fingerprint builder

Create:

- `cajas/reports/stable_fingerprint.py`
- `cajas/scripts/build_stable_fingerprint.py`

The fingerprint builder should:

- Accept a file or directory root.
- Normalize supported artifacts.
- Compute stable SHA256 from normalized content.
- Produce:
  - input path
  - included files
  - skipped files
  - per-file normalized hash
  - aggregate stable hash
  - normalization rule summary
  - warnings

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_stable_fingerprint.py \
  --root tmp/full-hardening-smoke/run_a \
  --out tmp/full-hardening-smoke/fingerprints/run_a_stable_fingerprint.json
```

## A3. Stable reproducibility checker

Create:

- `cajas/reports/stable_reproducibility_check.py`
- `cajas/scripts/check_stable_reproducibility.py`

Compare two stable fingerprint reports.

Report:

- matching normalized artifacts
- missing normalized artifacts
- changed normalized hashes
- skipped files
- expected variability absorbed by normalization
- true mismatches
- final stable reproducibility status:
  - `stable_reproducible`
  - `stable_reproducible_with_warnings`
  - `not_stable_reproducible`

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_stable_reproducibility.py \
  --left tmp/full-hardening-smoke/fingerprints/run_a_stable_fingerprint.json \
  --right tmp/full-hardening-smoke/fingerprints/run_b_stable_fingerprint.json \
  --out tmp/full-hardening-smoke/stable_repro/stable_reproducibility_report.json
```

---

# Part B — Final readiness integration hardening

Update:

- `cajas/reports/final_readiness_packet.py`
- `cajas/scripts/build_final_readiness_packet.py`
- `cajas/reports/final_readiness_summary.py`
- `cajas/scripts/build_final_readiness_summary.py`

Add optional support for:

```bash
--stable-reproducibility-report tmp/full-hardening-smoke/stable_repro/stable_reproducibility_report.json
```

Decision behavior:

- If raw reproducibility is `not_reproducible` but stable reproducibility is `stable_reproducible`, final readiness may become `research_stack_ready_for_manual_review` only if no other blocking conditions exist.
- If stable reproducibility is `stable_reproducible_with_warnings`, final readiness should be `needs_reproducibility_review`.
- If stable reproducibility is `not_stable_reproducible`, final readiness remains `blocked`.
- The packet must still explicitly block broker/live/paper execution.
- Readiness never means trading approval.

Markdown summary must include:

- raw reproducibility status
- stable reproducibility status
- normalized artifact count
- true mismatch count
- expected variability count
- readiness interpretation
- explicitly blocked actions

---

# Part C — Governance and forbidden capability audit

Create:

- `cajas/audits/research_governance_audit.py`
- `cajas/scripts/audit_research_governance.py`

The governance audit should scan configured project paths for forbidden execution-related patterns.

Default scan roots:

- `cajas`
- optionally `tasks`
- optionally `docs`

Forbidden or suspicious capability categories:

- broker integration
- live trading
- paper trading execution
- order generation
- order routing
- position sizing
- portfolio optimization
- PnL optimization
- execution simulation
- network calls
- credentials/secrets
- GPU/CUDA requirement

This audit must be conservative but not noisy. Implement allowlists for documentation phrases that explicitly say these are blocked/forbidden.

Output:

- JSON audit report
- category counts
- findings with file path, line number, category, severity, snippet
- allowlisted findings
- final status:
  - `pass`
  - `warn`
  - `fail`

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/audit_research_governance.py \
  --root cajas \
  --out tmp/full-hardening-smoke/governance/research_governance_audit.json
```

The audit should not block docs that say “no broker” or “broker is forbidden”.

---

# Part D — Artifact lineage graph

Create:

- `cajas/reports/artifact_lineage.py`
- `cajas/scripts/build_artifact_lineage.py`

Build a simple lineage graph across generated artifacts.

Represent:

- nodes:
  - artifact path
  - artifact type
  - phase group
  - exists/missing
  - checksum if available
- edges:
  - source artifact → derived artifact
  - command/script relationship if known
- phase groups:
  - labels/features
  - decision packet
  - adapter
  - dataset/handler
  - model bridge
  - research gate
  - final readiness
  - reproducibility hardening
  - governance
  - review bundle

Outputs:

- `artifact_lineage.json`
- `artifact_lineage.md`

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_artifact_lineage.py \
  --root tmp/full-hardening-smoke \
  --out-json tmp/full-hardening-smoke/lineage/artifact_lineage.json \
  --out-md tmp/full-hardening-smoke/lineage/artifact_lineage.md
```

---

# Part E — Experiment/run catalog

Create:

- `cajas/reports/research_run_catalog.py`
- `cajas/scripts/build_research_run_catalog.py`

The catalog should scan a run root and summarize:

- model run IDs if present
- experiment manifests
- metrics files
- registry files
- comparison files
- gate packets
- readiness packets
- reproducibility reports
- governance reports

Outputs:

- `research_run_catalog.json`
- `research_run_catalog.md`

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_research_run_catalog.py \
  --root tmp/full-hardening-smoke \
  --out-json tmp/full-hardening-smoke/catalog/research_run_catalog.json \
  --out-md tmp/full-hardening-smoke/catalog/research_run_catalog.md
```

---

# Part F — Offline reviewer packet

Create:

- `cajas/reports/offline_review_packet.py`
- `cajas/scripts/build_offline_review_packet.py`

The offline review packet is for human review only.

Inputs may include:

- final readiness packet
- final readiness summary
- stable reproducibility report
- governance audit report
- artifact lineage
- research run catalog

Output JSON should include:

- overall review state:
  - `ready_for_human_review`
  - `needs_reproducibility_review`
  - `needs_governance_review`
  - `blocked`
- review checklist
- reviewer questions
- required sign-off areas
- explicitly blocked actions
- permitted next actions
- artifact references
- summary of unresolved issues

Output Markdown should include the same content in readable form.

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_offline_review_packet.py \
  --final-readiness-packet tmp/full-hardening-smoke/final/final_readiness_packet.json \
  --stable-reproducibility-report tmp/full-hardening-smoke/stable_repro/stable_reproducibility_report.json \
  --governance-audit tmp/full-hardening-smoke/governance/research_governance_audit.json \
  --artifact-lineage tmp/full-hardening-smoke/lineage/artifact_lineage.json \
  --run-catalog tmp/full-hardening-smoke/catalog/research_run_catalog.json \
  --out-json tmp/full-hardening-smoke/review/offline_review_packet.json \
  --out-md tmp/full-hardening-smoke/review/offline_review_packet.md
```

---

# Part G — Consolidated final research bundle

Create:

- `cajas/reports/final_research_bundle.py`
- `cajas/scripts/build_final_research_bundle.py`

The bundle should collect top-level outputs into one index.

Inputs:

- final readiness packet
- final readiness summary
- stable reproducibility report
- governance audit
- artifact lineage
- run catalog
- offline review packet
- CI validation plan

Outputs:

- `final_research_bundle.json`
- `final_research_bundle.md`

It should include:

- bundle status
- key artifact paths
- top-level statuses
- known risks
- blocked execution actions
- next allowed steps
- next forbidden steps
- manual review checklist

CLI example:

```bash
./.venv-qlib313/bin/python cajas/scripts/build_final_research_bundle.py \
  --root tmp/full-hardening-smoke \
  --out-json tmp/full-hardening-smoke/bundle/final_research_bundle.json \
  --out-md tmp/full-hardening-smoke/bundle/final_research_bundle.md
```

---

# Part H — Mega smoke runner

Create:

- `cajas/scripts/run_full_research_stack_smoke.py`

It should orchestrate the full bounded research path:

1. Run existing final readiness smoke twice or equivalent research gate smoke twice:
   - `tmp/full-hardening-smoke/run_a`
   - `tmp/full-hardening-smoke/run_b`
2. Build stable fingerprints:
   - `fingerprints/run_a_stable_fingerprint.json`
   - `fingerprints/run_b_stable_fingerprint.json`
3. Build stable reproducibility report:
   - `stable_repro/stable_reproducibility_report.json`
4. Build updated final readiness packet and summary:
   - `final/final_readiness_packet.json`
   - `final/final_readiness_summary.md`
5. Run governance audit:
   - `governance/research_governance_audit.json`
6. Build artifact lineage:
   - `lineage/artifact_lineage.json`
   - `lineage/artifact_lineage.md`
7. Build research run catalog:
   - `catalog/research_run_catalog.json`
   - `catalog/research_run_catalog.md`
8. Build offline review packet:
   - `review/offline_review_packet.json`
   - `review/offline_review_packet.md`
9. Build final research bundle:
   - `bundle/final_research_bundle.json`
   - `bundle/final_research_bundle.md`
10. Print output paths and top-level statuses.

Suggested command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_full_research_stack_smoke.py --out-root tmp/full-hardening-smoke
```

Expected output paths:

- `tmp/full-hardening-smoke/run_a`
- `tmp/full-hardening-smoke/run_b`
- `tmp/full-hardening-smoke/fingerprints/run_a_stable_fingerprint.json`
- `tmp/full-hardening-smoke/fingerprints/run_b_stable_fingerprint.json`
- `tmp/full-hardening-smoke/stable_repro/stable_reproducibility_report.json`
- `tmp/full-hardening-smoke/final/final_readiness_packet.json`
- `tmp/full-hardening-smoke/final/final_readiness_summary.md`
- `tmp/full-hardening-smoke/governance/research_governance_audit.json`
- `tmp/full-hardening-smoke/lineage/artifact_lineage.json`
- `tmp/full-hardening-smoke/lineage/artifact_lineage.md`
- `tmp/full-hardening-smoke/catalog/research_run_catalog.json`
- `tmp/full-hardening-smoke/catalog/research_run_catalog.md`
- `tmp/full-hardening-smoke/review/offline_review_packet.json`
- `tmp/full-hardening-smoke/review/offline_review_packet.md`
- `tmp/full-hardening-smoke/bundle/final_research_bundle.json`
- `tmp/full-hardening-smoke/bundle/final_research_bundle.md`

---

# Tests

Add focused tests for all new modules and CLIs.

Expected tests include:

## Normalization/fingerprint/reproducibility

- JSON normalizer removes expected timestamp/path variability.
- JSON normalizer preserves semantic decision fields.
- Markdown normalizer removes expected path/timestamp variability.
- Stable fingerprint is identical for semantically equivalent artifacts with different roots.
- Stable fingerprint differs for real semantic changes.
- Stable reproducibility checker reports stable reproducible for matching normalized artifacts.
- Stable reproducibility checker reports not stable reproducible for true hash mismatch.

## Final readiness integration

- Final readiness packet integrates stable reproducibility conservatively.
- Final readiness summary includes stable reproducibility section.
- Broker/live/paper actions remain blocked even if stable reproducibility passes.

## Governance

- Governance audit flags forbidden implementation patterns.
- Governance audit allowlists documentation phrases that explicitly forbid those capabilities.
- Governance audit report has stable categories and severity.

## Lineage/catalog/review/bundle

- Artifact lineage includes expected nodes and edges.
- Research run catalog summarizes metrics/gate/readiness reports.
- Offline review packet preserves blocked actions and review questions.
- Final research bundle includes top-level statuses and artifact references.

## CLI/smoke

- CLI scripts write expected outputs.
- Mega smoke creates expected files.

Keep tests deterministic and lightweight.

---

# Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`

Add sections such as:

```markdown
## Stable Reproducibility and Artifact Normalization

## Research Governance Audit

## Artifact Lineage and Offline Review Bundle

## Full Research Stack Smoke
```

Document:

- Why raw run directories may differ.
- What normalization does.
- What normalization does not hide.
- How to run the full smoke command.
- How to interpret stable reproducibility statuses.
- How to interpret governance audit findings.
- What final research bundle means.
- That this still does not permit broker/live/paper execution.

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
./.venv-qlib313/bin/python cajas/scripts/run_full_research_stack_smoke.py --out-root tmp/full-hardening-smoke
```

If `.venv-qlib313` is unavailable, use the active project Python environment, but report the exact command used.

---

# Commit guidance

After validation passes, create local commits. Suggested split:

1. `feat: add stable normalization and reproducibility hardening`
2. `feat: add research governance lineage and catalog reports`
3. `feat: add offline review and final research bundle`
4. `docs: document full research stack hardening workflow`

If the diff is too large, use more commits by coherent subsystem.

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

---

# Final response expected from Codex

Return a compact summary with:

- Summary
- Files changed
- Validation
- Smoke output paths
- Git commits
- Notes / risks
- Final status

Do not push from Codex unless explicitly instructed.
