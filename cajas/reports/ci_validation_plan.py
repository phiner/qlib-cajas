"""Build CI validation plan for research pipeline."""

from __future__ import annotations


def build_ci_validation_plan() -> dict:
    tiers = [
        {
            "tier": "Tier 0",
            "intent": "hygiene",
            "commands": [
                "./.venv-qlib313/bin/python -m compileall cajas",
                "./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py",
                "find cajas -path \"*/init.py\" -print",
                "git ls-files | grep -E '(^|/)init\\.py$' || true",
            ],
        },
        {
            "tier": "Tier 1",
            "intent": "fast local validation",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py",
            ],
        },
        {
            "tier": "Tier 2",
            "intent": "fast pytest only",
            "commands": [
                "./.venv-qlib313/bin/python -m pytest cajas/tests -m \"not smoke and not slow and not closure and not full\"",
            ],
        },
        {
            "tier": "Tier 3",
            "intent": "micro smoke",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier micro --out-root tmp/smoke-validation-micro",
            ],
        },
        {
            "tier": "Tier 4",
            "intent": "minimal smoke",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation-minimal",
            ],
        },
        {
            "tier": "Tier 5",
            "intent": "closure smoke (expensive)",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier closure --out-root tmp/smoke-validation-closure",
            ],
        },
        {
            "tier": "Tier 6",
            "intent": "full smoke (very expensive)",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier full --out-root tmp/smoke-validation-full",
            ],
        },
    ]
    return {"schema_version": "v1", "tiers": tiers}
