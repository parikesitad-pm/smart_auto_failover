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

    def test_orchestrator_ui_contract(self):
        """Verify all properties and methods expected by the Cockpit UI are present on FailoverOrchestrator."""
        from desktop.platform import get_platform_backend
        from desktop.core.events.bus import EventBus
        from desktop.core.failover.orchestrator import FailoverOrchestrator
        from desktop.models.policy import WorkloadProfile

        backend = get_platform_backend()
        bus = EventBus()
        orch = FailoverOrchestrator(platform_backend=backend, event_bus=bus)

        # 1. Event bus access
        self.assertIs(orch.event_bus, bus)

        # 2. Policy engine config
        orch.policy_engine.config.workload_profile = WorkloadProfile.BROADCAST
        self.assertEqual(orch.config.workload_profile, WorkloadProfile.BROADCAST)

        # 3. Workload watcher scan
        apps = orch.workload_watcher.scan_active_processes()
        self.assertIsInstance(apps, set)

        # 4. Telemetry sampler
        dh = orch.latest_device_health
        self.assertIsNotNone(dh)
        self.assertTrue(hasattr(dh, "cpu_percent"))

        # 5. Metrics map
        metrics = orch.metrics
        self.assertIsInstance(metrics, dict)

        # 6. Lifecycle start and stop
        orch.start()
        orch.stop()


if __name__ == "__main__":
    unittest.main()
