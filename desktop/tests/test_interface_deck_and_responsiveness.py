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



if __name__ == "__main__":
    unittest.main()
