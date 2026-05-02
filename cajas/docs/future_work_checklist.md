# Future Work Checklist

## Immediate Next Work

- Keep fast validation consistently under 90s.
- Convert additional CLI artifact tests to in-process `main()` if runtime regresses.
- Monitor `reads_full_csv_likely_count` and keep it stable.
- Keep real-data access explicit and policy-guarded.

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

## Hard Blockers Before Paper/Live Work

- No broker code.
- No order generation or routing.
- No position sizing.
- No PnL optimization.
- No execution simulation.
- No live data connection.
