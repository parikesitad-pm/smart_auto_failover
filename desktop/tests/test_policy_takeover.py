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

    def test_case_5_normal_all_healthy_prioritize_eth0(self):
        """Case 5: When eth0, eth1, and wifi are all healthy, eth0 is prioritized as primary."""
        eth1 = NetworkInterface(
            id="eth1",
            name="eth1",
            friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.READY,
            ip_address="192.168.2.10",
            gateway="192.168.2.1",
            metrics=PathMetrics(latency_ms=20.0, jitter_ms=2.0, packet_loss_pct=0.0),
        )
        ifaces = [self.eth, eth1, self.wifi]
        score_eth0 = PolicyEngine.compute_score(self.eth, self.config, WorkloadProfile.CONFERENCE, ifaces)
        score_eth1 = PolicyEngine.compute_score(eth1, self.config, WorkloadProfile.CONFERENCE, ifaces)
        score_wifi = PolicyEngine.compute_score(self.wifi, self.config, WorkloadProfile.CONFERENCE, ifaces)

        # Baseline hierarchy: eth0 > eth1 > wifi
        self.assertGreater(score_eth0.total_score, score_eth1.total_score)
        self.assertGreater(score_eth1.total_score, score_wifi.total_score)

        # Since eth0 is active and pristine, no switch is made
        decision = PolicyEngine.evaluate_failover(ifaces, active_id="eth0", config=self.config, profile=WorkloadProfile.CONFERENCE)
        self.assertIsNone(decision)

    def test_case_2_only_eth0_and_wifi_prioritize_eth(self):
        """Case 2: When only eth0 and wifi are connected, Ethernet is strictly prioritized."""
        ifaces = [self.eth, self.wifi]
        score_eth = PolicyEngine.compute_score(self.eth, self.config, WorkloadProfile.CONFERENCE, ifaces)
        score_wifi = PolicyEngine.compute_score(self.wifi, self.config, WorkloadProfile.CONFERENCE, ifaces)
        self.assertGreater(score_eth.total_score, score_wifi.total_score)

        # If currently active on wifi (e.g. from prior drop), healthy eth0 reclaims connection
        self.wifi.state = InterfaceState.ONLINE
        self.eth.state = InterfaceState.READY
        decision = PolicyEngine.evaluate_failover(ifaces, active_id="wlan0", config=self.config, profile=WorkloadProfile.CONFERENCE)
        self.assertIsNotNone(decision)
        target_id, reason = decision
        self.assertEqual(target_id, "eth0")
        self.assertIn("Reclaiming primary wire path", reason)

    def test_case_3_eth0_degraded_immediate_switch_to_eth1(self):
        """Case 3: eth0, eth1, and wifi connected. When eth0 connection degrades (ALERT/loss), immediately switch to eth1."""
        eth1 = NetworkInterface(
            id="eth1",
            name="eth1",
            friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.READY,
            ip_address="192.168.2.10",
            gateway="192.168.2.1",
            metrics=PathMetrics(latency_ms=21.0, jitter_ms=2.1, packet_loss_pct=0.0),
        )
        # Degrade active eth0 to ALERT state
        self.eth.state = InterfaceState.ALERT
        self.eth.metrics.latency_ms = 140.0
        self.eth.metrics.jitter_ms = 22.0
        self.eth.metrics.packet_loss_pct = 5.0

        ifaces = [self.eth, eth1, self.wifi]
        decision = PolicyEngine.evaluate_failover(ifaces, active_id="eth0", config=self.config, profile=WorkloadProfile.CONFERENCE)
        self.assertIsNotNone(decision)
        target_id, reason = decision
        self.assertEqual(target_id, "eth1")
        self.assertIn("Immediate switch to standby", reason)

    def test_case_4_eth0_and_eth1_both_alert_immediate_switch_to_wifi(self):
        """Case 4: eth0, eth1, and wifi connected. When both eth0 and eth1 are ALERT/degraded, immediately switch to wifi."""
        eth1 = NetworkInterface(
            id="eth1",
            name="eth1",
            friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.ALERT,
            ip_address="192.168.2.10",
            gateway="192.168.2.1",
            metrics=PathMetrics(latency_ms=150.0, jitter_ms=25.0, packet_loss_pct=8.0),
        )
        self.eth.state = InterfaceState.ALERT
        self.eth.metrics.latency_ms = 145.0
        self.eth.metrics.jitter_ms = 20.0
        self.eth.metrics.packet_loss_pct = 6.0

        ifaces = [self.eth, eth1, self.wifi]
        decision = PolicyEngine.evaluate_failover(ifaces, active_id="eth0", config=self.config, profile=WorkloadProfile.CONFERENCE)
        self.assertIsNotNone(decision)
        target_id, reason = decision
        self.assertEqual(target_id, "wlan0")
        self.assertIn("Emergency failover to Wi-Fi", reason)

    def test_workload_protection_active_eth1_preserved(self):
        """Workload continuity: When eth1 is active and healthy, do not switch back to eth0 unless eth1 degrades/RTO."""
        eth1 = NetworkInterface(
            id="eth1",
            name="eth1",
            friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.ONLINE,
            ip_address="192.168.2.10",
            gateway="192.168.2.1",
            metrics=PathMetrics(latency_ms=22.0, jitter_ms=2.2, packet_loss_pct=0.0),
        )
        # eth0 has now recovered and is READY
        self.eth.state = InterfaceState.READY
        self.eth.metrics.latency_ms = 19.0
        self.eth.metrics.jitter_ms = 1.9

        ifaces = [self.eth, eth1, self.wifi]
        # While eth1 is running live sessions (Zoom, vMix, OBS), maintain eth1!
        decision = PolicyEngine.evaluate_failover(ifaces, active_id="eth1", config=self.config, profile=WorkloadProfile.CONFERENCE)
        self.assertIsNone(decision)

        # But if eth1 subsequently experiences RTO/degradation, failover back to eth0 immediately!
        eth1.state = InterfaceState.ALERT
        eth1.metrics.packet_loss_pct = 100.0
        decision_after_drop = PolicyEngine.evaluate_failover(ifaces, active_id="eth1", config=self.config, profile=WorkloadProfile.CONFERENCE)
        self.assertIsNotNone(decision_after_drop)
        target_id, _ = decision_after_drop
        self.assertEqual(target_id, "eth0")


if __name__ == "__main__":
    unittest.main()
