import unittest
from core.network_manager import NetworkManager
from core.ping_probe import PingProbe


class TestPingProbe(unittest.TestCase):
    def test_ping_with_local_ip(self):
        adapters = NetworkManager.get_all_adapters()
        connected_with_ip = [a for a in adapters if a.is_connected and a.ipv4 and not a.ipv4.startswith("169.254.")]
        if not connected_with_ip:
            self.skipTest("No active connected network interface with valid IPv4 found to test live ping")

        primary = connected_with_ip[0]
        result = PingProbe.ping_interface(source_ip=primary.ipv4, target="1.1.1.1", timeout_ms=800)
        print(f"\nPing test on '{primary.alias}' (IP: {primary.ipv4}) -> Success: {result.success}, Latency: {result.latency_ms}ms, Error: '{result.error}'")
        self.assertTrue(result.success, f"Ping should succeed over {primary.alias}: {result.error}")
        self.assertGreater(result.latency_ms, 0)
        self.assertLess(result.latency_ms, 800)


if __name__ == "__main__":
    unittest.main()

