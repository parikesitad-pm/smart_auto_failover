"""
AutoFailover 3.0 - Runtime Integration Tests
Author: parikesitad-pm
© 2026

Verifies end-to-end orchestration between:
Platform HAL -> Orchestrator -> EventBus -> Health -> Policy -> Recovery
"""

import unittest
import time
from typing import List, Dict, Any, Optional, Tuple

from desktop.models.interface import NetworkInterface, InterfaceState, InterfaceMediaType
from desktop.models.events import EventType, FailoverEvent
from desktop.models.policy import PolicyConfig, WorkloadProfile
from desktop.platform.base import PlatformBackend
from desktop.core.events.bus import EventBus
from desktop.core.failover.orchestrator import FailoverOrchestrator


class MockPlatformBackend(PlatformBackend):
    """Controllable mock platform backend for integration testing."""

    def __init__(self):
        self.interfaces: Dict[str, NetworkInterface] = {}
        self.default_route: Optional[Tuple[str, str]] = None
        self.switch_route_calls: List[Tuple[str, str]] = []
        self.admin_state_calls: List[Tuple[str, bool]] = []

    def discover_interfaces(self) -> List[NetworkInterface]:
        return list(self.interfaces.values())

    def query_interface_details(self, name: str) -> Dict[str, Any]:
        iface = self.interfaces.get(name)
        if not iface:
            return {
                "carrier": False,
                "admin_enabled": False,
                "ip_address": None,
                "netmask": None,
                "gateway": None,
                "ssid": None,
                "link_speed": None,
            }
        return {
            "carrier": iface.carrier,
            "admin_enabled": iface.admin_enabled,
            "ip_address": iface.ip_address,
            "netmask": iface.netmask,
            "gateway": iface.gateway,
            "ssid": iface.ssid,
            "link_speed": iface.link_speed,
        }

    def get_default_route(self) -> Optional[Tuple[str, str]]:
        return self.default_route

    def set_default_route(self, interface_name: str, gateway: str) -> bool:
        self.switch_route_calls.append((interface_name, gateway))
        self.default_route = (interface_name, gateway)
        return True

    def switch_default_route(self, iface_name: str, gateway_ip: str) -> bool:
        return self.set_default_route(iface_name, gateway_ip)

    def set_interface_admin_state(self, name: str, enable: bool) -> bool:
        self.admin_state_calls.append((name, enable))
        if name in self.interfaces:
            self.interfaces[name].admin_enabled = enable
        return True

    def set_interface_state(self, iface_name: str, enabled: bool) -> bool:
        return self.set_interface_admin_state(iface_name, enabled)

    def get_system_identity(self) -> Dict[str, str]:
        return {
            "device_name": "TestHost",
            "os_name": "TestOS",
            "architecture": "x86_64",
            "kernel": "5.15-test",
        }


class TestRuntimeIntegration(unittest.TestCase):
    def setUp(self):
        self.backend = MockPlatformBackend()
        self.bus = EventBus(max_history=50)

        # Configure two test interfaces
        self.eth = NetworkInterface(
            id="eth0",
            name="eth0",
            friendly_name="Ethernet (eth0)",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.ONLINE,
            ip_address="192.168.1.10",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            link_speed="1000 Mbps",
        )
        self.wifi = NetworkInterface(
            id="wlan0",
            name="wlan0",
            friendly_name="Wi-Fi (wlan0)",
            media_type=InterfaceMediaType.WIFI,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.READY,
            ip_address="192.168.2.50",
            netmask="255.255.255.0",
            gateway="192.168.2.1",
            ssid="OfficeNet_5G",
            link_speed="433 Mbps",
        )

        self.backend.interfaces = {"eth0": self.eth, "wlan0": self.wifi}
        self.backend.default_route = ("eth0", "192.168.1.1")

        self.config = PolicyConfig(takeover_margin=15.0, recovery_cooldown_seconds=1.0)
        self.orchestrator = FailoverOrchestrator(
            platform_backend=self.backend,
            event_bus=self.bus,
            config=self.config,
            probe_interval_sec=0.1,
        )

    def tearDown(self):
        self.orchestrator.stop()

    def test_initialization_discovers_interfaces_and_sets_active_path(self):
        """Verify orchestrator discovery populates interfaces, default route, and emits bus events."""
        self.orchestrator.initialize()

        self.assertEqual(len(self.orchestrator.interfaces), 2)
        self.assertEqual(self.orchestrator.active_interface_id, "eth0")
        self.assertIsNotNone(self.orchestrator.active_interface)
        self.assertEqual(self.orchestrator.active_interface.name, "eth0")

        # Verify event bus logged discovery
        history = self.bus.get_history()
        discovery_events = [e for e in history if e.event_type == EventType.INTERFACE_DISCOVERED]
        self.assertEqual(len(discovery_events), 2)

    def test_start_loop_auto_initializes_if_not_already_initialized(self):
        """Verify start_loop automatically calls initialize if caller did not call it."""
        self.assertFalse(self.orchestrator._initialized)
        self.assertEqual(len(self.orchestrator.interfaces), 0)

        self.orchestrator.start()
        time.sleep(0.05)

        self.assertTrue(self.orchestrator._initialized)
        self.assertEqual(len(self.orchestrator.interfaces), 2)
        self.assertEqual(self.orchestrator.active_interface_id, "eth0")

    def test_carrier_drop_triggers_failover_to_eligible_path(self):
        """Verify carrier disconnection on active interface triggers failover to ready interface."""
        self.orchestrator.initialize()

        # Simulate carrier drop on eth0
        self.eth.carrier = False
        self.eth.state = InterfaceState.OFFLINE
        self.orchestrator.tick()

        # eth0 should lose active status
        self.assertEqual(self.eth.state, InterfaceState.OFFLINE)
        self.assertIsNone(self.eth.ip_address)

        # Failover should promote wlan0
        self.assertEqual(self.orchestrator.active_interface_id, "wlan0")
        self.assertEqual(self.wifi.state, InterfaceState.ONLINE)
        self.assertTrue(any(dev == "wlan0" for dev, _ in self.backend.switch_route_calls))

    def test_zero_eligible_path_handled_safely(self):
        """Verify that when all interfaces lose carrier, system cleanly enters NO ACTIVE PATH state."""
        self.orchestrator.initialize()

        # Drop both interfaces
        self.eth.carrier = False
        self.wifi.carrier = False
        self.orchestrator.tick()

        self.assertIsNone(self.orchestrator.active_interface)
        self.assertIsNone(self.orchestrator.active_interface_id)

    def test_admin_disable_and_enable(self):
        """Verify administrative action toggles adapter state without violating policy invariants."""
        self.orchestrator.initialize()

        # Disable wlan0
        success = self.orchestrator.set_interface_admin_state("wlan0", False)
        self.assertTrue(success)
        self.assertEqual(self.wifi.state, InterfaceState.DISABLED)
        self.assertFalse(self.wifi.admin_enabled)

        # Enable wlan0 back
        success = self.orchestrator.set_interface_admin_state("wlan0", True)
        self.assertTrue(success)
        self.assertEqual(self.wifi.state, InterfaceState.READY)
        self.assertTrue(self.wifi.admin_enabled)

    def test_event_bus_chronological_history_and_recent(self):
        """Verify EventBus get_history returns chronological order and get_recent_events returns newest first."""
        self.bus.publish(EventType.INTERFACE_DISCOVERED, "Event 1")
        self.bus.publish(EventType.STATE_TRANSITION, "Event 2")
        self.bus.publish(EventType.ROUTE_SWITCHED, "Event 3")

        history = self.bus.get_history(limit=10)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].message, "Event 1")
        self.assertEqual(history[2].message, "Event 3")

        recent = self.bus.get_recent_events(limit=10)
        self.assertEqual(recent[0].message, "Event 3")
        self.assertEqual(recent[2].message, "Event 1")


if __name__ == "__main__":
    unittest.main()
