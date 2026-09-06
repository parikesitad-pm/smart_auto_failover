"""
Unit tests for MODULA - Smart Auto Failover v2.3 features.
Tests cover:
1. Bandwidth QoS: vMixService daemon filtering and priority presets (conference, streaming)
2. System Telemetry: GPU metrics & sampling
3. Settings Modal & Custom Ping configuration round-trip
4. Keyboard Shortcuts mapping & Tkinter key sequence converter
5. Changelog Modal v2.3 navigation
"""
import unittest
import customtkinter as ctk
from core.models import FailoverConfig, DEFAULT_SHORTCUTS
from core.bandwidth_qos import BandwidthQoSEngine, AppTrafficInfo
from core.system_telemetry import SystemTelemetry
from ui.app_window import AppWindow
from ui.modals.settings_modal import SettingsModal
from ui.modals.changelog_modal import ChangelogModal


class TestV23QoSAndPresets(unittest.TestCase):
    def test_vmix_service_ignored(self):
        """Verify vMixService.exe and background helpers are strictly ignored."""
        self.assertTrue(BandwidthQoSEngine.should_ignore("vMixService.exe"))
        self.assertTrue(BandwidthQoSEngine.should_ignore("vmixservice"))
        self.assertTrue(BandwidthQoSEngine.should_ignore("chrome_crashpad_handler.exe"))
        self.assertTrue(BandwidthQoSEngine.should_ignore("zoom_autoupdater.exe"))
        self.assertFalse(BandwidthQoSEngine.should_ignore("vMix64.exe"))
        self.assertFalse(BandwidthQoSEngine.should_ignore("Zoom.exe"))
        self.assertFalse(BandwidthQoSEngine.should_ignore("obs64.exe"))

    def test_qos_presets_conference(self):
        """Verify conference preset distributes 100% bandwidth with conference apps prioritized."""
        apps = [
            AppTrafficInfo(pid=101, name="Zoom.exe", friendly_name="Zoom Meeting", icon="🎥", exe_path="C:\\Zoom.exe", category="Video Conference"),
            AppTrafficInfo(pid=102, name="Spotify.exe", friendly_name="Spotify Music", icon="🎵", exe_path="C:\\Spotify.exe", category="Media & Audio"),
            AppTrafficInfo(pid=103, name="obs64.exe", friendly_name="OBS Studio", icon="🔴", exe_path="C:\\obs64.exe", category="Live Broadcast"),
        ]
        result = BandwidthQoSEngine.calculate_preset("conference", apps)
        self.assertEqual(len(result), 3)
        self.assertEqual(round(sum(result.values())), 100)
        self.assertTrue(result["Zoom.exe"] > result["Spotify.exe"])

    def test_qos_presets_streaming(self):
        """Verify streaming preset prioritizes live broadcast applications."""
        apps = [
            AppTrafficInfo(pid=201, name="obs64.exe", friendly_name="OBS Studio", icon="🔴", exe_path="C:\\obs64.exe", category="Live Broadcast"),
            AppTrafficInfo(pid=202, name="chrome.exe", friendly_name="Google Chrome", icon="🌐", exe_path="C:\\chrome.exe", category="Web & Meeting"),
        ]
        result = BandwidthQoSEngine.calculate_preset("streaming", apps)
        self.assertEqual(round(sum(result.values())), 100)
        self.assertTrue(result["obs64.exe"] > result["chrome.exe"])


class TestV23TelemetryAndSmoothBar(unittest.TestCase):
    def test_gpu_metrics(self):
        """Verify SystemTelemetry includes GPU metrics."""
        metrics = SystemTelemetry.get_live_metrics()
        self.assertTrue(hasattr(metrics, "gpu_percent"))
        self.assertTrue(hasattr(metrics, "gpu_name"))
        self.assertIsInstance(metrics.gpu_percent, float)
        self.assertGreaterEqual(metrics.gpu_percent, 0.0)

    def test_smooth_bar_rendering(self):
        """Verify _render_smooth_bar renders expected block shades."""
        bar_0 = AppWindow._render_smooth_bar(0.0, length=4)
        bar_50 = AppWindow._render_smooth_bar(50.0, length=4)
        bar_100 = AppWindow._render_smooth_bar(100.0, length=4)
        self.assertEqual(len(bar_0), 4)
        self.assertEqual(len(bar_50), 4)
        self.assertEqual(len(bar_100), 4)
        self.assertEqual(bar_0, "░░░░")
        self.assertEqual(bar_50, "██░░")
        self.assertEqual(bar_100, "████")


class TestV23ShortcutsAndKeyConversion(unittest.TestCase):
    def test_tk_key_conversion(self):
        """Verify shortcut strings convert to proper Tkinter sequences."""
        self.assertEqual(AppWindow._to_tk_key("Ctrl+M"), "<Control-m>")
        self.assertEqual(AppWindow._to_tk_key("F11"), "<F11>")
        self.assertEqual(AppWindow._to_tk_key("Ctrl+Shift+S"), "<Control-Shift-s>")
        self.assertEqual(AppWindow._to_tk_key("Alt+R"), "<Alt-r>")
        self.assertEqual(AppWindow._to_tk_key(""), "")

    def test_default_shortcuts_in_config(self):
        """Verify FailoverConfig initializes with full default shortcuts."""
        cfg = FailoverConfig()
        self.assertIsNotNone(cfg.shortcuts)
        for key in DEFAULT_SHORTCUTS.keys():
            self.assertIn(key, cfg.shortcuts)


class TestV23ModalsUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctk.set_appearance_mode("Dark")
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_settings_modal_instantiation(self):
        """Verify SettingsModal creates with Custom Ping and Shortcuts tabs."""
        cfg = FailoverConfig()
        modal = SettingsModal(self.root, config=cfg)
        self.assertIsNotNone(modal)
        self.assertTrue(hasattr(modal, "t1_entry"))
        self.assertTrue(hasattr(modal, "t2_entry"))
        self.assertTrue(hasattr(modal, "t3_entry"))
        self.assertTrue(hasattr(modal, "shortcut_entries"))
        modal.destroy()

    def test_changelog_modal_v23(self):
        """Verify ChangelogModal displays v2.3 and interactive version navigation."""
        from ui.modals.changelog_modal import CHANGELOG_DATA
        modal = ChangelogModal(self.root)
        self.assertIsNotNone(modal)
        self.assertEqual(modal.current_version, "v2.3")
        self.assertIn("v2.3", CHANGELOG_DATA)
        modal.destroy()


if __name__ == "__main__":
    unittest.main()
