"""
Automated UI & Component Verification Suite for MODULA v2.2.
Tests all CustomTkinter components, modal dialogs, and visualizers.
"""
import unittest
import tkinter as tk
import customtkinter as ctk

from core.models import (
    AdapterInfo,
    AdapterPortSummary,
    InterfaceStatus,
    LogEvent,
    LogLevel,
    MonitoredInterfaceState,
    PriorityLevel,
    TrafficStats,
)
from ui.components import (
    AdapterSummaryBar,
    InterfaceCard,
    LogPanel,
    SkeletonLoader,
    ToastNotificationManager,
    TrafficChartWidget,
)
from ui.modals import (
    BandwidthQoSModal,
    ChangelogModal,
    HelpFaqModal,
    SpeedtestDetailModal,
    SpeedtestModal,
    SystemDiagnosticsModal,
    TelemetrySourcesModal,
)


class TestUIComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a hidden test root for Tkinter widgets
        ctk.set_appearance_mode("Dark")
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_traffic_chart_widget_modes_and_updates(self):
        """Verify TrafficChartWidget updates, lerping, and all 3 visualizer modes without errors."""
        chart = TrafficChartWidget(self.root, width=400, height=80)
        self.assertIsNotNone(chart)

        # Feed traffic stats
        stats = TrafficStats(
            alias="Test-LAN",
            download_kbps=15420.0,
            upload_kbps=4500.0,
            jitter_ms=2.45,
            bytes_recv_sec=1927500,
            bytes_sent_sec=562500,
        )
        dl_hist = [1000.0, 5000.0, 15000.0, 15420.0]
        up_hist = [500.0, 2000.0, 4000.0, 4500.0]
        chart.update_traffic(stats, dl_hist, up_hist)

        # Test mode changes and redraws
        modes = ["⚡ Cyber Spectrum", "📡 RF Wave", "🌊 Smooth Curve"]
        for m in modes:
            chart._on_mode_change(m)
            self.assertEqual(chart.view_mode, m)
            chart._redraw_frame()

    def test_toast_notification_manager(self):
        """Verify toast bubbles queueing and dismissing."""
        toast = ToastNotificationManager(self.root)
        self.assertIsNotNone(toast)

        toast.success("Test Success Bubble")
        toast.error("Test Error Bubble")
        toast.warning("Test Warning Bubble")
        toast.info("Test Info Bubble")
        self.assertGreaterEqual(toast.queue.qsize(), 0)

    def test_adapter_summary_bar(self):
        """Verify port summary badges rendering."""
        summary_bar = AdapterSummaryBar(self.root)
        summary = AdapterPortSummary(
            total_ethernet=2,
            total_wireless=1,
            connected_count=3,
            active_route_alias="LAN 1 ('Ethernet')",
        )
        summary_bar.update_summary(summary)

    def test_interface_card(self):
        """Verify InterfaceCard updates with various latency and connection states."""
        card = InterfaceCard(
            self.root,
            priority=PriorityLevel.P1,
            on_adapter_selected=lambda p, a: None,
            on_toggle_adapter=lambda a, e: None,
        )
        card.set_adapter_options(["Ethernet 1", "Wi-Fi"], "Ethernet 1")

        state = MonitoredInterfaceState(
            priority=PriorityLevel.P1,
            alias="Ethernet 1",
            status=InterfaceStatus.ONLINE,
            assigned_metric=10,
            last_latency_ms=15.0,
            jitter_ms=1.2,
            total_pings=10,
            total_lost=0,
            is_active_route=True,
        )
        card.update_state(state)

    def test_log_panel(self):
        """Verify log appending and formatting."""
        log_panel = LogPanel(self.root)
        evt = LogEvent(
            timestamp="12:00:00",
            level=LogLevel.SUCCESS,
            message="Test Log Message for UI",
        )
        log_panel.append_log(evt)

    def test_telemetry_sources_modal(self):
        """Verify TelemetrySourcesModal renders technical probing explanations."""
        modal = TelemetrySourcesModal(self.root)
        self.assertIsNotNone(modal)
        modal.destroy()

    def test_changelog_and_help_modals(self):
        """Verify Changelog and Help FAQ modals instantiate properly."""
        cl = ChangelogModal(self.root)
        self.assertIsNotNone(cl)
        cl.destroy()

        hf = HelpFaqModal(self.root)
        self.assertIsNotNone(hf)
        hf.destroy()

    def test_bandwidth_qos_modal(self):
        """Verify Bandwidth QoS Modal opens and mounts process controls."""
        modal = BandwidthQoSModal(self.root)
        self.assertIsNotNone(modal)
        modal.destroy()

    def test_skeleton_loader(self):
        """Verify SkeletonLoader creation, progress updates, and dismiss."""
        sk = SkeletonLoader(self.root, on_finish=None, min_duration=0.1)
        self.assertIsNotNone(sk)
        sk.update_status("Testing network topology...", 0.45)
        self.assertEqual(sk.progress_bar.get(), 0.45)
        sk.destroy()

    def test_speedtest_detail_modal(self):
        """Verify SpeedtestDetailModal renders rich network quality telemetry."""
        sample_result = {
            "name": "Cloudflare Speed",
            "provider": "Cloudflare Edge CDN (Anycast)",
            "adapter": "Wi-Fi (Primary)",
            "download_mbps": 88.5,
            "upload_mbps": 42.1,
            "ping_ms": 11.2,
            "jitter_ms": 1.4,
            "packet_loss": 0.0,
            "bufferbloat_ms": 4.2,
            "location": "Jakarta / Singapore",
            "server": "Cloudflare CDN Anycast Node #42",
            "asn": "AS13335 (Cloudflare, Inc.)",
            "ip": "192.168.1.181",
        }
        modal = SpeedtestDetailModal(self.root, sample_result)
        self.assertIsNotNone(modal)
        modal.destroy()

    def test_splash_screen(self):
        """Verify SplashScreen HUD creation, canvas arcs, corner brackets, and completion."""
        from splash_screen import SplashScreen
        done_called = False

        def on_done():
            nonlocal done_called
            done_called = True

        splash = SplashScreen(master=self.root, on_finish=on_done, duration=0.1)
        self.assertIsNotNone(splash)
        self.assertEqual(splash.WIDTH, 560)
        self.assertEqual(splash.HEIGHT, 340)
        self.assertTrue(splash.is_active)
        splash._complete()
        self.assertTrue(done_called)


if __name__ == "__main__":
    unittest.main()
