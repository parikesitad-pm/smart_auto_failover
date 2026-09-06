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

from core.models import FailoverConfig, PriorityLevel, TrafficStats
from core.failover_engine import FailoverEngine
from core.traffic_monitor import TrafficMonitor
from ui.components.sports_car_gauge import SportsCarGaugeWidget
from ui.components.app_qos_widget import AppQoSWidget
from ui.modals.speedtest_modal import SportsCarSpeedGauge, OoklaGauge
from ui.modals.add_target_modal import AddTargetModal


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

    def test_sports_car_cockpit_gauges_and_backbone_dials(self):
        """Verify SportsCarGaugeWidget dual tachometer gauges, auto units, and circular backbone dials."""
        gauge = SportsCarGaugeWidget(self.root, height=140)
        # Default 3 targets -> 3 circular backbone dials
        self.assertEqual(len(gauge.targets), 3)
        self.assertEqual(len(gauge.bb_data), 3)

        # Update telemetry with stats and explicit dl/up kbps
        stats = TrafficStats(alias="Wi-Fi", download_kbps=25400.0, upload_kbps=8500.0, jitter_ms=1.4)
        gauge.update_telemetry(
            stats=stats,
            jitter=1.4,
            active_route_alias="P1 LAN 1",
            dl_kbps=25400.0,
            up_kbps=8500.0,
        )
        self.assertEqual(gauge.target_dl_kbps, 25400.0)
        self.assertEqual(gauge.target_up_kbps, 8500.0)
        self.assertEqual(gauge.target_jitter, 1.4)

        # Test speed formatting unit helper
        self.assertEqual(gauge._fmt_speed_val(500.0), ("500", "Kbps"))
        self.assertEqual(gauge._fmt_speed_val(12500.0), ("12.5", "Mbps"))
        self.assertEqual(gauge._fmt_speed_val(1250000.0), ("1.25", "Gbps"))

        # Add 4th target dynamically -> 4 circular dials
        gauge.set_targets(["1.1.1.1", "8.8.8.8", "9.9.9.9", "208.67.222.222"])
        self.assertEqual(len(gauge.targets), 4)
        self.assertEqual(len(gauge.bb_data), 4)
        self.assertIn("208.67.222.222", gauge.bb_data)

        # Backward compatible update_gauge call
        gauge.update_gauge(speed_mbps=55.0, latency_ms=14.0, jitter_ms=1.1)
        self.assertEqual(gauge.speed_val, 55.0)

        gauge.destroy()
        self.assertFalse(gauge._animating)

    def test_traffic_monitor_resolve_stats_fallback(self):
        """Verify TrafficMonitor.resolve_traffic_stats gracefully falls back to system total."""
        tm = TrafficMonitor()
        # Non-matching active alias falls back safely without KeyError
        stats = tm.resolve_traffic_stats("NonExistentAdapter", candidates=["LAN 1", "Wi-Fi"])
        self.assertIsInstance(stats, TrafficStats)
        self.assertGreaterEqual(stats.download_kbps, 0.0)
        self.assertGreaterEqual(stats.upload_kbps, 0.0)

    def test_add_target_modal_interface(self):
        """Verify AddTargetModal initializes with config/on_saved and handles save/delete."""
        cfg = FailoverConfig(ping_target_quaternary="208.67.222.222")
        saved_ips = []
        modal = AddTargetModal(self.root, config=cfg, on_saved=lambda ip: saved_ips.append(ip))
        self.assertEqual(modal.current_ip, "208.67.222.222")

        # Test valid save
        modal.ip_entry.delete(0, "end")
        modal.ip_entry.insert(0, "1.0.0.1")
        modal._save_target()
        self.assertIn("1.0.0.1", saved_ips)

        # Test delete target
        modal2 = AddTargetModal(self.root, current_ip="1.0.0.1", on_save=lambda ip: saved_ips.append(ip))
        modal2._delete_target()
        self.assertIn("", saved_ips)

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

    def test_sports_car_speedtest_gauge(self):
        """Verify SportsCarSpeedGauge renders tachometer dial, dynamic scale, peak hold, and lerp."""
        gauge = SportsCarSpeedGauge(self.root, width=330, height=175)
        self.assertEqual(gauge.max_scale, 100.0)
        self.assertEqual(gauge.stage_text, "READY")

        # Set speed below max scale
        gauge.set_speed(48.5, stage="DOWNLOAD")
        self.assertEqual(gauge.target_speed, 48.5)
        self.assertEqual(gauge.stage_text, "DOWNLOAD")
        self.assertEqual(gauge.peak_speed, 48.5)

        # Scale tier promotion when exceeding 88%
        gauge.set_speed(150.0, stage="FAST OOKLA")
        self.assertEqual(gauge.max_scale, 250.0)
        self.assertEqual(gauge.peak_speed, 150.0)

        # Peak hold remains even if current drops
        gauge.set_speed(20.0, stage="UPLOAD")
        self.assertEqual(gauge.peak_speed, 150.0)

        # Reset returns to clean 0 state
        gauge.reset()
        self.assertEqual(gauge.current_speed, 0.0)
        self.assertEqual(gauge.target_speed, 0.0)
        self.assertEqual(gauge.peak_speed, 0.0)
        self.assertEqual(gauge.stage_text, "READY")
        self.assertEqual(gauge.max_scale, 100.0)

        # Backwards compatibility alias check
        self.assertIs(OoklaGauge, SportsCarSpeedGauge)

        gauge.destroy()
        self.assertFalse(gauge._animating)


if __name__ == "__main__":
    unittest.main()
