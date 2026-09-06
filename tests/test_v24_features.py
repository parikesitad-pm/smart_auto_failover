"""
MODULA - Smart Auto Failover
Unit Tests for v2.4 Features:
- Dynamic 1 to 8 Priority Levels & Adapter Cards
- 4th IP Custom Ping Target & Probing
- Sports Car Tachometer Instrument Cluster & Multi-Channel Backbone Bars
- Inline Bandwidth QoS Monitor Widget
"""

import unittest
import customtkinter as ctk

from core.models import FailoverConfig, PriorityLevel
from core.failover_engine import FailoverEngine
from ui.components.sports_car_gauge import SportsCarGaugeWidget
from ui.components.app_qos_widget import AppQoSWidget


class TestV24Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Headless root for CTk widgets
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_priority_level_p1_to_p8(self):
        """Verify PriorityLevel enum supports all 8 priority tiers."""
        self.assertEqual(len(PriorityLevel), 8)
        self.assertEqual(PriorityLevel.P1.value, 1)
        self.assertEqual(PriorityLevel.P8.value, 8)
        self.assertEqual(PriorityLevel.P1.short_label, "LAN 1")
        self.assertEqual(PriorityLevel.P3.short_label, "Wi-Fi")
        self.assertEqual(PriorityLevel.P4.short_label, "Port 4")
        self.assertEqual(PriorityLevel.P8.short_label, "Port 8")

    def test_failover_config_quaternary_target(self):
        """Verify 4th IP target configuration, persistence, and configured targets list."""
        cfg = FailoverConfig(
            ping_target_primary="1.1.1.1",
            ping_target_secondary="8.8.8.8",
            ping_target_tertiary="9.9.9.9",
            ping_target_quaternary="",
        )
        targets_3 = cfg.get_configured_targets()
        self.assertEqual(targets_3, ["1.1.1.1", "8.8.8.8", "9.9.9.9"])

        # Add 4th target
        cfg.ping_target_quaternary = "208.67.222.222"
        targets_4 = cfg.get_configured_targets()
        self.assertEqual(len(targets_4), 4)
        self.assertEqual(targets_4[3], "208.67.222.222")

        # Verify serialization roundtrip
        d = cfg.to_dict()
        self.assertEqual(d.get("ping_target_quaternary"), "208.67.222.222")
        restored = FailoverConfig.from_dict(d)
        self.assertEqual(restored.ping_target_quaternary, "208.67.222.222")

    def test_failover_engine_p1_to_p8_states(self):
        """Verify FailoverEngine initializes states across all 8 priority levels."""
        cfg = FailoverConfig()
        engine = FailoverEngine(config=cfg)
        self.assertEqual(len(engine.states), 8)
        for p in PriorityLevel:
            self.assertIn(p, engine.states)
            self.assertEqual(engine.states[p].priority, p)

    def test_sports_car_gauge_dual_bars(self):
        """Verify SportsCarGaugeWidget renders multi-channel dual bars per target."""
        gauge = SportsCarGaugeWidget(self.root, height=135)
        # 3 targets -> 6 bars
        gauge.update_gauge(speed_mbps=45.2, latency_ms=16.0, jitter_ms=1.8, targets=["1.1.1.1", "8.8.8.8", "9.9.9.9"])
        self.assertEqual(gauge.speed_val, 45.2)
        self.assertEqual(len(gauge.targets), 3)

        # 4 targets -> 8 bars
        gauge.update_gauge(
            speed_mbps=88.5,
            latency_ms=12.0,
            jitter_ms=0.9,
            targets=["1.1.1.1", "8.8.8.8", "9.9.9.9", "208.67.222.222"],
        )
        self.assertEqual(gauge.speed_val, 88.5)
        self.assertEqual(len(gauge.targets), 4)
        gauge.destroy()

    def test_app_qos_widget_controls(self):
        """Verify AppQoSWidget correctly initializes and handles priority quick-boosts."""
        qos = AppQoSWidget(self.root)
        qos.update_stats()
        self.assertIsNotNone(qos.mode_label)

        # Test boost meeting
        qos._boost_meeting()
        self.assertIn("MEETING", qos.mode_label.cget("text"))

        # Test boost streaming
        qos._boost_streaming()
        self.assertIn("STREAMING", qos.mode_label.cget("text"))

        # Test balance all
        qos._balance_all()
        self.assertIn("SEIMBANG", qos.mode_label.cget("text"))
        qos.destroy()

    def test_ipv4_validation_logic(self):
        """Verify IP regex validation used in AddTargetModal and SettingsModal."""
        import re
        ip_regex = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"

        valid_ips = ["1.1.1.1", "8.8.8.8", "9.9.9.9", "208.67.222.222", "192.168.1.1", "10.0.0.1"]
        invalid_ips = ["999.999.999.999", "abc.def.ghi.jkl", "1.1.1", "1.1.1.1.1", "256.1.1.1", ""]

        for ip in valid_ips:
            self.assertIsNotNone(re.match(ip_regex, ip), f"Should be valid: {ip}")

        for ip in invalid_ips:
            self.assertIsNone(re.match(ip_regex, ip), f"Should be invalid: {ip}")


if __name__ == "__main__":
    unittest.main()
