"""
AutoFailover 3.0 Digital Network Cockpit Dashboard
Author: parikesitad-pm
© 2026

Main digital instrument cluster for AutoFailover 3.0.
Consumes runtime state from FailoverOrchestrator and renders responsive UI.
"""

import os
import time
import threading
import webbrowser
from typing import Any, Dict, List, Optional, Tuple

try:
    import customtkinter as ctk
    from PIL import Image
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from ..theme import COCKPIT_THEME
from ...models.interface import NetworkInterface, InterfaceState, InterfaceMediaType
from ...models.events import FailoverEvent
from ...models.policy import WorkloadProfile
from ...core.failover.orchestrator import FailoverOrchestrator
from ...core.speedtest import SpeedTestRunner, SpeedTestResult


def get_health_rating(score: int, is_connected: bool) -> Tuple[str, str]:
    """Returns (rating_text, color_hex) for Network Health Index."""
    if not is_connected or score <= 0:
        return "NO CONNECTION", COCKPIT_THEME["red"]
    elif score >= 90:
        return "EXCELLENT", COCKPIT_THEME["emerald"]
    elif score >= 75:
        return "HEALTHY", COCKPIT_THEME["cyan"]
    elif score >= 55:
        return "DEGRADED", COCKPIT_THEME["amber"]
    elif score >= 30:
        return "POOR", COCKPIT_THEME["amber"]
    else:
        return "CRITICAL", COCKPIT_THEME["red"]


class CockpitDashboard:
    """
    Main digital instrument cluster for AutoFailover 3.0.
    Consumes runtime state from FailoverOrchestrator and renders responsive UI.
    """

    def __init__(self, parent: Any, orchestrator: FailoverOrchestrator, logo_path: str):
        self.parent = parent
        self.orchestrator = orchestrator
        self.logo_path = logo_path
        self.speedtest_runner = SpeedTestRunner()
        self._interface_cards: Dict[str, Dict[str, Any]] = {}
        self._placeholder_lbl: Optional[Any] = None
        self._latest_speedtest: Optional[SpeedTestResult] = None
        self._last_health_breakdown: Dict[str, Any] = {}

        if not HAS_CTK:
            return

        self.root_frame = ctk.CTkFrame(self.parent, fg_color=COCKPIT_THEME["bg_dark"])
        self.root_frame.pack(fill="both", expand=True)

        self._build_top_bar()
        self._build_kpi_cards()
        self._build_main_split()
        self._build_bottom_status()

        # Subscribe to orchestrator event bus and replay history
        bus = getattr(self.orchestrator, "event_bus", None) or getattr(self.orchestrator, "bus", None)
        if bus:
            bus.subscribe(self._on_bus_event)
            if hasattr(bus, "get_history"):
                for ev in bus.get_history(limit=30):
                    self._render_event(ev)
            elif hasattr(bus, "get_recent_events"):
                for ev in reversed(bus.get_recent_events(limit=30)):
                    self._render_event(ev)

        # Start periodic UI polling ticker (5 Hz)
        self._schedule_ui_tick()

    def _build_top_bar(self):
        self.top_bar = ctk.CTkFrame(
            self.root_frame,
            fg_color=COCKPIT_THEME["bg_card"],
            height=68,
            corner_radius=0,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        self.top_bar.pack(fill="x", padx=0, pady=0)
        self.top_bar.pack_propagate(False)

        # Brand / Title (Section 1 & 6: AutoFailover 3.0 by Modula)
        brand_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        brand_frame.pack(side="left", padx=20, pady=10)

        if os.path.exists(self.logo_path):
            try:
                pil_img = Image.open(self.logo_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(36, 36))
                logo_lbl = ctk.CTkLabel(brand_frame, image=ctk_img, text="")
                logo_lbl.pack(side="left", padx=(0, 12))
            except Exception:
                pass

        titles_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        titles_box.pack(side="left")

        title_lbl = ctk.CTkLabel(
            titles_box,
            text="AutoFailover 3.0",
            font=("Segoe UI", 16, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
            anchor="w",
        )
        title_lbl.pack(anchor="w")

        ver_lbl = ctk.CTkLabel(
            titles_box,
            text="by Modula",
            font=("Segoe UI", 11),
            text_color=COCKPIT_THEME["emerald"],
            anchor="w",
        )
        ver_lbl.pack(anchor="w")

        # Active Path Status Pill (Section 7: prominent active indicator)
        self.active_pill = ctk.CTkLabel(
            self.top_bar,
            text="ONLINE: Scanning...",
            font=("Segoe UI", 12, "bold"),
            text_color=COCKPIT_THEME["emerald"],
            fg_color=COCKPIT_THEME["bg_surface"],
            corner_radius=16,
            padx=16,
            pady=6,
        )
        self.active_pill.pack(side="right", padx=20, pady=14)

        # Workload Profile Selector
        self.workload_menu = ctk.CTkOptionMenu(
            self.top_bar,
            values=["VIDEO_CONFERENCE", "LIVE_STREAMING", "GENERAL"],
            command=self._on_workload_change,
            fg_color=COCKPIT_THEME["bg_surface"],
            button_color=COCKPIT_THEME["border_highlight"],
            text_color=COCKPIT_THEME["cyan"],
            font=("Segoe UI", 11, "bold"),
            width=170,
            height=30,
        )
        self.workload_menu.set("VIDEO_CONFERENCE")
        self.workload_menu.pack(side="right", padx=(0, 12), pady=14)

        workload_lbl = ctk.CTkLabel(
            self.top_bar,
            text="Workload Profile:",
            font=("Segoe UI", 11),
            text_color=COCKPIT_THEME["text_muted"],
        )
        workload_lbl.pack(side="right", padx=(0, 8), pady=14)

    def _build_kpi_cards(self):
        kpi_container = ctk.CTkFrame(self.root_frame, fg_color="transparent", height=100)
        kpi_container.pack(fill="x", padx=20, pady=(16, 12))

        for i in range(4):
            kpi_container.columnconfigure(i, weight=1, uniform="kpi")

        # 1. RFC 3550 Latency & Jitter
        self.card_rtt = self._create_card(kpi_container, 0, "LATENCY / RFC 3550 JITTER", "-- ms", "Jitter: -- ms")

        # 2. Network Health Index (Interactive on click)
        self.card_health = self._create_card(
            kpi_container,
            1,
            "NETWORK HEALTH INDEX",
            "-- / 100",
            "Click for Breakdown",
            on_click=self._show_health_detail_modal,
        )

        # 3. Workload Continuity
        self.card_workload = self._create_card(kpi_container, 2, "ACTIVE WORKLOAD PROTECTION", "MONITORING", "Protected: Zoom, OBS, Teams")

        # 4. Failover Decision Engine
        self.card_engine = self._create_card(kpi_container, 3, "FAILOVER POLICY ENGINE", "ACTIVE PATH STABLE", "Takeover Margin: 15.0 pts")

    def _create_card(
        self,
        parent: Any,
        col: int,
        header: str,
        val_text: str,
        sub_text: str,
        on_click: Optional[Any] = None,
    ) -> Dict[str, Any]:
        frame = ctk.CTkFrame(
            parent,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
            height=90,
        )
        frame.grid(row=0, column=col, padx=6, sticky="nsew")
        frame.pack_propagate(False)

        h_lbl = ctk.CTkLabel(
            frame,
            text=header,
            font=("Segoe UI", 9, "bold"),
            text_color=COCKPIT_THEME["text_muted"],
        )
        h_lbl.pack(anchor="w", padx=14, pady=(10, 2))

        v_lbl = ctk.CTkLabel(
            frame,
            text=val_text,
            font=("Segoe UI", 13, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        v_lbl.pack(anchor="w", padx=14, pady=(0, 2))

        s_lbl = ctk.CTkLabel(
            frame,
            text=sub_text,
            font=("Segoe UI", 10),
            text_color=COCKPIT_THEME["cyan"],
        )
        s_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        if on_click:
            frame.bind("<Button-1>", lambda e: on_click())
            h_lbl.bind("<Button-1>", lambda e: on_click())
            v_lbl.bind("<Button-1>", lambda e: on_click())
            s_lbl.bind("<Button-1>", lambda e: on_click())
            frame.configure(cursor="hand2")

        return {"frame": frame, "val": v_lbl, "sub": s_lbl}

    def _build_main_split(self):
        main_split = ctk.CTkFrame(self.root_frame, fg_color="transparent")
        main_split.pack(fill="both", expand=True, padx=20, pady=0)

        main_split.columnconfigure(0, weight=3)
        main_split.columnconfigure(1, weight=2)
        main_split.rowconfigure(0, weight=1)

        # Left Column: Network Interfaces Deck
        left_frame = ctk.CTkFrame(
            main_split,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        left_frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        deck_title = ctk.CTkLabel(
            left_frame,
            text="NETWORK INTERFACES DECK",
            font=("Segoe UI", 12, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        deck_title.pack(anchor="w", padx=16, pady=(14, 8))

        # Scrollable interfaces list
        self.interfaces_scroll = ctk.CTkScrollableFrame(
            left_frame,
            fg_color="transparent",
            scrollbar_button_color=COCKPIT_THEME["border"],
        )
        self.interfaces_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Right Column: Speed Test & Live Event Stream
        right_frame = ctk.CTkFrame(main_split, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)

        # Speed Test Card
        self._build_speedtest_panel(right_frame)

        # Real-time Events Card
        self._build_events_panel(right_frame)

    def _build_speedtest_panel(self, parent: Any):
        frame = ctk.CTkFrame(
            parent,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        frame.grid(row=0, column=0, pady=(0, 8), sticky="nsew")

        st_title = ctk.CTkLabel(
            frame,
            text="BANDWIDTH & SPEED BENCHMARK",
            font=("Segoe UI", 12, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        st_title.pack(anchor="w", padx=16, pady=(12, 6))

        # Controls row
        ctrl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=16, pady=4)

        self.provider_menu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=["ookla", "fast_com", "cloudflare", "nperf"],
            fg_color=COCKPIT_THEME["bg_surface"],
            button_color=COCKPIT_THEME["border_highlight"],
            text_color=COCKPIT_THEME["cyan"],
            font=("Segoe UI", 11),
            width=110,
            height=28,
        )
        self.provider_menu.set("cloudflare")
        self.provider_menu.pack(side="left", padx=(0, 6))

        self.btn_run_test = ctk.CTkButton(
            ctrl_frame,
            text="Run Test",
            command=self._start_speed_test,
            font=("Segoe UI", 11, "bold"),
            fg_color=COCKPIT_THEME["emerald"],
            hover_color=COCKPIT_THEME["emerald_glow"],
            height=28,
            width=90,
        )
        self.btn_run_test.pack(side="left", padx=3)

        self.btn_bulk_test = ctk.CTkButton(
            ctrl_frame,
            text="Bulk (All 4)",
            command=self._start_bulk_test,
            font=("Segoe UI", 11),
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            height=28,
            width=80,
        )
        self.btn_bulk_test.pack(side="left", padx=3)

        self.btn_detail_test = ctk.CTkButton(
            ctrl_frame,
            text="Details",
            command=self._show_speedtest_detail_modal,
            font=("Segoe UI", 11),
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            height=28,
            width=70,
        )
        self.btn_detail_test.pack(side="left", padx=3)

        # Speed readout
        self.speed_readout_lbl = ctk.CTkLabel(
            frame,
            text="Ready to benchmark active connection (does not affect failover)",
            font=("Consolas", 10),
            text_color=COCKPIT_THEME["text_muted"],
        )
        self.speed_readout_lbl.pack(anchor="w", padx=16, pady=8)

    def _build_events_panel(self, parent: Any):
        frame = ctk.CTkFrame(
            parent,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        frame.grid(row=1, column=0, pady=(8, 0), sticky="nsew")

        ev_title = ctk.CTkLabel(
            frame,
            text="SYSTEM & FAILOVER EVENTS",
            font=("Segoe UI", 12, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        ev_title.pack(anchor="w", padx=16, pady=(12, 6))

        self.events_scroll = ctk.CTkScrollableFrame(
            frame,
            fg_color="transparent",
            scrollbar_button_color=COCKPIT_THEME["border"],
        )
        self.events_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_bottom_status(self):
        bottom_bar = ctk.CTkFrame(
            self.root_frame,
            fg_color=COCKPIT_THEME["bg_card"],
            height=36,
            corner_radius=0,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        bottom_bar.pack(fill="x", side="bottom", padx=0, pady=0)
        bottom_bar.pack_propagate(False)

        # Host Telemetry (Decoupled from network failover decisions)
        self.host_telemetry_lbl = ctk.CTkLabel(
            bottom_bar,
            text="Host Telemetry (Decoupled): CPU: --% | RAM: --%",
            font=("Consolas", 10),
            text_color=COCKPIT_THEME["text_muted"],
        )
        self.host_telemetry_lbl.pack(side="left", padx=20)

        # Right Footer with clickable author attribution (Section 6)
        footer_frame = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        footer_frame.pack(side="right", padx=20)

        author_btn = ctk.CTkButton(
            footer_frame,
            text="Crafted with ♥ by parikesitad-pm",
            font=("Segoe UI", 10, "underline"),
            text_color=COCKPIT_THEME["cyan"],
            fg_color="transparent",
            hover_color=COCKPIT_THEME["bg_surface"],
            height=24,
            command=self._open_author_link,
        )
        author_btn.pack(side="left", padx=(0, 10))

        tag_lbl = ctk.CTkLabel(
            footer_frame,
            text="A Modula Project · © 2026",
            font=("Segoe UI", 10),
            text_color=COCKPIT_THEME["text_muted"],
        )
        tag_lbl.pack(side="left")

    def _open_author_link(self):
        try:
            webbrowser.open_new_tab("https://github.com/parikesitad-pm")
        except Exception:
            pass

    def _on_workload_change(self, choice: str):
        profile_map = {
            "VIDEO_CONFERENCE": WorkloadProfile.VIDEO_CONFERENCE,
            "LIVE_STREAMING": WorkloadProfile.LIVE_STREAMING,
            "GENERAL": WorkloadProfile.GENERAL,
        }
        selected = profile_map.get(choice, WorkloadProfile.VIDEO_CONFERENCE)
        self.orchestrator.policy_engine.config.workload_profile = selected
        self.card_workload["val"].configure(text=choice)

    def _start_speed_test(self):
        provider = self.provider_menu.get()
        self.speed_readout_lbl.configure(text=f"Testing bandwidth via {provider.upper()}...")
        self.btn_run_test.configure(state="disabled")

        def _worker():
            res = self.speedtest_runner.run_single_test(provider)
            self.parent.after(0, lambda: self._on_speed_test_done(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_speed_test_done(self, res: SpeedTestResult):
        self.btn_run_test.configure(state="normal")
        self._latest_speedtest = res
        if res.error:
            self.speed_readout_lbl.configure(text=f"Test error: {res.error}")
        else:
            self.speed_readout_lbl.configure(
                text=f"Result ({res.provider}): DL: {res.download_mbps:.1f} Mbps | UL: {res.upload_mbps:.1f} Mbps | Ping: {res.latency_ms:.1f}ms"
            )

    def _start_bulk_test(self):
        self.speed_readout_lbl.configure(text="Running bulk benchmark across all 4 providers...")
        self.btn_bulk_test.configure(state="disabled")

        def _worker():
            results = self.speedtest_runner.run_bulk_tests()
            avg_dl = sum(r.download_mbps for r in results if not r.error) / max(1, len(results))
            self.parent.after(0, lambda: self._on_bulk_test_done(avg_dl, len(results)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_bulk_test_done(self, avg_dl: float, count: int):
        self.btn_bulk_test.configure(state="normal")
        self.speed_readout_lbl.configure(text=f"Bulk Complete ({count} providers): Avg DL: {avg_dl:.1f} Mbps")

    def _on_bus_event(self, event: FailoverEvent):
        if HAS_CTK:
            self.parent.after(0, lambda: self._render_event(event))

    def _render_event(self, event: FailoverEvent):
        # Prune older events if scroll frame exceeds 50 items
        children = self.events_scroll.winfo_children()
        if len(children) >= 50:
            children[0].destroy()

        color = COCKPIT_THEME["text_secondary"]
        severity = getattr(event, "severity", "INFO")
        if severity == "WARNING":
            color = COCKPIT_THEME["amber"]
        elif severity == "CRITICAL":
            color = COCKPIT_THEME["red"]
        elif severity == "INFO":
            color = COCKPIT_THEME["cyan"]

        ts = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        msg = f"[{ts}]  {event.event_type.value:<20}  {event.message}"
        lbl = ctk.CTkLabel(
            self.events_scroll,
            text=msg,
            font=("Consolas", 10),
            text_color=color,
            justify="left",
            anchor="w",
            wraplength=380,
        )
        lbl.pack(anchor="w", fill="x", pady=2)

    def _schedule_ui_tick(self):
        self._refresh_state()
        self.parent.after(200, self._schedule_ui_tick)

    def _refresh_state(self):
        if not HAS_CTK:
            return

        # 1. Update Active Path Pill & KPI Cards (Section 7 & 11)
        active_if = self.orchestrator.active_interface
        standby_if = None
        for iface in self.orchestrator.interfaces:
            if iface.state in (InterfaceState.READY, InterfaceState.ALERT):
                standby_if = iface
                break

        standby_name = standby_if.friendly_name if standby_if else "None"

        if active_if:
            media_icon = "📶" if active_if.media_type == InterfaceMediaType.WIFI else "⚡"
            self.active_pill.configure(
                text=f"{media_icon} ONLINE: {active_if.friendly_name}",
                text_color=COCKPIT_THEME["emerald"],
            )
            # Update KPI 1: RFC 3550 Latency / Jitter
            m = self.orchestrator.metrics.get(active_if.name)
            if m:
                rtt = getattr(m, "latency_ms", 0.0) or getattr(m, "smoothed_rtt_ms", 0.0)
                jit = getattr(m, "jitter_ms", 0.0) or getattr(m, "rfc3550_jitter_ms", 0.0)
                loss = getattr(m, "packet_loss_pct", 0.0)
                health = getattr(m, "health_index", 0)

                rtt_str = f"{rtt:.1f} ms" if rtt > 0 else "-- ms"
                jit_str = f"RFC 3550 Jitter: {jit:.2f} ms"
                self.card_rtt["val"].configure(text=rtt_str)
                self.card_rtt["sub"].configure(text=jit_str)

                # Update KPI 2: Network Health Index (Section 11)
                rating, rating_color = get_health_rating(health, True)
                self.card_health["val"].configure(text=f"{health} / 100 • {rating}", text_color=rating_color)
                self.card_health["sub"].configure(text=f"Active: {active_if.name} (Click for Details)")

                # Cache breakdown for details modal
                self._last_health_breakdown = {
                    "score": health,
                    "rating": rating,
                    "rtt": rtt,
                    "jitter": jit,
                    "loss": loss,
                    "active_name": active_if.friendly_name,
                    "standby_name": standby_name,
                    "timestamp": time.strftime("%H:%M:%S"),
                }
            else:
                self.card_rtt["val"].configure(text="Probing...")
                self.card_rtt["sub"].configure(text="Jitter: -- ms")
                self.card_health["val"].configure(text="-- / 100")
                self.card_health["sub"].configure(text=f"State: {active_if.state.name}")

            # Update KPI 4: Engine Status (Section 14: informative policy card)
            margin = getattr(self.orchestrator.config, "takeover_margin", 15.0)
            self.card_engine["val"].configure(text="ACTIVE PATH STABLE")
            self.card_engine["sub"].configure(
                text=f"Active: {active_if.name} | Standby: {standby_name} | Margin: {margin:.1f} pts"
            )
        else:
            self.active_pill.configure(
                text="⚠️ NO ACTIVE PATH",
                text_color=COCKPIT_THEME["red"],
            )
            self.card_rtt["val"].configure(text="-- ms")
            self.card_rtt["sub"].configure(text="Jitter: -- ms")
            self.card_health["val"].configure(text="0 / 100 • NO CONNECTION", text_color=COCKPIT_THEME["red"])
            self.card_health["sub"].configure(text="Status: OFFLINE")

            # Eliminate contradictory state
            self.card_engine["val"].configure(text="NO ELIGIBLE PATH")
            self.card_engine["sub"].configure(text="Waiting for usable interface")

        # 2. Update KPI 3: Workload
        active_apps = self.orchestrator.workload_watcher.scan_active_processes()
        if active_apps:
            self.card_workload["val"].configure(text="SESSION PROTECTED")
            self.card_workload["sub"].configure(text=f"Apps: {', '.join(active_apps)}")
        else:
            self.card_workload["val"].configure(text="PASSIVE MONITOR")
            self.card_workload["sub"].configure(text="Watching Zoom, OBS, Teams")

        # 3. Update Decoupled Host Telemetry
        device_health = self.orchestrator.latest_device_health
        if device_health:
            self.host_telemetry_lbl.configure(
                text=f"Host Telemetry (Decoupled): CPU: {device_health.cpu_percent:.1f}% | RAM: {device_health.ram_percent:.1f}% | Pressure: {device_health.pressure.upper()}"
            )

        # 4. Render Interfaces Deck
        self._render_interfaces_deck()

    def _render_interfaces_deck(self):
        interfaces = self.orchestrator.interfaces
        if not interfaces:
            if not self._placeholder_lbl:
                self._placeholder_lbl = ctk.CTkLabel(
                    self.interfaces_scroll,
                    text="Scanning for network interfaces...",
                    font=("Segoe UI", 11, "italic"),
                    text_color=COCKPIT_THEME["text_muted"],
                )
                self._placeholder_lbl.pack(pady=20)
            return

        if self._placeholder_lbl:
            self._placeholder_lbl.destroy()
            self._placeholder_lbl = None

        state_color_map = {
            InterfaceState.ONLINE: COCKPIT_THEME["state_online"],
            InterfaceState.READY: COCKPIT_THEME["state_ready"],
            InterfaceState.ALERT: COCKPIT_THEME["state_alert"],
            InterfaceState.OFFLINE: COCKPIT_THEME["state_offline"],
            InterfaceState.DISABLED: COCKPIT_THEME["state_disabled"],
        }

        current_ids = {iface.id for iface in interfaces}

        # Remove cards for vanished interfaces
        for iface_id in list(self._interface_cards.keys()):
            if iface_id not in current_ids:
                widgets = self._interface_cards.pop(iface_id)
                widgets["frame"].destroy()

        # Update existing cards or create new ones
        for iface in interfaces:
            # Section 8 & 9: Strictly avoid stale info on disconnected interfaces
            is_connected = iface.state in (InterfaceState.ONLINE, InterfaceState.READY, InterfaceState.ALERT)
            media_icon = "📶" if iface.media_type == InterfaceMediaType.WIFI else "⚡"
            if not is_connected:
                media_icon = "🔌"

            if iface.state == InterfaceState.DISABLED:
                details_str = "Disabled by operating system"
            elif iface.state == InterfaceState.OFFLINE:
                details_str = "Cable disconnected" if iface.media_type == InterfaceMediaType.ETHERNET else "No connection"
            else:
                details_parts = []
                if iface.ip_address:
                    details_parts.append(f"IPv4: {iface.ip_address}")
                if iface.gateway:
                    details_parts.append(f"GW: {iface.gateway}")
                if iface.ssid:
                    details_parts.append(f"SSID: {iface.ssid}")
                if iface.link_speed:
                    details_parts.append(f"({iface.link_speed})")
                m = self.orchestrator.metrics.get(iface.name)
                if m and getattr(m, "latency_ms", 0.0) > 0:
                    details_parts.append(f"[{m.latency_ms:.0f}ms / {m.jitter_ms:.1f}ms / {m.health_index}%]")
                details_str = " • ".join(details_parts) if details_parts else "Connected"

            color = state_color_map.get(iface.state, COCKPIT_THEME["text_muted"])

            if iface.id in self._interface_cards:
                widgets = self._interface_cards[iface.id]
                widgets["badge"].configure(text=iface.state.name, fg_color=color)
                widgets["name"].configure(text=f"{media_icon} {iface.friendly_name}")
                widgets["details"].configure(text=details_str)
                if iface.state == InterfaceState.DISABLED:
                    widgets["btn"].configure(
                        text="Enable",
                        font=("Segoe UI", 10, "bold"),
                        fg_color=COCKPIT_THEME["emerald"],
                        hover_color=COCKPIT_THEME["emerald_glow"],
                        command=lambda name=iface.name: self._confirm_enable_interface(name),
                    )
                else:
                    widgets["btn"].configure(
                        text="Disable",
                        font=("Segoe UI", 10),
                        fg_color=COCKPIT_THEME["bg_card"],
                        hover_color=COCKPIT_THEME["red"],
                        command=lambda name=iface.name: self._confirm_disable_interface(name),
                    )
            else:
                row = ctk.CTkFrame(
                    self.interfaces_scroll,
                    fg_color=COCKPIT_THEME["bg_surface"],
                    corner_radius=6,
                    border_width=1,
                    border_color=COCKPIT_THEME["border"],
                    height=56,
                )
                row.pack(fill="x", pady=4)
                row.pack_propagate(False)

                badge = ctk.CTkLabel(
                    row,
                    text=iface.state.name,
                    font=("Segoe UI", 10, "bold"),
                    text_color="#ffffff",
                    fg_color=color,
                    corner_radius=4,
                    padx=8,
                    pady=2,
                    width=64,
                )
                badge.pack(side="left", padx=(10, 8), pady=12)

                name_lbl = ctk.CTkLabel(
                    row,
                    text=f"{media_icon} {iface.friendly_name}",
                    font=("Segoe UI", 11, "bold"),
                    text_color=COCKPIT_THEME["text_primary"],
                )
                name_lbl.pack(side="left", padx=4)

                det_lbl = ctk.CTkLabel(
                    row,
                    text=details_str,
                    font=("Consolas", 10),
                    text_color=COCKPIT_THEME["text_muted"],
                )
                det_lbl.pack(side="left", padx=12)

                # Info / Details button opening interface modal
                info_btn = ctk.CTkButton(
                    row,
                    text="Details",
                    font=("Segoe UI", 10),
                    fg_color=COCKPIT_THEME["bg_card"],
                    hover_color=COCKPIT_THEME["border_highlight"],
                    width=54,
                    height=24,
                    command=lambda i=iface: self._show_interface_detail_modal(i),
                )
                info_btn.pack(side="right", padx=(4, 10))

                if iface.state == InterfaceState.DISABLED:
                    action_btn = ctk.CTkButton(
                        row,
                        text="Enable",
                        font=("Segoe UI", 10, "bold"),
                        fg_color=COCKPIT_THEME["emerald"],
                        hover_color=COCKPIT_THEME["emerald_glow"],
                        width=64,
                        height=24,
                        command=lambda name=iface.name: self._confirm_enable_interface(name),
                    )
                else:
                    action_btn = ctk.CTkButton(
                        row,
                        text="Disable",
                        font=("Segoe UI", 10),
                        fg_color=COCKPIT_THEME["bg_card"],
                        hover_color=COCKPIT_THEME["red"],
                        width=64,
                        height=24,
                        command=lambda name=iface.name: self._confirm_disable_interface(name),
                    )
                action_btn.pack(side="right", padx=4)

                self._interface_cards[iface.id] = {
                    "frame": row,
                    "badge": badge,
                    "name": name_lbl,
                    "details": det_lbl,
                    "btn": action_btn,
                    "info": info_btn,
                }

    def _show_health_detail_modal(self):
        """Opens interactive Network Health breakdown modal (Section 12)."""
        if not HAS_CTK:
            return
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Network Health Index Breakdown")
        dialog.geometry("480x380")
        dialog.configure(fg_color=COCKPIT_THEME["bg_dark"])
        dialog.transient(self.parent)
        dialog.grab_set()

        bd = self._last_health_breakdown
        score = bd.get("score", 0)
        rating = bd.get("rating", "UNKNOWN")
        rtt = bd.get("rtt", 0.0)
        jit = bd.get("jitter", 0.0)
        loss = bd.get("loss", 0.0)
        active_name = bd.get("active_name", "None")
        standby_name = bd.get("standby_name", "None")
        timestamp = bd.get("timestamp", "--:--:--")

        title_lbl = ctk.CTkLabel(
            dialog,
            text=f"NETWORK HEALTH: {score} / 100 ({rating})",
            font=("Segoe UI", 14, "bold"),
            text_color=COCKPIT_THEME["emerald"] if score >= 75 else COCKPIT_THEME["cyan"],
        )
        title_lbl.pack(pady=(18, 10))

        grid_frame = ctk.CTkFrame(dialog, fg_color=COCKPIT_THEME["bg_card"], corner_radius=6)
        grid_frame.pack(fill="both", expand=True, padx=20, pady=10)

        rows = [
            ("Latency (RTT):", f"{rtt:.1f} ms", "EXCELLENT" if rtt < 30 else ("GOOD" if rtt < 80 else "DEGRADED")),
            ("RFC 3550 Jitter:", f"{jit:.2f} ms", "EXCELLENT" if jit < 5 else ("GOOD" if jit < 15 else "DEGRADED")),
            ("Packet Loss:", f"{loss:.1f}%", "EXCELLENT" if loss == 0 else "DEGRADED"),
            ("Active Outbound Path:", active_name, "ONLINE"),
            ("Standby Candidate:", standby_name, "READY"),
            ("Last Health Evaluation:", timestamp, "STABLE"),
        ]

        for idx, (label, val, status) in enumerate(rows):
            r_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
            r_frame.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(r_frame, text=label, font=("Segoe UI", 11), text_color=COCKPIT_THEME["text_muted"]).pack(side="left")
            ctk.CTkLabel(r_frame, text=f"{val} ({status})", font=("Segoe UI", 11, "bold"), text_color=COCKPIT_THEME["text_primary"]).pack(side="right")

        desc_lbl = ctk.CTkLabel(
            dialog,
            text="Network Health summarizes the quality and stability of the active connection used by the AutoFailover Policy Engine.",
            font=("Segoe UI", 10, "italic"),
            text_color=COCKPIT_THEME["text_muted"],
            wraplength=440,
            justify="center",
        )
        desc_lbl.pack(pady=(4, 10))

        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            width=80,
        ).pack(pady=(0, 14))

    def _show_speedtest_detail_modal(self):
        """Opens interactive Speed Benchmark detail modal (Section 10)."""
        if not HAS_CTK:
            return
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Bandwidth & Speed Benchmark Details")
        dialog.geometry("460x340")
        dialog.configure(fg_color=COCKPIT_THEME["bg_dark"])
        dialog.transient(self.parent)
        dialog.grab_set()

        res = self._latest_speedtest

        title_lbl = ctk.CTkLabel(
            dialog,
            text="SPEED BENCHMARK RESULT",
            font=("Segoe UI", 14, "bold"),
            text_color=COCKPIT_THEME["cyan"],
        )
        title_lbl.pack(pady=(18, 10))

        content_frame = ctk.CTkFrame(dialog, fg_color=COCKPIT_THEME["bg_card"], corner_radius=6)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        active = self.orchestrator.active_interface
        active_str = active.friendly_name if active else "Default Route"

        if res:
            items = [
                ("Provider:", res.provider.upper()),
                ("Tested Interface:", active_str),
                ("Download Speed:", f"{res.download_mbps:.1f} Mbps"),
                ("Upload Speed:", f"{res.upload_mbps:.1f} Mbps"),
                ("Ping / Latency:", f"{res.latency_ms:.1f} ms"),
                ("Status:", "Success" if not res.error else f"Error: {res.error}"),
            ]
        else:
            items = [
                ("Provider:", self.provider_menu.get().upper()),
                ("Tested Interface:", active_str),
                ("Status:", "No benchmark run yet in this session"),
            ]

        for label, val in items:
            r_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            r_frame.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(r_frame, text=label, font=("Segoe UI", 11), text_color=COCKPIT_THEME["text_muted"]).pack(side="left")
            ctk.CTkLabel(r_frame, text=val, font=("Segoe UI", 11, "bold"), text_color=COCKPIT_THEME["text_primary"]).pack(side="right")

        note_lbl = ctk.CTkLabel(
            dialog,
            text="Note: Speed benchmarks are run on-demand and do not control failover decisions.",
            font=("Segoe UI", 10, "italic"),
            text_color=COCKPIT_THEME["text_muted"],
            wraplength=420,
            justify="center",
        )
        note_lbl.pack(pady=(4, 10))

        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            width=80,
        ).pack(pady=(0, 14))

    def _show_interface_detail_modal(self, iface: NetworkInterface):
        """Opens interactive technical details modal for selected interface."""
        if not HAS_CTK:
            return
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Interface Details - {iface.name}")
        dialog.geometry("480x360")
        dialog.configure(fg_color=COCKPIT_THEME["bg_dark"])
        dialog.transient(self.parent)
        dialog.grab_set()

        title_lbl = ctk.CTkLabel(
            dialog,
            text=f"{iface.friendly_name} [{iface.state.value}]",
            font=("Segoe UI", 14, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        title_lbl.pack(pady=(18, 10))

        content_frame = ctk.CTkFrame(dialog, fg_color=COCKPIT_THEME["bg_card"], corner_radius=6)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        m = self.orchestrator.metrics.get(iface.name)
        items = [
            ("Device Name:", iface.name),
            ("Media Type:", iface.media_type.value.upper()),
            ("Physical Carrier:", "CONNECTED" if iface.carrier else "DISCONNECTED"),
            ("Admin State:", "ENABLED" if iface.admin_enabled else "DISABLED"),
            ("Current State:", iface.state.value),
            ("IPv4 Address:", iface.ip_address or "N/A"),
            ("Default Gateway:", iface.gateway or "N/A"),
            ("Wi-Fi SSID:", iface.ssid or "N/A"),
            ("Link Speed:", iface.link_speed or "N/A"),
            ("Latency / Jitter:", f"{m.latency_ms:.1f}ms / {m.jitter_ms:.1f}ms" if m else "N/A"),
        ]

        for label, val in items:
            r_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            r_frame.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(r_frame, text=label, font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"]).pack(side="left")
            ctk.CTkLabel(r_frame, text=val, font=("Segoe UI", 10, "bold"), text_color=COCKPIT_THEME["text_primary"]).pack(side="right")

        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            width=80,
        ).pack(pady=(10, 14))

    def _confirm_enable_interface(self, iface_name: str):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Administrative Confirmation")
        dialog.geometry("440x180")
        dialog.configure(fg_color=COCKPIT_THEME["bg_dark"])
        dialog.transient(self.parent)
        dialog.grab_set()

        lbl = ctk.CTkLabel(
            dialog,
            text=f"'{iface_name}' is disabled.\nEnable it for automatic failover evaluation?",
            font=("Segoe UI", 12),
            text_color=COCKPIT_THEME["text_primary"],
            justify="center",
        )
        lbl.pack(pady=(24, 10))

        sub_lbl = ctk.CTkLabel(
            dialog,
            text="(Policy Engine will evaluate health before any route switch)",
            font=("Segoe UI", 10),
            text_color=COCKPIT_THEME["text_muted"],
        )
        sub_lbl.pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()

        def _do_enable():
            self.orchestrator.set_interface_admin_state(iface_name, True)
            dialog.destroy()

        def _do_cancel():
            dialog.destroy()

        btn_enable = ctk.CTkButton(
            btn_frame,
            text="Enable",
            command=_do_enable,
            fg_color=COCKPIT_THEME["emerald"],
            hover_color=COCKPIT_THEME["emerald_glow"],
            width=100,
        )
        btn_enable.pack(side="left", padx=8)

        btn_keep = ctk.CTkButton(
            btn_frame,
            text="Keep Disabled",
            command=_do_cancel,
            fg_color=COCKPIT_THEME["bg_card"],
            hover_color=COCKPIT_THEME["border_highlight"],
            width=110,
        )
        btn_keep.pack(side="left", padx=8)

    def _confirm_disable_interface(self, iface_name: str):
        self.orchestrator.set_interface_admin_state(iface_name, False)
