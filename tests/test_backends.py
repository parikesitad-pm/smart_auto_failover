import unittest
from core.network_manager import NetworkManager
from core.backends.windows_backend import WindowsBackend
from core.backends.macos_backend import MacOSBackend
from core.ping_probe import PingProbe, IS_WINDOWS


class TestCrossPlatformBackends(unittest.TestCase):
    def test_backend_instantiations(self):
        win_backend = WindowsBackend()
        self.assertIsNotNone(win_backend)

        mac_backend = MacOSBackend()
        self.assertIsNotNone(mac_backend)

    def test_network_manager_detection(self):
        backend = NetworkManager.get_backend()
        self.assertIsNotNone(backend)
        os_name = NetworkManager.get_os_name()
        print(f"\nDetected OS: {os_name}, Loaded Backend: {type(backend).__name__}")
        if IS_WINDOWS:
            self.assertIsInstance(backend, WindowsBackend)
            self.assertEqual(os_name, "Windows")

    def test_priority_order_method_exists(self):
        backend = NetworkManager.get_backend()
        self.assertTrue(hasattr(backend, "set_network_priority_order"))
        self.assertTrue(callable(getattr(backend, "set_network_priority_order")))

    def test_adapter_filtering(self):
        if IS_WINDOWS:
            backend = WindowsBackend()
            adapters = backend.get_all_adapters()
            # Ensure no loopback, Bluetooth, or Local Area Connection* virtual adapters leak into result
            for a in adapters:
                self.assertNotIn("loopback", a.alias.lower())
                self.assertFalse(a.alias.lower().startswith("local area connection*"))
                self.assertNotIn("bluetooth", a.alias.lower())
                self.assertNotIn("bluetooth", (a.description or "").lower())


if __name__ == "__main__":
    unittest.main()
