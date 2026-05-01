"""Build index files for generated research artifacts."""

from __future__ import annotations

from pathlib import Path


CATEGORY_RULES = {
    "labels": ["label", "threshold"],
    "features": ["feature", "kline"],
    "training": ["train", "model", "metrics", "prediction"],
    "comparison": ["comparison", "benchmark"],
    "calibration": ["calibration"],
    "stability": ["stability", "seed"],
    "validation": ["validation", "plan"],
    "errors": ["error_slice", "confusion"],
    "leakage_drift": ["leakage", "drift"],
    "readiness": ["readiness"],
    "decision": ["decision"],
    "promotion": ["promotion", "manifest"],
}


def _detect_category(name: str) -> str:
    lowered = name.lower()
    for category, keys in CATEGORY_RULES.items():
        if any(k in lowered for k in keys):
            return category
    return "other"


def build_research_report_index(*, root_dir: str | Path) -> dict:
    root = Path(root_dir).expanduser().resolve()
    grouped: dict[str, list[str]] = {k: [] for k in CATEGORY_RULES}
    grouped["other"] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        grouped[_detect_category(path.name)].append(rel)
    for key in grouped:
        grouped[key] = sorted(grouped[key])
    return {"root_dir": str(root), "groups": grouped, "total_files": sum(len(v) for v in grouped.values())}

