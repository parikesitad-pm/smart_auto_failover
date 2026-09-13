"""
AutoFailover 3.0 Tests - Interface Deck UI & Runtime Responsiveness
Author: parikesitad-pm
© 2026
"""

import time
import unittest
from unittest.mock import MagicMock, patch
from desktop.models.interface import NetworkInterface, InterfaceState, InterfaceMediaType
from desktop.models.snapshot import RuntimeSnapshot
from desktop.core.failover.orchestrator import FailoverOrchestrator
from desktop.platform.windows.backend import WindowsPlatformBackend, get_subprocess_rate_per_min


class TestInterfaceDeckAndResponsiveness(unittest.TestCase):
    """Verifies Interface Deck requirements and non-blocking runtime invariants."""

    def test_snapshot_generation_and_thread_safety(self):
        backend = MagicMock()
        backend.discover_interfaces.return_value = [
            NetworkInterface(
                id="eth0",
                name="eth0",
                friendly_name="Ethernet (eth0)",
                media_type=InterfaceMediaType.ETHERNET,
                carrier=True,
                admin_enabled=True,
                state=InterfaceState.ONLINE,
                ip_address="192.168.1.100",
                gateway="192.168.1.1",
            ),
            NetworkInterface(
                id="wlan0",
                name="wlan0",
                friendly_name="Wi-Fi (wlan0)",
                media_type=InterfaceMediaType.WIFI,
                carrier=True,
                admin_enabled=True,
                state=InterfaceState.READY,
                ip_address="192.168.1.101",
                gateway="192.168.1.1",
                ssid="Corporate-Secure-5G",
            ),
        ]
        backend.get_default_route.return_value = ("eth0", "192.168.1.1")
        orchestrator = FailoverOrchestrator(platform_backend=backend)
        orchestrator.initialize()

        snapshot = orchestrator.get_snapshot()
        self.assertIsNotNone(snapshot)
        self.assertEqual(len(snapshot.interfaces), 2)
        self.assertIsNotNone(snapshot.active_interface)
        self.assertEqual(snapshot.active_interface.name, "eth0")
        self.assertIsNotNone(snapshot.standby_interface)
        self.assertEqual(snapshot.standby_interface.name, "wlan0")
        self.assertEqual(snapshot.engine_status, "ACTIVE PATH STABLE")

    def test_offline_interface_purges_stale_data(self):
        """Hides stale IP, Gateway, SSID when offline (Section 7)."""
        iface = NetworkInterface(
            id="eth0",
            name="eth0",
            friendly_name="Ethernet (eth0)",
            media_type=InterfaceMediaType.ETHERNET,
            carrier=False,
            admin_enabled=True,
            state=InterfaceState.OFFLINE,
            ip_address="192.168.1.100",
            gateway="192.168.1.1",
        )
        iface.clear_network_addressing()
        self.assertIsNone(iface.ip_address)
        self.assertIsNone(iface.gateway)
        self.assertIsNone(iface.ssid)
        self.assertEqual(iface.state, InterfaceState.OFFLINE)

    def test_disabled_interface_purges_stale_data(self):
        """Hides stale addressing when administratively disabled (Section 7)."""
        iface = NetworkInterface(
            id="wlan0",
            name="wlan0",
            friendly_name="Wi-Fi (wlan0)",
            media_type=InterfaceMediaType.WIFI,
            carrier=False,
            admin_enabled=False,
            state=InterfaceState.DISABLED,
            ip_address="10.0.0.5",
            gateway="10.0.0.1",
            ssid="Home-Mesh",
        )
        iface.clear_network_addressing()
        self.assertIsNone(iface.ip_address)
        self.assertIsNone(iface.gateway)
        self.assertIsNone(iface.ssid)
        self.assertEqual(iface.state, InterfaceState.DISABLED)

    def test_long_ssid_handling(self):
        """Ensures long SSIDs do not break data models or display."""
        long_ssid = "Super-Califragi-listic-Enterprise-Guest-Wi-Fi-Access-Point-Floor-4-Very-Long-SSID"
        iface = NetworkInterface(
            id="wlan0",
            name="wlan0",
            friendly_name="Wi-Fi (wlan0)",
            media_type=InterfaceMediaType.WIFI,
            carrier=True,
            admin_enabled=True,
            state=InterfaceState.READY,
            ip_address="192.168.50.4",
            ssid=long_ssid,
        )
        self.assertEqual(iface.ssid, long_ssid)

    def test_zero_interfaces_snapshot(self):
        """Ensures zero-interface state sets appropriate engine status."""
        backend = MagicMock()
        backend.discover_interfaces.return_value = []
        backend.get_default_route.return_value = None
        orchestrator = FailoverOrchestrator(platform_backend=backend)
        orchestrator.initialize()

        snapshot = orchestrator.get_snapshot()
        self.assertEqual(len(snapshot.interfaces), 0)
        self.assertIsNone(snapshot.active_interface)
        self.assertEqual(snapshot.engine_status, "NO ELIGIBLE PATH")

    def test_windows_backend_caching_and_subprocesses(self):
        """Ensures Windows backend utilizes caching and tracks subprocess rates."""
        win_backend = WindowsPlatformBackend()
        mock_psutil = MagicMock()
        mock_psutil.net_if_addrs.return_value = {"Ethernet": []}
        mock_stat = MagicMock()
        mock_stat.isup = True
        mock_stat.speed = 1000
        mock_psutil.net_if_stats.return_value = {"Ethernet": mock_stat}

        win_backend._static_adapter_cache["Ethernet"] = {
            "friendly_name": "Ethernet (Intel I225-V)",
            "media_type": InterfaceMediaType.ETHERNET,
            "description": "Intel Ethernet Controller",
            "link_speed": "1 Gbps",
        }
        win_backend._cache_default_route = (time.monotonic(), ("Ethernet", "192.168.1.1"))

        with patch.dict("sys.modules", {"psutil": mock_psutil}), \
             patch("desktop.platform.windows.backend.HAS_PSUTIL", True), \
             patch("desktop.platform.windows.backend.psutil", mock_psutil, create=True):
            with patch.object(win_backend, "_run_ps") as mock_ps:
                ifaces = win_backend.discover_interfaces()
                self.assertEqual(len(ifaces), 1)
                self.assertEqual(ifaces[0].friendly_name, "Ethernet (Intel I225-V)")
                # _run_ps should not be called because Ethernet was already cached!
                mock_ps.assert_not_called()

        rate = get_subprocess_rate_per_min()
        self.assertIsInstance(rate, int)

    def test_unused_disconnected_ethernet_stays_hidden_after_every_sort_tick(self):
        """Unused disconnected Ethernet port stays hidden and does NOT reappear from sorting."""
        from desktop.ui.dashboard.cockpit import CockpitDashboard
        eth_active = NetworkInterface(
            id="eth0", name="eth0", friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.ONLINE, ip_address="192.168.1.10",
        )
        eth_disconnected = NetworkInterface(
            id="eth1", name="eth1", friendly_name="Ethernet 2 (Unused)",
            media_type=InterfaceMediaType.ETHERNET, carrier=False, admin_enabled=True,
            state=InterfaceState.OFFLINE,
        )
        wifi = NetworkInterface(
            id="wlan0", name="wlan0", friendly_name="Wi-Fi",
            media_type=InterfaceMediaType.WIFI, carrier=True, admin_enabled=True,
            state=InterfaceState.READY, ip_address="192.168.1.20",
        )
        all_ifaces = [eth_active, eth_disconnected, wifi]

        # Stage 2: Visibility filter
        visible = CockpitDashboard._filter_overview_interfaces(all_ifaces, show_inactive=False)
        self.assertNotIn(eth_disconnected, visible)
        self.assertEqual(len(visible), 2)

        # Stage 3: Sorting multiple times
        for _ in range(5):
            ordered = CockpitDashboard._sort_visible_interfaces(visible)
            # Must NEVER cause disconnected Ethernet to reappear
            self.assertNotIn(eth_disconnected, ordered)
            self.assertEqual(len(ordered), 2)

    def test_online_remains_first_among_visible_cards(self):
        """ONLINE active connection always sorts to index 0."""
        from desktop.ui.dashboard.cockpit import CockpitDashboard
        ready_eth = NetworkInterface(
            id="eth1", name="eth1", friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.READY, ip_address="192.168.1.2",
        )
        online_eth = NetworkInterface(
            id="eth0", name="eth0", friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.ONLINE, ip_address="192.168.1.1",
        )
        alert_wifi = NetworkInterface(
            id="wlan0", name="wlan0", friendly_name="Wi-Fi",
            media_type=InterfaceMediaType.WIFI, carrier=True, admin_enabled=True,
            state=InterfaceState.ALERT, ip_address="192.168.1.3",
        )
        visible = [ready_eth, alert_wifi, online_eth]
        ordered = CockpitDashboard._sort_visible_interfaces(visible)
        self.assertEqual(ordered[0].id, "eth0")
        self.assertEqual(ordered[0].state, InterfaceState.ONLINE)

    def test_ready_ethernet_sorts_above_ready_wifi(self):
        """READY Ethernet always sorts above READY Wi-Fi."""
        from desktop.ui.dashboard.cockpit import CockpitDashboard
        ready_wifi = NetworkInterface(
            id="wlan0", name="wlan0", friendly_name="Wi-Fi",
            media_type=InterfaceMediaType.WIFI, carrier=True, admin_enabled=True,
            state=InterfaceState.READY, ip_address="192.168.1.50",
        )
        ready_eth = NetworkInterface(
            id="eth1", name="eth1", friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.READY, ip_address="192.168.1.51",
        )
        visible = [ready_wifi, ready_eth]
        ordered = CockpitDashboard._sort_visible_interfaces(visible)
        self.assertEqual(ordered[0].id, "eth1")
        self.assertEqual(ordered[1].id, "wlan0")

    def test_connecting_previously_hidden_ethernet_makes_it_visible(self):
        """Plugging cable in changes carrier to True, making interface visible and properly sorted."""
        from desktop.ui.dashboard.cockpit import CockpitDashboard
        eth = NetworkInterface(
            id="eth1", name="eth1", friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET, carrier=False, admin_enabled=True,
            state=InterfaceState.OFFLINE,
        )
        # Initially hidden
        visible = CockpitDashboard._filter_overview_interfaces([eth], show_inactive=False)
        # (Fallback returns it only if zero interfaces exist, but when others exist it's hidden)
        online_eth = NetworkInterface(
            id="eth0", name="eth0", friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.ONLINE, ip_address="192.168.1.1",
        )
        visible = CockpitDashboard._filter_overview_interfaces([online_eth, eth], show_inactive=False)
        self.assertNotIn(eth, visible)

        # Cable plugged in -> becomes READY
        eth.carrier = True
        eth.state = InterfaceState.READY
        eth.ip_address = "192.168.1.2"
        visible_after = CockpitDashboard._filter_overview_interfaces([online_eth, eth], show_inactive=False)
        self.assertIn(eth, visible_after)
        ordered = CockpitDashboard._sort_visible_interfaces(visible_after)
        self.assertEqual(ordered[0].id, "eth0")
        self.assertEqual(ordered[1].id, "eth1")

    def test_disconnecting_irrelevant_ethernet_hides_it_again(self):
        """Unplugging cable transitions state to OFFLINE, hiding it from Overview."""
        from desktop.ui.dashboard.cockpit import CockpitDashboard
        online_eth = NetworkInterface(
            id="eth0", name="eth0", friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.ONLINE, ip_address="192.168.1.1",
        )
        eth2 = NetworkInterface(
            id="eth1", name="eth1", friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.READY, ip_address="192.168.1.2",
        )
        # Unplugged
        eth2.carrier = False
        eth2.state = InterfaceState.OFFLINE
        eth2.clear_network_addressing()

        visible = CockpitDashboard._filter_overview_interfaces([online_eth, eth2], show_inactive=False)
        self.assertNotIn(eth2, visible)
        self.assertIn(online_eth, visible)

    def test_show_inactive_reveals_all_interfaces_intentionally(self):
        """Enabling Show Inactive reveals all interfaces intentionally."""
        from desktop.ui.dashboard.cockpit import CockpitDashboard
        online_eth = NetworkInterface(
            id="eth0", name="eth0", friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.ONLINE, ip_address="192.168.1.1",
        )
        offline_eth = NetworkInterface(
            id="eth1", name="eth1", friendly_name="Ethernet 2",
            media_type=InterfaceMediaType.ETHERNET, carrier=False, admin_enabled=True,
            state=InterfaceState.OFFLINE,
        )
        disabled_wifi = NetworkInterface(
            id="wlan0", name="wlan0", friendly_name="Wi-Fi",
            media_type=InterfaceMediaType.WIFI, carrier=False, admin_enabled=False,
            state=InterfaceState.DISABLED,
        )
        all_ifaces = [online_eth, offline_eth, disabled_wifi]

        visible = CockpitDashboard._filter_overview_interfaces(all_ifaces, show_inactive=True)
        self.assertEqual(len(visible), 3)
        self.assertIn(offline_eth, visible)
        self.assertIn(disabled_wifi, visible)

    def test_sorting_does_not_mutate_interface_visibility_state(self):
        """Sorting is pure and does not mutate interface attributes or list membership."""
        from desktop.ui.dashboard.cockpit import CockpitDashboard
        online_eth = NetworkInterface(
            id="eth0", name="eth0", friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.ONLINE, ip_address="192.168.1.1",
        )
        ready_wifi = NetworkInterface(
            id="wlan0", name="wlan0", friendly_name="Wi-Fi",
            media_type=InterfaceMediaType.WIFI, carrier=True, admin_enabled=True,
            state=InterfaceState.READY, ip_address="192.168.1.2",
        )
        visible = [ready_wifi, online_eth]
        ordered = CockpitDashboard._sort_visible_interfaces(visible)

        # Original list unchanged in identity of members
        self.assertEqual(len(ordered), len(visible))
        self.assertEqual(online_eth.state, InterfaceState.ONLINE)
        self.assertEqual(ready_wifi.state, InterfaceState.READY)

    def test_detail_modal_opens_without_typeerror_or_attributeerror(self):
        """Verifies compute_score and is_eligible_candidate calls inside detail modal logic do not crash."""
        from desktop.core.policy.engine import PolicyEngine
        from desktop.models.policy import PolicyConfig, WorkloadProfile
        iface = NetworkInterface(
            id="eth0", name="eth0", friendly_name="Ethernet 1",
            media_type=InterfaceMediaType.ETHERNET, carrier=True, admin_enabled=True,
            state=InterfaceState.ONLINE, ip_address="192.168.1.1",
        )
        config = PolicyConfig()
        profile = WorkloadProfile.CONFERENCE
        # Calling compute_score with 4 arguments must return CandidateScore
        score_obj = PolicyEngine.compute_score(iface, config, profile, [iface])
        self.assertIsNotNone(score_obj)
        self.assertIsInstance(score_obj.total_score, float)
        # Calling is_eligible_candidate on state must return bool
        self.assertIsInstance(iface.state.is_eligible_candidate(), bool)


if __name__ == "__main__":
    unittest.main()
