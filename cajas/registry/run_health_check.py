"""Health checks for local run registry and run artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from cajas.registry.run_registry import read_run_registry


TRADING_KEYS = {"profit", "return", "sharpe", "drawdown", "pnl", "win_rate", "expectancy"}


@dataclass(frozen=True)
class RunHealthIssue:
    severity: str
    code: str
    message: str
    run_name: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RunHealthReport:
    registry_path: str
    total_records: int
    checked_runs: int
    healthy_runs: int
    warning_count: int
    error_count: int
    issues: list[RunHealthIssue]

    def to_dict(self) -> dict:
        return {
            "registry_path": self.registry_path,
            "total_records": self.total_records,
            "checked_runs": self.checked_runs,
            "healthy_runs": self.healthy_runs,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "issues": [i.to_dict() for i in self.issues],
        }


def _scan_for_trading_keys(payload) -> list[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for k, v in payload.items():
            lk = str(k).lower()
            if lk in TRADING_KEYS:
                found.add(lk)
            found.update(_scan_for_trading_keys(v))
    elif isinstance(payload, list):
        for x in payload:
            found.update(_scan_for_trading_keys(x))
    return sorted(found)


def check_run_registry_health(*, registry_path: str | Path) -> RunHealthReport:
    reg = Path(registry_path).expanduser().resolve()
    issues: list[RunHealthIssue] = []

    if not reg.exists():
        issues.append(RunHealthIssue("warning", "registry_missing", "Registry file does not exist."))
        return RunHealthReport(str(reg), 0, 0, 0, 1, 0, issues)

    rows = read_run_registry(reg)
    checked = 0
    healthy = 0

    for row in rows:
        checked += 1
        run_name = str(row.get("run_name", "")) or None
        out_dir = Path(str(row.get("output_dir", ""))).expanduser()
        run_ok = True

        if not out_dir.exists():
            issues.append(RunHealthIssue("error", "artifact_dir_missing", f"Artifact directory missing: {out_dir}", run_name))
            run_ok = False
        else:
            for req in ["model_metadata.json", "metrics_test.json", "metrics_valid.json", "run_manifest.json"]:
                if not (out_dir / req).exists() and bool(row.get("training_executed", False)):
                    issues.append(RunHealthIssue("error", "required_artifact_missing", f"Missing required artifact: {req}", run_name))
                    run_ok = False

            metrics_path = out_dir / "metrics_test.json"
            if metrics_path.exists():
                try:
                    mt = json.loads(metrics_path.read_text(encoding="utf-8"))
                    for key in ("accuracy", "macro_f1", "weighted_f1"):
                        value = mt.get(key)
                        if value is not None and not (0.0 <= float(value) <= 1.0):
                            issues.append(RunHealthIssue("warning", "metric_out_of_range", f"{key} out of [0,1]: {value}", run_name))
                    bad_keys = _scan_for_trading_keys(mt)
                    if bad_keys:
                        issues.append(RunHealthIssue("error", "trading_metric_key_present", f"Trading metric keys found: {', '.join(bad_keys)}", run_name))
                        run_ok = False
                except Exception as exc:  # noqa: BLE001
                    issues.append(RunHealthIssue("error", "metrics_parse_failed", f"Failed to parse metrics_test.json: {exc}", run_name))
                    run_ok = False

        if run_ok:
            healthy += 1

    warning_count = sum(1 for i in issues if i.severity == "warning")
    error_count = sum(1 for i in issues if i.severity == "error")
    return RunHealthReport(str(reg), len(rows), checked, healthy, warning_count, error_count, issues)
