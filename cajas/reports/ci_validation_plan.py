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
            "intent": "focused unit tests",
            "commands": [
                "./.venv-qlib313/bin/python -m pytest cajas/tests/test_run_research_gate_smoke.py",
                "./.venv-qlib313/bin/python -m pytest cajas/tests/test_run_final_readiness_smoke.py",
            ],
        },
        {
            "tier": "Tier 2",
            "intent": "full suite",
            "commands": ["./.venv-qlib313/bin/python -m pytest cajas/tests"],
        },
        {
            "tier": "Tier 3",
            "intent": "bounded smoke flows",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_research_gate_smoke.py --out-root tmp/research-gate-smoke",
                "./.venv-qlib313/bin/python cajas/scripts/run_final_readiness_smoke.py --out-root tmp/final-readiness-smoke",
            ],
        },
        {
            "tier": "Tier 4",
            "intent": "optional heavier research runs",
            "commands": [
                "./.venv-qlib313/bin/python cajas/scripts/run_qlib_model_bridge_smoke.py --out-root tmp/qlib-model-bridge-smoke",
            ],
        },
    ]
    return {"schema_version": "v1", "tiers": tiers}
