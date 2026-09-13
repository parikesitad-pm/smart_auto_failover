"""
Characterization Unit Tests: Health Scoring & Transition Boundaries
Author: parikesitad-pm
© 2026
"""

import unittest
from desktop.models.interface import InterfaceState
from desktop.models.metrics import PathMetrics
from desktop.models.policy import PolicyConfig
from desktop.core.health.evaluator import HealthEngine


class TestHealthEngine(unittest.TestCase):
    def test_perfect_health(self):
        """0ms latency, 0ms jitter, 0% loss = 100 Health Score."""
        m = PathMetrics(latency_ms=0.0, jitter_ms=0.0, packet_loss_pct=0.0)
        score = HealthEngine.calculate_health_index(m)
        self.assertEqual(score, 100)

    def test_total_loss_zero_health(self):
        """100% packet loss = 0 Health Score."""
        m = PathMetrics(latency_ms=10.0, jitter_ms=2.0, packet_loss_pct=100.0)
        score = HealthEngine.calculate_health_index(m)
        self.assertEqual(score, 0)

    def test_state_evaluation_degradation(self):
        """When jitter exceeds alert threshold, path transitions to ALERT."""
        config = PolicyConfig(jitter_alert_threshold_ms=18.0)
        m = PathMetrics(latency_ms=25.0, jitter_ms=22.0, packet_loss_pct=0.0)
        new_state = HealthEngine.evaluate_state(InterfaceState.ONLINE, m, config, carrier_detected=True)
        self.assertEqual(new_state, InterfaceState.ALERT)

    def test_carrier_loss_transitions_offline(self):
        """When carrier is lost, interface transitions to OFFLINE immediately."""
        config = PolicyConfig()
        m = PathMetrics(latency_ms=15.0, jitter_ms=1.0, packet_loss_pct=0.0)
        new_state = HealthEngine.evaluate_state(InterfaceState.ONLINE, m, config, carrier_detected=False)
        self.assertEqual(new_state, InterfaceState.OFFLINE)

    def test_disabled_stays_disabled(self):
        """Administratively disabled adapter stays DISABLED."""
        config = PolicyConfig()
        m = PathMetrics(latency_ms=0.0, jitter_ms=0.0, packet_loss_pct=0.0)
        new_state = HealthEngine.evaluate_state(InterfaceState.DISABLED, m, config, carrier_detected=True)
        self.assertEqual(new_state, InterfaceState.DISABLED)


if __name__ == "__main__":
    unittest.main()
