"""Build CI validation plan for research pipeline."""

from __future__ import annotations


def build_ci_validation_plan() -> dict:
    tiers = [
        {
            "tier": "Tier 0",
            "intent": "path hygiene and compilation",
            "commands": [
                "./.venv-qlib313/bin/python -m compileall cajas",
                "./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py",
                "find cajas -path \"*/init.py\" -print",
                "git ls-files | grep -E '(^|/)init\\.py$' || true",
            ],
        },
        {
            "tier": "Tier 1",
            "intent": "fast unit validation",
            "commands": [
                "./.venv-qlib313/bin/python -m pytest cajas/tests -m \"not slow and not smoke\"",
            ],
        },
        {
            "tier": "Tier 2",
            "intent": "full suite",
            "commands": ["./.venv-qlib313/bin/python -m pytest cajas/tests"],
        },
        {
            "tier": "Tier 3",
            "intent": "explicit smoke validation",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier minimal --out-root tmp/smoke-validation",
            ],
        },
        {
            "tier": "Tier 4",
            "intent": "full historical smoke (optional)",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_smoke_validation.py --tier full --out-root tmp/smoke-validation",
            ],
        },
    ]
    return {"schema_version": "v1", "tiers": tiers}
