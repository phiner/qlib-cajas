# Future Work Checklist

## Immediate Next Work

- Keep fast validation consistently under 90s.
- Convert additional CLI artifact tests to in-process `main()` if runtime regresses.
- Monitor `reads_full_csv_likely_count` and keep it stable.
- Keep real-data access explicit and policy-guarded.
- Keep dataset quality modular CLIs and smoke runner stable:
  - `cajas/scripts/build_dataset_quality_report.py`
  - `cajas/scripts/build_label_coverage_diagnostics.py`
  - `cajas/scripts/build_time_coverage_diagnostics.py`
  - `cajas/scripts/run_chunked_feature_dry_run.py`
  - `cajas/scripts/build_feature_schema_manifest.py`
  - `cajas/scripts/build_offline_research_queue_summary.py`
  - `cajas/scripts/run_dataset_quality_smoke.py`

## Data I/O Future Work

- Optional parquet/arrow cache path when dependency policy allows it.
- Chunked feature extraction for multi-GB CSV workflows.
- Manifest-based incremental processing.
- Cache invalidation and stale-index tests.

## Research Future Work

- Offline-only experiment comparison expansions.
- Manual governance review refresh flow.
- Research-only approval packet refresh cadence.
- Keep trading execution out of scope unless designed in a separate branch/spec.
- Prioritize dataset quality loop + chunked feature readiness as the immediate post-merge workstream:
  - see `cajas/docs/post_merge_next_workstream_plan.md`
  - execution prompt: `tasks/prompts/001_eurusd_gui_sample_index_state_fix.md`

## Hard Blockers Before Paper/Live Work

- No broker code.
- No order generation or routing.
- No position sizing.
- No PnL optimization.
- No execution simulation.
- No live data connection.
