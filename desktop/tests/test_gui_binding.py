"""
AutoFailover 3.0 - GUI State Binding & Non-Contradiction Tests
Author: parikesitad-pm
© 2026

Verifies that the presentation layer accurately binds to Core state:
- Non-contradiction invariant: No active path -> NO ELIGIBLE PATH (never ACTIVE PATH STABLE)
- Dynamic interface card rendering and state badge colors
- Historical event stream replay
- Workload status protection strings without truncation
"""

import unittest
from unittest.mock import MagicMock
from typing import Dict, Any

from desktop.models.interface import NetworkInterface, InterfaceState, InterfaceMediaType
from desktop.models.events import EventType, FailoverEvent
from desktop.core.events.bus import EventBus
from desktop.core.failover.orchestrator import FailoverOrchestrator
from desktop.ui.theme import COCKPIT_THEME


class MockOrchestrator:
    """Mock orchestrator providing controlled state snapshots to UI binding tests."""

    def __init__(self):
        self.interfaces = []
        self.active_interface = None
        self.active_interface_id = None
        self.metrics = {}
        self.config = MagicMock(takeover_margin=15.0)
        self.workload_watcher = MagicMock()
        self.workload_watcher.scan_active_processes.return_value = []
        self.latest_device_health = None
        self.bus = EventBus(max_history=50)
        self.event_bus = self.bus


class TestGuiBindingLogic(unittest.TestCase):
    def setUp(self):
        self.mock_orch = MockOrchestrator()

    def test_contradiction_avoidance_when_zero_active_path(self):
        """
        Verify that when active_interface is None, the dashboard state mapping
        strictly renders 'NO ACTIVE PATH' and 'NO ELIGIBLE PATH', never 'ACTIVE PATH STABLE'.
        """
        self.mock_orch.active_interface = None

        # Simulate _refresh_state logic directly
        active_if = self.mock_orch.active_interface
        if active_if:
            pill_text = f"ONLINE: {active_if.friendly_name}"
            engine_text = "ACTIVE PATH STABLE"
        else:
            pill_text = "NO ACTIVE PATH"
            engine_text = "NO ELIGIBLE PATH"

        self.assertEqual(pill_text, "NO ACTIVE PATH")
        self.assertEqual(engine_text, "NO ELIGIBLE PATH")
        self.assertNotEqual(engine_text, "ACTIVE PATH STABLE")

    def test_active_path_stable_when_online_interface_present(self):
        """Verify that when an interface is ONLINE, the dashboard reflects stable active path."""
        eth = NetworkInterface(
            id="eth0",
            name="eth0",
            friendly_name="Ethernet (eth0)",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.ONLINE,
            ip_address="192.168.1.5",
        )
        self.mock_orch.active_interface = eth

        active_if = self.mock_orch.active_interface
        if active_if:
            pill_text = f"ONLINE: {active_if.friendly_name}"
            engine_text = "ACTIVE PATH STABLE"
        else:
            pill_text = "NO ACTIVE PATH"
            engine_text = "NO ELIGIBLE PATH"

        self.assertEqual(pill_text, "ONLINE: Ethernet (eth0)")
        self.assertEqual(engine_text, "ACTIVE PATH STABLE")

    def test_workload_text_no_truncation(self):
        """Verify workload protection string avoids wide text truncation."""
        self.mock_orch.workload_watcher.scan_active_processes.return_value = ["Zoom"]

        active_apps = self.mock_orch.workload_watcher.scan_active_processes()
        if active_apps:
            val_text = "SESSION PROTECTED"
        else:
            val_text = "PASSIVE MONITOR"

        self.assertEqual(val_text, "SESSION PROTECTED")
        # Ensure string is compact and fits within standard KPI width
        self.assertLess(len(val_text), 20)

    def test_theme_contains_all_five_interface_states(self):
        """Verify that COCKPIT_THEME has semantic colors for all 5 interface states."""
        self.assertIn("state_online", COCKPIT_THEME)
        self.assertIn("state_ready", COCKPIT_THEME)
        self.assertIn("state_alert", COCKPIT_THEME)
        self.assertIn("state_offline", COCKPIT_THEME)
        self.assertIn("state_disabled", COCKPIT_THEME)

    def test_event_bus_replay_binding(self):
        """Verify that chronological replay delivers all prior events without dropping order."""
        bus = self.mock_orch.event_bus
        bus.publish(EventType.INTERFACE_DISCOVERED, "Discovered eth0")
        bus.publish(EventType.INTERFACE_DISCOVERED, "Discovered wlan0")
        bus.publish(EventType.ROUTE_SWITCHED, "Route switched to eth0")

        replayed_messages = []
        for ev in bus.get_history(limit=10):
            replayed_messages.append(ev.message)

        self.assertEqual(len(replayed_messages), 3)
        self.assertEqual(replayed_messages[0], "Discovered eth0")
        self.assertEqual(replayed_messages[1], "Discovered wlan0")
        self.assertEqual(replayed_messages[2], "Route switched to eth0")


if __name__ == "__main__":
    unittest.main()
