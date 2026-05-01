"""Build summary reports from the local run registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from cajas.registry.run_registry import read_run_registry


@dataclass(frozen=True)
class RunRegistrySummaryReport:
    registry_path: str
    total_records: int
    run_types: dict[str, int]
    statuses: dict[str, int]
    training_runs: list[dict]
    artifact_dirs: list[str]
    warnings: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def build_run_registry_summary(*, registry_path: str | Path) -> RunRegistrySummaryReport:
    path = Path(registry_path).expanduser().resolve()
    if not path.exists():
        return RunRegistrySummaryReport(
            registry_path=str(path),
            total_records=0,
            run_types={},
            statuses={},
            training_runs=[],
            artifact_dirs=[],
            warnings=["Registry file not found."],
        )

    rows = read_run_registry(path)
    run_types: dict[str, int] = {}
    statuses: dict[str, int] = {}
    training_runs: list[dict] = []
    artifact_dirs: list[str] = []

    for row in rows:
        run_type = str(row.get("run_type", "unknown"))
        status = str(row.get("status", "unknown"))
        run_types[run_type] = run_types.get(run_type, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1
        out = str(row.get("output_dir", ""))
        if out:
            artifact_dirs.append(out)
        if bool(row.get("training_executed", False)):
            training_runs.append(
                {
                    "run_id": row.get("run_id"),
                    "run_name": row.get("run_name"),
                    "run_type": run_type,
                    "status": status,
                    "output_dir": out,
                }
            )

    return RunRegistrySummaryReport(
        registry_path=str(path),
        total_records=len(rows),
        run_types=run_types,
        statuses=statuses,
        training_runs=training_runs,
        artifact_dirs=sorted(set(artifact_dirs)),
        warnings=[],
    )
