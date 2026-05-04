# Phase 56–65 Prompt: Qlib Research Decision Layer + Conservative Integration Cleanup

You are continuing work on branch:

```bash
cajas/market-recognition-phase-0
```

Previous state:

- Phase 41–45 completed and committed:
  - label variant generation
  - holdout training
  - label variant comparison
  - label decision report
- Phase 46–55 completed and committed:
  - kline structure features
  - feature set registry/comparison
  - calibration analysis
  - seed stability
  - rolling-year validation planning
  - error slice analysis
  - leakage/drift audit
  - Qlib readiness and research roadmap reports
- Full validation passed:
  - `python -m compileall cajas`
  - `python -m pytest cajas/tests` → 174 passed
  - path hygiene pass
  - no `init.py` typo files
- Git status was clean after local commits.

Do **not** change Qlib core.
Do **not** add trading execution logic.
Do **not** claim profitability.
Do **not** change existing script contracts unless tests/docs are updated.
This phase should remain a research/diagnostic layer.

---

## Goal

Add a conservative **research decision layer** that combines the existing Phase 41–55 artifacts into a reproducible decision/audit workflow:

1. choose candidate label variant(s),
2. choose candidate feature set(s),
3. inspect calibration and seed stability,
4. inspect error slices and leakage/drift findings,
5. produce a final research decision packet that says whether the current setup is:
   - `reject`,
   - `needs_more_data`,
   - `needs_label_redesign`,
   - `needs_feature_redesign`,
   - `candidate_for_qlib_trial`.

This is **not** a trading decision. It is a research readiness decision.

---

## Phase 56 — Research Decision Schema

Add:

```text
cajas/reports/research_decision_schema.py
```

Implement small dataclass-style structures or plain typed helpers for:

- `ResearchDecisionInput`
- `ResearchDecisionFinding`
- `ResearchDecisionRecommendation`
- `ResearchDecisionResult`

The result should support JSON serialization.

Minimum fields:

```text
run_id
created_at_utc
label_variant_summary_path
feature_set_summary_path
calibration_summary_path
seed_stability_summary_path
rolling_validation_plan_path
error_slice_summary_path
leakage_drift_audit_path
qlib_readiness_report_path
final_decision
confidence_level
blocking_findings
non_blocking_findings
recommended_next_actions
notes
```

Decision values:

```text
reject
needs_more_data
needs_label_redesign
needs_feature_redesign
candidate_for_qlib_trial
```

Confidence values:

```text
low
medium
high
```

Tests:

```text
cajas/tests/test_research_decision_schema.py
```

---

## Phase 57 — Research Decision Builder

Add:

```text
cajas/reports/research_decision_builder.py
```

It should read available report artifacts from a run/report directory and produce a structured decision JSON.

Input should be resilient:

- missing optional files should become warnings, not crashes;
- missing core files should create blocking findings;
- malformed JSON/CSV should create blocking findings with clear messages.

The builder should use conservative rules only.

Suggested rules:

- If leakage/drift audit has severe leakage findings → `reject` or `needs_feature_redesign`.
- If label distribution is too sparse or heavily dominated → `needs_more_data` or `needs_label_redesign`.
- If seed stability varies materially → `needs_more_data` or `needs_feature_redesign`.
- If calibration is poor but other metrics are acceptable → `needs_feature_redesign`.
- If Qlib readiness report says key artifacts are missing → not `candidate_for_qlib_trial`.
- Only return `candidate_for_qlib_trial` when no blocking findings exist and required summaries are present.

Keep thresholds configurable via function args or a small config object, but provide safe defaults.

Tests:

```text
cajas/tests/test_research_decision_builder.py
```

Use tiny temp JSON/CSV fixtures.

---

## Phase 58 — CLI: build_research_decision_packet.py

Add CLI:

```text
cajas/scripts/build_research_decision_packet.py
```

Required behavior:

```bash
python cajas/scripts/build_research_decision_packet.py \
  --reports-dir <DIR> \
  --out-dir <DIR>
```

Optional args:

```text
--run-id <ID>
--notes <TEXT>
--strict
```

Outputs:

```text
research_decision_packet.json
research_decision_packet.md
research_decision_findings.csv
research_decision_recommendations.csv
```

Markdown report should include:

- final decision
- confidence level
- required artifact checklist
- blocking findings
- non-blocking findings
- recommended next actions
- source artifact paths

Tests:

```text
cajas/tests/test_build_research_decision_packet_cli.py
```

---

## Phase 59 — Candidate Promotion Manifest

Add:

```text
cajas/reports/candidate_promotion_manifest.py
```

Purpose:

When the decision is `candidate_for_qlib_trial`, create a manifest describing exactly what is being promoted for a future Qlib trial.

This is still not a trading deployment.

Manifest fields:

```text
promotion_id
created_at_utc
decision_packet_path
label_variant_id
feature_set_id
target_name
horizon
model_family
train_period
holdout_period
known_limitations
required_rechecks
status
```

Allowed statuses:

```text
draft
blocked
candidate_for_manual_review
```

If the decision is not `candidate_for_qlib_trial`, manifest status should be `blocked`.

Tests:

```text
cajas/tests/test_candidate_promotion_manifest.py
```

---

## Phase 60 — CLI: build_candidate_promotion_manifest.py

Add CLI:

```text
cajas/scripts/build_candidate_promotion_manifest.py
```

Usage:

```bash
python cajas/scripts/build_candidate_promotion_manifest.py \
  --decision-packet <PATH> \
  --out-dir <DIR> \
  --label-variant-id <ID> \
  --feature-set-id <ID> \
  --target-name <NAME> \
  --horizon <N> \
  --model-family <NAME>
```

Outputs:

```text
candidate_promotion_manifest.json
candidate_promotion_manifest.md
```

Tests:

```text
cajas/tests/test_build_candidate_promotion_manifest_cli.py
```

---

## Phase 61 — Report Index Builder

Add:

```text
cajas/reports/research_report_index.py
```

Purpose:

Build a single index file for all generated research artifacts in an output directory.

CLI:

```text
cajas/scripts/build_research_report_index.py
```

Usage:

```bash
python cajas/scripts/build_research_report_index.py \
  --root-dir <DIR> \
  --out-dir <DIR>
```

Outputs:

```text
research_report_index.json
research_report_index.md
```

Index should group files by category:

```text
labels
features
training
comparison
calibration
stability
validation
errors
leakage_drift
readiness
decision
promotion
other
```

Tests:

```text
cajas/tests/test_research_report_index.py
cajas/tests/test_build_research_report_index_cli.py
```

---

## Phase 62 — End-to-End Research Packet Smoke Script

Add:

```text
cajas/scripts/run_research_packet_smoke.py
```

This should be a lightweight smoke orchestrator over existing scripts and tiny example data.

It should:

1. create a temp output root unless `--out-root` is supplied,
2. run or simulate minimal report artifacts from existing components,
3. build the research decision packet,
4. build the candidate promotion manifest,
5. build the report index,
6. print generated paths.

Usage:

```bash
python cajas/scripts/run_research_packet_smoke.py --out-root tmp/research-packet-smoke
```

Keep it bounded and fast.
Avoid heavy model training by default.
If needed, use small synthetic fixtures.

Tests:

```text
cajas/tests/test_run_research_packet_smoke.py
```

---

## Phase 63 — README / Docs Update

Update:

```text
cajas/README.md
cajas/docs/qlib_integration_notes.md
```

Add a short section:

```text
Research Decision Packet Workflow
```

Document commands:

```bash
python cajas/scripts/build_research_decision_packet.py --reports-dir ... --out-dir ...
python cajas/scripts/build_candidate_promotion_manifest.py --decision-packet ... --out-dir ...
python cajas/scripts/build_research_report_index.py --root-dir ... --out-dir ...
python cajas/scripts/run_research_packet_smoke.py --out-root tmp/research-packet-smoke
```

Clearly state:

- this is research readiness only;
- it does not trade;
- it does not modify Qlib core;
- promotion manifest means candidate for manual review, not production deployment.

---

## Phase 64 — Exports and Package Hygiene

Update relevant `__init__.py` exports only where they already exist.

Check:

```bash
find cajas -path "*/init.py" -print
```

Must produce no output.

Run path hygiene:

```bash
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

Must pass.

---

## Phase 65 — Validation and Commit

Run:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git status --short
```

Also run the new smoke:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_research_packet_smoke.py \
  --out-root tmp/research-packet-smoke
```

Create local commits. Suggested split:

1. schema/builder/report decision code + tests
2. candidate promotion + index code + tests
3. smoke script + docs

Do not push.

Final response should include:

- validation results,
- smoke output paths,
- commit hashes,
- final `git status --short`,
- manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```
