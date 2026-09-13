"""
Characterization Unit Tests: 5-State Model & Disconnect Behavior
Author: parikesitad-pm
© 2026
"""

import unittest
from desktop.models.interface import InterfaceState, NetworkInterface, InterfaceMediaType
from desktop.models.metrics import PathMetrics


class TestInterfaceStates(unittest.TestCase):
    def test_five_state_distinctions(self):
        """Verify 5 distinct states exist per contract."""
        self.assertEqual(InterfaceState.ONLINE.value, "ONLINE")
        self.assertEqual(InterfaceState.READY.value, "READY")
        self.assertEqual(InterfaceState.ALERT.value, "ALERT")
        self.assertEqual(InterfaceState.OFFLINE.value, "OFFLINE")
        self.assertEqual(InterfaceState.DISABLED.value, "DISABLED")

    def test_candidate_eligibility(self):
        """Only READY and ALERT are eligible for failover; DISABLED and OFFLINE are strictly excluded."""
        self.assertTrue(InterfaceState.READY.is_eligible_candidate())
        self.assertTrue(InterfaceState.ALERT.is_eligible_candidate())
        self.assertFalse(InterfaceState.ONLINE.is_eligible_candidate())
        self.assertFalse(InterfaceState.OFFLINE.is_eligible_candidate())
        self.assertFalse(InterfaceState.DISABLED.is_eligible_candidate())

    def test_disabled_clears_addressing(self):
        """When an adapter is disabled or disconnected, dynamic addressing is blanked."""
        iface = NetworkInterface(
            id="eth0",
            name="eth0",
            friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.ONLINE,
            ip_address="192.168.1.100",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            ssid=None,
            link_speed="1 Gbps",
        )
        iface.clear_network_addressing()
        self.assertIsNone(iface.ip_address)
        self.assertIsNone(iface.netmask)
        self.assertIsNone(iface.gateway)
        self.assertEqual(iface.metrics.packet_loss_pct, 100.0)
        self.assertEqual(iface.metrics.health_index, 0)


if __name__ == "__main__":
    unittest.main()
