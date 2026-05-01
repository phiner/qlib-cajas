from __future__ import annotations

import unittest

from cajas.baseline.training_guard import (
    TrainingDisabledError,
    assert_baseline_training_allowed,
)


class TrainingGuardTests(unittest.TestCase):
    def test_config_disabled_raises(self) -> None:
        with self.assertRaises(TrainingDisabledError):
            assert_baseline_training_allowed(
                config_training_enabled=False,
                phase_policy_allows_training=True,
            )

    def test_phase_policy_disabled_raises(self) -> None:
        with self.assertRaises(TrainingDisabledError):
            assert_baseline_training_allowed(
                config_training_enabled=True,
                phase_policy_allows_training=False,
            )

    def test_both_disabled_raises(self) -> None:
        with self.assertRaises(TrainingDisabledError):
            assert_baseline_training_allowed(
                config_training_enabled=False,
                phase_policy_allows_training=False,
            )

    def test_both_enabled_allows(self) -> None:
        res = assert_baseline_training_allowed(
            config_training_enabled=True,
            phase_policy_allows_training=True,
        )
        self.assertTrue(res.allowed)


if __name__ == "__main__":
    unittest.main()
