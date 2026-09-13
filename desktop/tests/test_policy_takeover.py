"""
Characterization Unit Tests: Policy Arbitration & Anti-Flap Takeover Margin
Author: parikesitad-pm
© 2026
"""

import unittest
from desktop.models.interface import NetworkInterface, InterfaceState, InterfaceMediaType
from desktop.models.metrics import PathMetrics
from desktop.models.policy import PolicyConfig, WorkloadProfile
from desktop.core.policy.engine import PolicyEngine


class TestPolicyTakeover(unittest.TestCase):
    def setUp(self):
        self.config = PolicyConfig(takeover_margin=12.0)
        self.eth = NetworkInterface(
            id="eth0",
            name="eth0",
            friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.ONLINE,
            ip_address="192.168.1.10",
            gateway="192.168.1.1",
            metrics=PathMetrics(latency_ms=20.0, jitter_ms=2.0, packet_loss_pct=0.0)
        )
        self.wifi = NetworkInterface(
            id="wlan0",
            name="wlan0",
            friendly_name="Wi-Fi",
            media_type=InterfaceMediaType.WIFI,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.READY,
            ip_address="192.168.50.4",
            gateway="192.168.50.1",
            metrics=PathMetrics(latency_ms=25.0, jitter_ms=3.0, packet_loss_pct=0.0)
        )

    def test_no_switch_for_tiny_difference(self):
        """Active path healthy, candidate slightly different -> NO switch."""
        decision = PolicyEngine.evaluate_failover(
            [self.eth, self.wifi],
            active_id="eth0",
            config=self.config,
            profile=WorkloadProfile.CONFERENCE
        )
        self.assertIsNone(decision)

    def test_takeover_when_margin_exceeded(self):
        """When standby candidate score exceeds active by at least takeover_margin -> switch!"""
        # Degrade active path: 160ms latency, 15ms jitter
        self.eth.metrics.latency_ms = 160.0
        self.eth.metrics.jitter_ms = 15.0
        # Standby candidate is pristine: 5ms latency, 0.5ms jitter
        self.wifi.metrics.latency_ms = 5.0
        self.wifi.metrics.jitter_ms = 0.5

        decision = PolicyEngine.evaluate_failover(
            [self.eth, self.wifi],
            active_id="eth0",
            config=self.config,
            profile=WorkloadProfile.CONFERENCE
        )
        self.assertIsNotNone(decision)
        target_id, reason = decision
        self.assertEqual(target_id, "wlan0")

    def test_immediate_switch_when_active_becomes_offline(self):
        """When active path is physically unplugged (OFFLINE), immediately switch bypassing margin."""
        self.eth.state = InterfaceState.OFFLINE
        self.eth.carrier = False
        self.eth.metrics.reset()

        decision = PolicyEngine.evaluate_failover(
            [self.eth, self.wifi],
            active_id="eth0",
            config=self.config,
            profile=WorkloadProfile.CONFERENCE
        )
        self.assertIsNotNone(decision)
        target_id, reason = decision
        self.assertEqual(target_id, "wlan0")
        self.assertIn("Emergency", reason)

    def test_disabled_adapter_never_selected(self):
        """Administratively disabled adapter must NEVER be selected."""
        self.eth.state = InterfaceState.OFFLINE
        self.wifi.state = InterfaceState.DISABLED
        self.wifi.admin_enabled = False

        decision = PolicyEngine.evaluate_failover(
            [self.eth, self.wifi],
            active_id="eth0",
            config=self.config,
            profile=WorkloadProfile.CONFERENCE
        )
        self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()
