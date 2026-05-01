"""Hard guard preventing baseline training in disabled phases."""

from __future__ import annotations

from dataclasses import asdict, dataclass


class TrainingDisabledError(RuntimeError):
    """Raised when baseline training is not allowed by config/policy."""


@dataclass(frozen=True)
class TrainingGuardResult:
    allowed: bool
    reason: str
    config_training_enabled: bool
    phase_policy_allows_training: bool

    def to_dict(self) -> dict:
        return asdict(self)


def assert_baseline_training_allowed(
    *,
    config_training_enabled: bool,
    phase_policy_allows_training: bool = False,
) -> TrainingGuardResult:
    if not config_training_enabled:
        raise TrainingDisabledError("Training disabled by configuration (training.enabled=false).")
    if not phase_policy_allows_training:
        raise TrainingDisabledError("Training disabled by phase policy.")
    return TrainingGuardResult(
        allowed=True,
        reason="Training allowed by config and phase policy.",
        config_training_enabled=config_training_enabled,
        phase_policy_allows_training=phase_policy_allows_training,
    )
