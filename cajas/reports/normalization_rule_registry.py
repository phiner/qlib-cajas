"""Central normalization rule registry for reproducibility tooling."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class NormalizationRule:
    rule_id: str
    description: str
    target_pattern: str
    risk_level: str
    enabled_by_default: bool
    examples: list[str]


def get_normalization_rules() -> list[NormalizationRule]:
    return [
        NormalizationRule(
            rule_id="replace_timestamp_strings",
            description="Replace timestamp-like values in strings and known timestamp fields.",
            target_pattern="timestamp-like scalar values",
            risk_level="low",
            enabled_by_default=True,
            examples=["2026-05-01T12:00:00Z -> <TS>"],
        ),
        NormalizationRule(
            rule_id="replace_tmp_paths",
            description="Replace temporary directory roots in paths.",
            target_pattern="/tmp/... style absolute paths",
            risk_level="low",
            enabled_by_default=True,
            examples=["/tmp/research-quality-loop-smoke/run_a -> <TMP_ROOT>"],
        ),
        NormalizationRule(
            rule_id="replace_cwd_paths",
            description="Replace current working directory prefixes.",
            target_pattern="absolute paths rooted at cwd",
            risk_level="low",
            enabled_by_default=True,
            examples=["/home/user/repo/... -> <CWD>/..."],
        ),
        NormalizationRule(
            rule_id="replace_run_labels",
            description="Replace generated run labels used only for output folders.",
            target_pattern="run_a/run_b style generated roots",
            risk_level="low",
            enabled_by_default=True,
            examples=["run_a -> <RUN_ROOT>", "run_b -> <RUN_ROOT>"],
        ),
        NormalizationRule(
            rule_id="replace_known_variable_fields",
            description="Replace clearly variable metadata fields (root, working_directory, absolute_path).",
            target_pattern="specific metadata field names",
            risk_level="medium",
            enabled_by_default=True,
            examples=["working_directory: /x -> <VAR>"],
        ),
    ]


def get_normalization_rule_registry() -> dict:
    rules = [asdict(rule) for rule in get_normalization_rules()]
    return {
        "schema_version": "v1",
        "rules": rules,
    }

