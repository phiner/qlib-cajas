"""Conservative governance audit for forbidden execution capabilities."""

from __future__ import annotations

from pathlib import Path

PATTERNS = {
    "broker_integration": ["broker", "order routing", "order submission"],
    "live_trading": ["live trading", "paper trading execution", "execution engine"],
    "position_sizing": ["position sizing", "portfolio optimization"],
    "pnl_optimization": ["pnl optimization", "optimize pnl", "sharpe"],
    "network_calls": ["requests.get(", "http://", "https://"],
    "credentials": ["api_key", "secret", "token="],
    "gpu_cuda": ["cuda", "gpu"],
}
ALLOWLIST = ["no broker", "forbidden", "blocked", "no live", "research-only"]


def run_research_governance_audit(*, root: str | Path) -> dict:
    root_path = Path(root).expanduser().resolve()
    findings = []
    allowlisted = []

    for path in root_path.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".md", ".json", ".txt"}:
            continue
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(lines, start=1):
            lower = line.lower()
            for cat, pats in PATTERNS.items():
                if any(p in lower for p in pats):
                    item = {
                        "file": str(path),
                        "line": i,
                        "category": cat,
                        "severity": "warning" if path.suffix.lower() == ".md" else "error",
                        "snippet": line[:200],
                    }
                    if any(a in lower for a in ALLOWLIST):
                        allowlisted.append(item)
                    else:
                        findings.append(item)

    by_cat = {}
    for f in findings:
        by_cat[f["category"]] = by_cat.get(f["category"], 0) + 1

    status = "pass"
    if findings:
        status = "fail" if any(f["severity"] == "error" for f in findings) else "warn"

    return {
        "schema_version": "v1",
        "root": str(root_path),
        "status": status,
        "category_counts": by_cat,
        "findings": findings,
        "allowlisted_findings": allowlisted,
    }
