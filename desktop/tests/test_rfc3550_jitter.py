"""
Characterization Unit Tests: RFC 3550 Statistical Jitter
Author: parikesitad-pm
© 2026
"""

import unittest
from desktop.core.probe.rfc3550 import RFC3550JitterTracker


class TestRFC3550Jitter(unittest.TestCase):
    def test_rfc3550_smoothing_formula(self):
        """
        D(i-1, i) = (R_i - S_i) - (R_{i-1} - S_{i-1})
        J(i) = J(i-1) + (|D| - J(i-1)) / 16
        """
        tracker = RFC3550JitterTracker()

        # Packet 1: Send at t=0.000, Recv at t=0.020 (transit = 20ms)
        j1 = tracker.update(0.000, 0.020)
        self.assertEqual(j1, 0.0)

        # Packet 2: Send at t=0.100, Recv at t=0.136 (transit = 36ms, D = 16ms)
        # J = 0 + (16 - 0) / 16 = 1.0ms
        j2 = tracker.update(0.100, 0.136)
        self.assertAlmostEqual(j2, 1.0, places=4)

        # Packet 3: Send at t=0.200, Recv at t=0.220 (transit = 20ms, D = 16ms)
        # J = 1.0 + (16 - 1.0) / 16 = 1.0 + 0.9375 = 1.9375ms
        j3 = tracker.update(0.200, 0.220)
        self.assertAlmostEqual(j3, 1.9375, places=4)

    def test_zero_jitter_on_constant_delay(self):
        """Constant network transit should converge jitter towards 0."""
        tracker = RFC3550JitterTracker()
        for i in range(25):
            tracker.update(i * 0.1, i * 0.1 + 0.015)  # constant 15ms
        self.assertAlmostEqual(tracker.jitter_ms, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
