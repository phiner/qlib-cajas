# Phase 216–235 Prompt: Manual Governance Review Closure + Research-Only Approval Packet

You are working on branch:

- `phase-next-mega-logic`

## Current state

Phase 196–215 completed and committed locally.

Latest known validation:

- `./.venv-qlib313/bin/python -m compileall cajas` passed.
- `./.venv-qlib313/bin/python -m pytest cajas/tests` passed with 267 tests.
- `./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py` passed.
- `find cajas -path "*/init.py" -print` produced no output.
- `git ls-files | grep -E '(^|/)init\\.py$' || true` produced no output.
- `./.venv-qlib313/bin/python cajas/scripts/run_final_reproducibility_closure_smoke.py --out-root tmp/final-repro-closure-smoke` passed.

Latest top-level status changes:

Before Phase 196–215:

- `final_readiness`: `needs_reproducibility_review`
- `stable_reproducibility`: `not_stable_reproducible`
- `governance_remediation_suggested_status`: `needs_manual_review`

After Phase 196–215:

- `final_readiness`: `needs_manual_governance_review`
- `stable_reproducibility`: `stable_reproducible`
- `governance_remediation_suggested_status`: `needs_manual_review`

Important interpretation:

- Stable reproducibility is closed.
- Final readiness is no longer blocked by reproducibility.
- Remaining work is manual governance review closure.
- This phase should turn the remaining governance manual-review state into a clear, auditable, research-only approval workflow.
- Approval must never authorize broker, live trading, paper execution, order generation, routing, position sizing, portfolio optimization, PnL optimization, or execution simulation.

## Phase 216–235 objective

Implement **Manual Governance Review Closure + Research-Only Approval Packet**.

Target outcome:

- Existing governance remediation status remains conservative but becomes reviewable.
- A human reviewer can explicitly approve the stack for **offline research only**.
- The system generates an approval packet and summary that says:
  - stable reproducibility is closed
  - governance was manually reviewed
  - execution boundaries remain forbidden
  - next allowed actions are offline research/reporting only
- Final state should become one of:
  - `research_stack_ready_for_manual_review`
  - `offline_research_approved`
  - `needs_manual_governance_review` if reviewer approval is absent or invalid
  - `blocked` only if true execution violations remain

Do not force approval. Approval must come from a decision file, not implicit logic.

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

# Part A — Governance review decision schema

Create:

- `cajas/reports/governance_review_decision.py`
- `cajas/scripts/build_governance_review_decision.py`

Input decision file should be JSON. Add an example:

- `cajas/data_examples/governance_review_decision_example.json`

Example:

```json
{
  "reviewer": "manual",
  "decision": "approve_offline_research_only",
  "scope": "offline_research_only",
  "notes": "Reviewed governance findings as boundary documentation and non-execution research tooling.",
  "accepted_findings": [
    {
      "category": "boundary_documentation",
      "reason": "Statements explicitly forbid execution behavior."
    }
  ],
  "rejected_capabilities": [
    "broker integration",
    "live trading",
    "paper trading execution",
    "order generation",
    "order routing",
    "position sizing",
    "portfolio optimization",
    "PnL optimization",
    "execution simulation"
  ],
  "required_next_controls": [
    "Keep execution boundaries visible in all readiness outputs.",
    "Require a separate future phase before any paper-trading design discussion."
  ]
}
```

Allowed decisions:

- `approve_offline_research_only`
- `needs_changes`
- `rejected`

The builder should read:

- governance remediation report
- final readiness packet
- stable reproducibility report
- optional reviewer decision file

Output:

- `governance_review_decision.json`
- `governance_review_decision.md`

Decision behavior:

- If input decision is absent, invalid, or not approval, status remains `needs_manual_governance_review`.
- If input decision approves offline research only and no true execution violations remain, status becomes `offline_research_governance_approved`.
- If true execution violations remain, status remains `blocked` even with approval.
- Rejected capabilities must always be present.

---

# Part B — Research-only approval packet

Create:

- `cajas/reports/research_only_approval_packet.py`
- `cajas/scripts/build_research_only_approval_packet.py`

Inputs:

- final readiness packet
- stable reproducibility report
- governance remediation report
- governance review decision
- offline review packet
- final research bundle

Output:

- `research_only_approval_packet.json`
- `research_only_approval_packet.md`

The approval packet should include:

- approval status:
  - `offline_research_approved`
  - `needs_manual_governance_review`
  - `needs_changes`
  - `rejected`
  - `blocked`
- stable reproducibility status
- governance review status
- final readiness status
- approved scope:
  - `offline_research_only`
- explicitly forbidden scope:
  - broker/live/paper execution
  - order generation/routing
  - position sizing
  - portfolio optimization
  - PnL optimization
  - execution simulation
- allowed next actions:
  - continue offline feature research
  - continue label/quality review
  - run bounded CPU-only experiments
  - improve reports
  - prepare future design docs
- forbidden next actions:
  - implement broker
  - implement paper trading execution
  - implement live data connection
  - implement order routing
  - optimize PnL
- reviewer notes and accepted findings
- audit trail of source artifacts

---

# Part C — Final readiness integration

Update:

- `cajas/reports/final_readiness_packet.py`
- `cajas/reports/final_readiness_summary.py`
- `cajas/reports/offline_review_packet.py`
- `cajas/reports/final_research_bundle.py`

Add optional support for:

```bash
--governance-review-decision tmp/governance-review-smoke/governance_review/governance_review_decision.json
--research-only-approval-packet tmp/governance-review-smoke/approval/research_only_approval_packet.json
```

Decision behavior:

- Stable reproducibility is `stable_reproducible`.
- Governance remediation is `needs_manual_review`.
- Valid offline-only governance approval exists.
- No true execution violations remain.
- Then final readiness may become:
  - `offline_research_approved`
  - or `research_stack_ready_for_manual_review`, depending existing enum compatibility.
- If existing enum does not support `offline_research_approved`, add it carefully with tests/docs.
- Do not remove blocked execution actions from any output.

---

# Part D — Governance review smoke runner

Create:

- `cajas/scripts/run_governance_review_closure_smoke.py`

It should orchestrate:

1. Run final reproducibility closure smoke or reuse equivalent outputs.
2. Build governance review decision from example decision file.
3. Build research-only approval packet.
4. Rebuild final readiness packet/summary with governance review evidence.
5. Rebuild offline review packet and final research bundle if supported.
6. Print top-level statuses.

Suggested command:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_governance_review_closure_smoke.py --out-root tmp/governance-review-smoke
```

Expected outputs:

- `tmp/governance-review-smoke/repro_closure`
- `tmp/governance-review-smoke/governance_review/governance_review_decision.json`
- `tmp/governance-review-smoke/governance_review/governance_review_decision.md`
- `tmp/governance-review-smoke/approval/research_only_approval_packet.json`
- `tmp/governance-review-smoke/approval/research_only_approval_packet.md`
- `tmp/governance-review-smoke/final/final_readiness_packet.json`
- `tmp/governance-review-smoke/final/final_readiness_summary.md`
- `tmp/governance-review-smoke/review/offline_review_packet.json`
- `tmp/governance-review-smoke/bundle/final_research_bundle.json`
- `tmp/governance-review-smoke/bundle/final_research_bundle.md`

---

# Part E — Tests

Add focused tests for all new/modified behavior.

Required coverage:

## Governance review decision

- valid offline-only approval produces `offline_research_governance_approved`
- missing decision keeps `needs_manual_governance_review`
- invalid decision is rejected
- approval cannot override true execution violations
- rejected capabilities are preserved

## Research-only approval packet

- valid governance approval produces `offline_research_approved`
- approved scope is exactly `offline_research_only`
- forbidden scope includes broker/live/paper/order/PnL capabilities
- allowed next actions are research-only
- source artifact audit trail is present

## Final readiness integration

- stable reproducible + governance review approval moves readiness to approved/manual-ready status
- true execution violation keeps readiness blocked
- no output removes blocked execution boundaries
- reviewer approval does not authorize trading execution

## Smoke

- governance review closure smoke creates expected files
- smoke reports top-level statuses
- smoke does not require GPU/CUDA/network

Keep tests deterministic and lightweight.

---

# Part F — Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`
- `cajas/data_examples/README.md`
- `tasks/phase_216_235_manual_governance_review_closure_prompt.md`

Add sections such as:

```markdown
## Manual Governance Review Closure

## Research-Only Approval Packet

## Offline Research Approval Scope
```

Document:

- How to run governance review closure smoke.
- How to write a governance review decision file.
- What `offline_research_approved` means.
- What it does not mean.
- Why execution boundaries remain forbidden.
- That any future paper-trading design requires a separate explicit phase.

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
./.venv-qlib313/bin/python cajas/scripts/run_governance_review_closure_smoke.py --out-root tmp/governance-review-smoke
```

If `.venv-qlib313` is unavailable, use the active project Python environment and report exact commands.

---

# Commit guidance

After validation passes, create local commits. Suggested split:

1. `feat: add governance review decision workflow`
2. `feat: add research-only approval packet`
3. `feat: integrate governance approval into final readiness`
4. `docs: document research-only approval workflow`

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
