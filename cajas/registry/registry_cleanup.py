"""Classify registry records and write optional filtered registry copy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from cajas.registry.run_registry import read_run_registry


@dataclass(frozen=True)
class RegistryRecordClassification:
    run_name: str
    run_id: str | None
    output_dir: str | None
    classification: str
    reason: str
    keep_by_default: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RegistryCleanupReport:
    registry_path: str
    total_records: int
    active_records: int
    stale_records: int
    missing_artifact_records: int
    temp_test_records: int
    classifications: list[RegistryRecordClassification]
    recommendations: list[str]

    def to_dict(self) -> dict:
        return {
            "registry_path": self.registry_path,
            "total_records": self.total_records,
            "active_records": self.active_records,
            "stale_records": self.stale_records,
            "missing_artifact_records": self.missing_artifact_records,
            "temp_test_records": self.temp_test_records,
            "classifications": [c.to_dict() for c in self.classifications],
            "recommendations": self.recommendations,
        }


def _classify_record(row: dict) -> RegistryRecordClassification:
    run_name = str(row.get("run_name", ""))
    run_id = row.get("run_id")
    out_dir = row.get("output_dir")
    out = Path(str(out_dir)).expanduser() if out_dir else None

    if out is None or str(out_dir).strip() == "":
        return RegistryRecordClassification(run_name, run_id, None, "unknown", "missing output_dir", False)

    out_str = str(out)
    if out.exists():
        req = ["run_manifest.json", "training_config.json"]
        present = sum(1 for x in req if (out / x).exists())
        if present >= 1:
            return RegistryRecordClassification(run_name, run_id, out_str, "active", "artifact directory exists", True)
        return RegistryRecordClassification(run_name, run_id, out_str, "missing_artifact", "directory exists but required artifacts missing", False)

    if out_str.startswith("/tmp/tmp"):
        return RegistryRecordClassification(run_name, run_id, out_str, "temp_test", "temporary pytest path", False)

    if out_str.startswith("/home/"):
        return RegistryRecordClassification(run_name, run_id, out_str, "stale", "local path missing", False)
    return RegistryRecordClassification(run_name, run_id, out_str, "missing_artifact", "artifact directory missing", False)


def classify_run_registry_records(*, registry_path: str | Path) -> RegistryCleanupReport:
    path = Path(registry_path).expanduser().resolve()
    if not path.exists():
        return RegistryCleanupReport(str(path), 0, 0, 0, 0, 0, [], ["Registry file does not exist."])

    rows = read_run_registry(path)
    classes = [_classify_record(row) for row in rows]

    active = sum(1 for c in classes if c.classification == "active")
    stale = sum(1 for c in classes if c.classification == "stale")
    missing = sum(1 for c in classes if c.classification == "missing_artifact")
    temp = sum(1 for c in classes if c.classification == "temp_test")

    recs = []
    if temp > 0:
        recs.append("Consider exporting filtered registry copy excluding temp_test records.")
    if missing + stale > 0:
        recs.append("Investigate stale/missing artifact records and archive if obsolete.")

    return RegistryCleanupReport(
        registry_path=str(path),
        total_records=len(rows),
        active_records=active,
        stale_records=stale,
        missing_artifact_records=missing,
        temp_test_records=temp,
        classifications=classes,
        recommendations=recs,
    )


def write_filtered_registry_copy(
    *,
    registry_path: str | Path,
    output_path: str | Path,
    exclude_temp_test: bool = True,
) -> dict:
    path = Path(registry_path).expanduser().resolve()
    rows = read_run_registry(path)

    kept: list[dict] = []
    removed = 0
    for row in rows:
        c = _classify_record(row)
        if exclude_temp_test and c.classification == "temp_test":
            removed += 1
            continue
        kept.append(row)

    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")

    return {"output_path": str(out), "written": len(kept), "removed": removed}
