# Phase 66–75 Prompt: Qlib Adapter Contract + Dry-Run Research Promotion Boundary

You are continuing the `cajas/market-recognition-phase-0` branch.

The previous Phase 56–65 work is complete and committed locally. It added a research decision packet workflow, candidate promotion manifest, research report index, and an end-to-end research packet smoke runner. Full tests passed (`183 passed`), path hygiene passed, and git status was clean.

## Core goal

Implement Phase 66–75 as a conservative **Qlib adapter contract and dry-run promotion boundary**.

This phase must make it possible to take a promoted research candidate and produce a Qlib-facing integration packet without touching Qlib core, without training live strategies, and without changing trading execution logic.

The output should be a stable research-to-Qlib handoff layer:

1. Define a strict adapter contract schema.
2. Validate candidate promotion manifests against the adapter contract.
3. Build a dry-run Qlib integration packet.
4. Add compatibility and completeness reports.
5. Add a bounded smoke command that exercises the full path from existing research outputs to adapter packet.

## Hard scope boundaries

Do **not**:

- Modify Qlib core code.
- Add live trading logic.
- Add broker/execution logic.
- Add real strategy deployment.
- Add online inference services.
- Rewrite existing Phase 41–65 workflows.
- Change existing CLI behavior incompatibly.
- Add heavy dependencies unless already present in the project.

This phase is about contracts, validation, dry-run artifacts, reports, and tests only.

## Expected additions

### 1. Qlib adapter contract schema

Add:

- `cajas/reports/qlib_adapter_contract.py`
- tests, for example:
  - `cajas/tests/test_qlib_adapter_contract.py`

The module should define small dataclass-style structures or plain dictionaries for a Qlib adapter contract.

The contract should include at least:

- `contract_version`
- `candidate_id`
- `research_run_id`
- `dataset_version`
- `feature_set_id`
- `label_variant_id`
- `target_name`
- `prediction_horizon`
- `instrument_universe`
- `frequency`
- `required_feature_columns`
- `required_label_columns`
- `artifact_paths`
- `known_limitations`
- `promotion_status`
- `created_at_utc`

Add validation helpers that return structured issues rather than raising for normal validation failures.

Issue fields should be stable and testable, for example:

- `severity`: `error` / `warning`
- `code`
- `message`
- optional `field`

### 2. Adapter contract builder

Add:

- `cajas/reports/qlib_adapter_contract_builder.py`
- tests, for example:
  - `cajas/tests/test_qlib_adapter_contract_builder.py`

The builder should construct a contract from existing research/promotion inputs.

It should accept promotion manifest style inputs from Phase 56–65 and a small config/dict describing Qlib-facing assumptions.

It should not assume all real files exist unless explicitly requested. Provide a validation mode where missing optional artifacts are warnings and missing required artifacts are errors.

### 3. CLI: build adapter contract

Add:

- `cajas/scripts/build_qlib_adapter_contract.py`
- CLI tests, for example:
  - `cajas/tests/test_build_qlib_adapter_contract_cli.py`

The CLI should accept arguments similar to:

```bash
python cajas/scripts/build_qlib_adapter_contract.py \
  --promotion-manifest <path> \
  --out <path> \
  --candidate-id <id> \
  --feature-set-id <id> \
  --label-variant-id <id> \
  --target-name <name> \
  --frequency <freq>
```

Use actual current project CLI conventions if these exact flags conflict with the codebase.

The CLI should write:

- a JSON contract file
- optionally a validation summary JSON next to it, or embedded validation section

### 4. Dry-run Qlib integration packet

Add:

- `cajas/reports/qlib_integration_packet.py`
- `cajas/scripts/build_qlib_integration_packet.py`
- tests:
  - `cajas/tests/test_qlib_integration_packet.py`
  - `cajas/tests/test_build_qlib_integration_packet_cli.py`

The integration packet should be a dry-run handoff bundle describing what would be needed to integrate the candidate into Qlib.

It should include at least:

- adapter contract summary
- required datasets
- required feature columns
- required labels/targets
- expected prediction output shape
- evaluation artifacts
- readiness decision
- blocking issues
- non-blocking warnings
- next manual steps

The packet may be JSON and/or Markdown. Prefer JSON plus a short Markdown summary if simple.

### 5. Compatibility report

Add:

- `cajas/reports/qlib_compatibility_report.py`
- `cajas/scripts/build_qlib_compatibility_report.py`
- tests:
  - `cajas/tests/test_qlib_compatibility_report.py`
  - `cajas/tests/test_build_qlib_compatibility_report_cli.py`

The report should check whether a candidate appears compatible with the current project’s Qlib research boundary.

Checks should include:

- required identifiers present
- feature set present
- label variant present
- dataset metadata present
- target metadata present
- promotion status acceptable
- no blocking leakage/drift issue recorded if such input is available
- no missing required artifact path when strict mode is requested

Keep checks deterministic and lightweight.

### 6. End-to-end adapter smoke runner

Add:

- `cajas/scripts/run_qlib_adapter_smoke.py`
- test:
  - `cajas/tests/test_run_qlib_adapter_smoke.py`

The smoke runner should build minimal deterministic fixture inputs under an output root and then run:

1. adapter contract generation
2. integration packet generation
3. compatibility report generation

It should print the main output paths and exit non-zero on blocking failures.

Example:

```bash
python cajas/scripts/run_qlib_adapter_smoke.py --out-root tmp/qlib-adapter-smoke
```

### 7. Documentation updates

Update:

- `cajas/README.md`
- `cajas/docs/qlib_integration_notes.md`

Add a section explaining:

- research decision packet vs adapter contract vs dry-run integration packet
- what this phase does not do
- example commands
- expected output files
- how a human should read blocking vs warning issues

### 8. Exports

Update exports if the package uses them:

- `cajas/reports/__init__.py`

Avoid creating any `init.py` typo files. Existing hygiene checks must remain clean.

## Validation requirements

Run all of the following before committing:

```bash
./.venv-qlib313/bin/python -m compileall cajas
./.venv-qlib313/bin/python -m pytest cajas/tests
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
find cajas -path "*/init.py" -print
git ls-files | grep -E '(^|/)init\.py$' || true
./.venv-qlib313/bin/python cajas/scripts/run_qlib_adapter_smoke.py --out-root tmp/qlib-adapter-smoke
```

If the virtualenv path differs, use the active project Python, but report the exact command used.

## Commit guidance

Create local commits only. Do not push.

Suggested split:

1. `feat: add qlib adapter contract workflow`
2. `feat: add qlib dry-run integration packet reports`
3. `docs: document qlib adapter handoff workflow`

At the end, report:

- files changed
- validation commands and results
- smoke output paths
- local commit hashes
- final `git status --short`
- manual push command:

```bash
git push origin cajas/market-recognition-phase-0
```

## Acceptance criteria

- Full test suite passes.
- Path hygiene passes.
- Adapter smoke passes.
- No Qlib core changes.
- No live trading or broker logic added.
- All new artifacts are deterministic and lightweight.
- Git status is clean after local commits.
