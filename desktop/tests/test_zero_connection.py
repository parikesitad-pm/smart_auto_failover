"""
Characterization Unit Tests: Zero Connection Scenario
Author: parikesitad-pm
© 2026
"""

import unittest
from desktop.models.interface import NetworkInterface, InterfaceState, InterfaceMediaType
from desktop.models.metrics import PathMetrics
from desktop.models.policy import PolicyConfig, WorkloadProfile
from desktop.core.policy.engine import PolicyEngine


class TestZeroConnection(unittest.TestCase):
    def test_zero_connection_behavior(self):
        """
        When Ethernet is unplugged (OFFLINE) and Wi-Fi is disabled at OS level (DISABLED):
        - Active path: None
        - Policy: NO ELIGIBLE PATH (returns None)
        - All dynamic addressing cleared
        """
        eth = NetworkInterface(
            id="eth0",
            name="eth0",
            friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=False,
            admin_enabled=True,
            state=InterfaceState.OFFLINE,
            ip_address="192.168.1.10",
            gateway="192.168.1.1",
        )
        eth.clear_network_addressing()

        wifi = NetworkInterface(
            id="wlan0",
            name="wlan0",
            friendly_name="Wi-Fi",
            media_type=InterfaceMediaType.WIFI,
            carrier=False,
            admin_enabled=False,
            state=InterfaceState.DISABLED,
            ip_address="192.168.50.4",
            gateway="192.168.50.1",
            ssid="Office-WiFi"
        )
        wifi.clear_network_addressing()

        config = PolicyConfig()

        # Check policy failover evaluation with 0 usable candidates
        decision = PolicyEngine.evaluate_failover(
            [eth, wifi],
            active_id="eth0",
            config=config,
            profile=WorkloadProfile.CONFERENCE
        )

        # There are zero eligible candidates, so failover cannot pick any target
        self.assertIsNone(decision)
        # Verify no stale values remain
        self.assertIsNone(eth.ip_address)
        self.assertIsNone(eth.gateway)
        self.assertIsNone(wifi.ip_address)
        self.assertIsNone(wifi.gateway)
        self.assertIsNone(wifi.ssid)
        self.assertEqual(eth.metrics.health_index, 0)
        self.assertEqual(wifi.metrics.health_index, 0)


if __name__ == "__main__":
    unittest.main()
