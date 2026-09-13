"""
Characterization Unit Tests: Recovery Stabilization & Cooldown Arbiter
Author: parikesitad-pm
© 2026
"""

import time
import unittest
from desktop.core.recovery.arbiter import RecoveryArbiter


class TestRecoveryArbiter(unittest.TestCase):
    def test_cooldown_enforcement(self):
        """Newly restored link must observe cooldown before marked stabilized."""
        arbiter = RecoveryArbiter(default_cooldown_sec=0.2)
        arbiter.notify_carrier_restored("eth0")

        # Immediately after restore -> not stabilized
        self.assertFalse(arbiter.is_stabilized("eth0"))
        self.assertGreater(arbiter.get_remaining_cooldown("eth0"), 0.0)

        # Wait for cooldown duration
        time.sleep(0.25)
        self.assertTrue(arbiter.is_stabilized("eth0"))
        self.assertEqual(arbiter.get_remaining_cooldown("eth0"), 0.0)

    def test_carrier_loss_resets_cooldown(self):
        """If carrier drops during cooldown, recovery resets."""
        arbiter = RecoveryArbiter(default_cooldown_sec=0.5)
        arbiter.notify_carrier_restored("eth0")
        time.sleep(0.1)

        # Cable pulled again
        arbiter.notify_carrier_lost("eth0")
        self.assertTrue(arbiter.is_stabilized("eth0"))  # Not in recovery tracking anymore

        # Cable restored again -> new timer starts
        arbiter.notify_carrier_restored("eth0")
        self.assertFalse(arbiter.is_stabilized("eth0"))


if __name__ == "__main__":
    unittest.main()
