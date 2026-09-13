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
from ...models.snapshot import RuntimeSnapshot
from ...core.failover.orchestrator import FailoverOrchestrator
from ...core.policy.engine import PolicyEngine
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

        # Current Active Connection Header (Section 13: visually distinct active path container)
        self.active_box = ctk.CTkFrame(
            self.top_bar,
            fg_color=COCKPIT_THEME["bg_surface"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        self.active_box.pack(side="right", padx=20, pady=12)

        self.active_tag = ctk.CTkLabel(
            self.active_box,
            text="ACTIVE",
            font=("Segoe UI", 9, "bold"),
            text_color=COCKPIT_THEME["cyan"],
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=4,
            padx=7,
            pady=2,
        )
        self.active_tag.pack(side="left", padx=(8, 4), pady=6)

        self.active_title_lbl = ctk.CTkLabel(
            self.active_box,
            text="Scanning...",
            font=("Segoe UI", 12, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        self.active_title_lbl.pack(side="left", padx=6, pady=6)

        self.active_status_badge = ctk.CTkLabel(
            self.active_box,
            text="ONLINE",
            font=("Segoe UI", 9, "bold"),
            text_color="#ffffff",
            fg_color=COCKPIT_THEME["emerald"],
            corner_radius=4,
            padx=7,
            pady=2,
        )
        self.active_status_badge.pack(side="left", padx=(4, 8), pady=6)


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

        t0 = time.monotonic()
        snapshot = self.orchestrator.get_snapshot()
        if not snapshot:
            return

        active_if = snapshot.active_interface
        standby_if = snapshot.standby_interface
        standby_name = standby_if.friendly_name if standby_if else "None"

        # 1. Update Active Connection Header (Section 13)
        if active_if:
            media_icon = "📶" if active_if.media_type == InterfaceMediaType.WIFI else ("⚡" if active_if.media_type == InterfaceMediaType.ETHERNET else "🔌")
            if active_if.media_type == InterfaceMediaType.WIFI and active_if.ssid:
                title_str = f"{media_icon} {active_if.friendly_name} • {active_if.ssid}"
            else:
                title_str = f"{media_icon} {active_if.friendly_name} ({active_if.name})"

            self.active_tag.pack(side="left", padx=(8, 4), pady=6)
            self.active_title_lbl.configure(text=title_str, text_color=COCKPIT_THEME["text_primary"])
            self.active_status_badge.configure(text="ONLINE", fg_color=COCKPIT_THEME["state_online"])
            self.active_status_badge.pack(side="left", padx=(4, 8), pady=6)

            # Update KPI 1: RFC 3550 Latency / Jitter
            m = snapshot.metrics.get(active_if.name)
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
            margin = snapshot.takeover_margin
            self.card_engine["val"].configure(text="ACTIVE PATH STABLE")
            self.card_engine["sub"].configure(
                text=f"Active: {active_if.name} | Standby: {standby_name} | Margin: {margin:.1f} pts"
            )
        else:
            self.active_tag.pack_forget()
            self.active_title_lbl.configure(text="⚠️ NO ACTIVE CONNECTION", text_color=COCKPIT_THEME["red"])
            self.active_status_badge.configure(text="OFFLINE", fg_color=COCKPIT_THEME["state_offline"])
            self.active_status_badge.pack(side="left", padx=(4, 8), pady=6)

            self.card_rtt["val"].configure(text="-- ms")
            self.card_rtt["sub"].configure(text="Jitter: -- ms")
            self.card_health["val"].configure(text="0 / 100 • NO CONNECTION", text_color=COCKPIT_THEME["red"])
            self.card_health["sub"].configure(text="Status: OFFLINE")

            # Eliminate contradictory state
            self.card_engine["val"].configure(text="NO ELIGIBLE PATH")
            self.card_engine["sub"].configure(text="Waiting for usable interface")

        # 2. Update KPI 3: Workload (From background snapshot — zero UI thread process scanning)
        active_apps = snapshot.workload_apps
        if active_apps:
            self.card_workload["val"].configure(text="SESSION PROTECTED")
            self.card_workload["sub"].configure(text=f"Apps: {', '.join(active_apps)}")
        else:
            self.card_workload["val"].configure(text="PASSIVE MONITOR")
            self.card_workload["sub"].configure(text="Watching Zoom, OBS, Teams")

        # 3. Update Decoupled Host Telemetry & Subprocess Instrumentation
        device_health = snapshot.device_health
        ui_refresh_ms = (time.monotonic() - t0) * 1000.0
        if device_health:
            sub_info = f" | Subprocesses: {snapshot.subprocess_count_per_min}/min | UI Tick: {ui_refresh_ms:.1f}ms"
            self.host_telemetry_lbl.configure(
                text=f"Host Telemetry (Decoupled): CPU: {device_health.cpu_percent:.1f}% | RAM: {device_health.ram_percent:.1f}% | Pressure: {device_health.pressure.upper()}{sub_info}"
            )

        # 4. Render Interfaces Deck from snapshot
        self._render_interfaces_deck(snapshot)


    def _render_interfaces_deck(self, snapshot: RuntimeSnapshot):
        interfaces = snapshot.interfaces
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

        role_info_map = {
            InterfaceState.ONLINE: ("● ACTIVE CONNECTION", COCKPIT_THEME["emerald"], "Designated primary outbound route"),
            InterfaceState.READY: ("○ FAILOVER STANDBY", COCKPIT_THEME["cyan"], "Healthy candidate ready for failover takeover"),
            InterfaceState.ALERT: ("▲ DEGRADED", COCKPIT_THEME["amber"], "Experiencing elevated latency, jitter or packet loss"),
            InterfaceState.OFFLINE: ("✕ DISCONNECTED", COCKPIT_THEME["text_muted"], "No physical link carrier detected"),
            InterfaceState.DISABLED: ("⛔ DISABLED", COCKPIT_THEME["text_muted"], "Disabled at operating system level"),
        }

        current_ids = {iface.id for iface in interfaces}

        # Remove cards for vanished interfaces
        for iface_id in list(self._interface_cards.keys()):
            if iface_id not in current_ids:
                widgets = self._interface_cards.pop(iface_id)
                widgets["card"].destroy()

        # Update existing cards or create new ones
        for iface in interfaces:
            is_connected = iface.state in (InterfaceState.ONLINE, InterfaceState.READY, InterfaceState.ALERT)
            media_icon = "📶" if iface.media_type == InterfaceMediaType.WIFI else ("⚡" if iface.media_type == InterfaceMediaType.ETHERNET else "🔌")
            badge_color = state_color_map.get(iface.state, COCKPIT_THEME["text_muted"])
            role_title, role_color, role_subtext = role_info_map.get(
                iface.state,
                ("STANDBY", COCKPIT_THEME["text_muted"], "Auxiliary interface")
            )
            border_color = COCKPIT_THEME["border_highlight"] if iface.state == InterfaceState.ONLINE else COCKPIT_THEME["border"]

            m = snapshot.metrics.get(iface.name)
            lat_str = f"{m.latency_ms:.1f} ms" if (m and getattr(m, "latency_ms", 0.0) > 0) else "-- ms"
            jit_str = f"{m.jitter_ms:.2f} ms" if (m and getattr(m, "jitter_ms", 0.0) > 0) else "-- ms"
            health_score = m.health_index if m else 0
            rating_str, _ = get_health_rating(health_score, is_connected)
            health_display = f"{health_score} · {rating_str}" if (is_connected and health_score > 0) else "--"

            if iface.state == InterfaceState.DISABLED:
                offline_text = "Disabled by operating system"
            elif iface.state == InterfaceState.OFFLINE:
                offline_text = "Cable disconnected" if iface.media_type == InterfaceMediaType.ETHERNET else "No connection"
            else:
                offline_text = ""

            if iface.id in self._interface_cards:
                w = self._interface_cards[iface.id]
                w["card"].configure(border_color=border_color)
                w["badge"].configure(text=iface.state.name, fg_color=badge_color)
                w["role"].configure(text=role_title, text_color=role_color)
                w["name"].configure(text=f"{media_icon} {iface.friendly_name}")
                w["sys_id"].configure(text=iface.name)
                w["role_desc"].configure(text=role_subtext)

                if is_connected:
                    w["offline_lbl"].pack_forget()
                    w["grid"].pack(fill="x", padx=14, pady=(4, 8), after=w["top_row"])
                    w["kv_ipv4"].configure(text=iface.ip_address or "--")
                    w["kv_gw"].configure(text=iface.gateway or "--")
                    if iface.media_type == InterfaceMediaType.WIFI:
                        w["kv_extra_k"].configure(text="SSID")
                        w["kv_extra_v"].configure(text=iface.ssid or "--")
                    else:
                        w["kv_extra_k"].configure(text="Netmask")
                        w["kv_extra_v"].configure(text=iface.netmask or "--")
                    w["kv_link"].configure(text=iface.link_speed or "--")
                    w["kv_lat"].configure(text=lat_str)
                    w["kv_health"].configure(text=health_display)
                else:
                    w["grid"].pack_forget()
                    w["offline_lbl"].configure(text=offline_text)
                    w["offline_lbl"].pack(fill="x", padx=14, pady=10, after=w["top_row"])

                if iface.state == InterfaceState.DISABLED:
                    w["btn"].configure(
                        text="Enable",
                        font=("Segoe UI", 10, "bold"),
                        fg_color=COCKPIT_THEME["emerald"],
                        hover_color=COCKPIT_THEME["emerald_glow"],
                        command=lambda name=iface.name: self._confirm_enable_interface(name),
                    )
                else:
                    w["btn"].configure(
                        text="Disable",
                        font=("Segoe UI", 10),
                        fg_color=COCKPIT_THEME["bg_card"],
                        hover_color=COCKPIT_THEME["red"],
                        command=lambda name=iface.name: self._confirm_disable_interface(name),
                    )
            else:
                card = ctk.CTkFrame(
                    self.interfaces_scroll,
                    fg_color=COCKPIT_THEME["bg_surface"],
                    corner_radius=8,
                    border_width=1,
                    border_color=border_color,
                )
                card.pack(fill="x", pady=6, padx=4)

                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=14, pady=(12, 6))

                left_box = ctk.CTkFrame(top_row, fg_color="transparent")
                left_box.pack(side="left")

                name_lbl = ctk.CTkLabel(
                    left_box,
                    text=f"{media_icon} {iface.friendly_name}",
                    font=("Segoe UI", 13, "bold"),
                    text_color=COCKPIT_THEME["text_primary"],
                    anchor="w",
                )
                name_lbl.pack(anchor="w")

                sys_id_lbl = ctk.CTkLabel(
                    left_box,
                    text=iface.name,
                    font=("Consolas", 10),
                    text_color=COCKPIT_THEME["text_muted"],
                    anchor="w",
                )
                sys_id_lbl.pack(anchor="w")

                right_box = ctk.CTkFrame(top_row, fg_color="transparent")
                right_box.pack(side="right")

                badge_lbl = ctk.CTkLabel(
                    right_box,
                    text=iface.state.name,
                    font=("Segoe UI", 10, "bold"),
                    text_color="#ffffff",
                    fg_color=badge_color,
                    corner_radius=4,
                    padx=8,
                    pady=2,
                )
                badge_lbl.pack(anchor="e")

                role_lbl = ctk.CTkLabel(
                    right_box,
                    text=role_title,
                    font=("Segoe UI", 9, "bold"),
                    text_color=role_color,
                    anchor="e",
                )
                role_lbl.pack(anchor="e", pady=(3, 0))

                grid_frame = ctk.CTkFrame(card, fg_color=COCKPIT_THEME["bg_card"], corner_radius=6)
                grid_frame.columnconfigure(0, weight=1)
                grid_frame.columnconfigure(1, weight=1)

                col0 = ctk.CTkFrame(grid_frame, fg_color="transparent")
                col0.grid(row=0, column=0, sticky="nsew", padx=10, pady=6)

                r0 = ctk.CTkFrame(col0, fg_color="transparent")
                r0.pack(fill="x", pady=2)
                ctk.CTkLabel(r0, text="IPv4", font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"], width=56, anchor="w").pack(side="left")
                kv_ipv4 = ctk.CTkLabel(r0, text=iface.ip_address or "--", font=("Consolas", 10, "bold"), text_color=COCKPIT_THEME["text_primary"], anchor="w")
                kv_ipv4.pack(side="left", padx=4)

                r1 = ctk.CTkFrame(col0, fg_color="transparent")
                r1.pack(fill="x", pady=2)
                ctk.CTkLabel(r1, text="Gateway", font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"], width=56, anchor="w").pack(side="left")
                kv_gw = ctk.CTkLabel(r1, text=iface.gateway or "--", font=("Consolas", 10), text_color=COCKPIT_THEME["text_primary"], anchor="w")
                kv_gw.pack(side="left", padx=4)

                r2 = ctk.CTkFrame(col0, fg_color="transparent")
                r2.pack(fill="x", pady=2)
                extra_k = "SSID" if iface.media_type == InterfaceMediaType.WIFI else "Netmask"
                extra_v = iface.ssid if iface.media_type == InterfaceMediaType.WIFI else (iface.netmask or "--")
                kv_extra_k = ctk.CTkLabel(r2, text=extra_k, font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"], width=56, anchor="w")
                kv_extra_k.pack(side="left")
                kv_extra_v = ctk.CTkLabel(r2, text=extra_v or "--", font=("Segoe UI", 10), text_color=COCKPIT_THEME["cyan"], anchor="w")
                kv_extra_v.pack(side="left", padx=4)

                col1 = ctk.CTkFrame(grid_frame, fg_color="transparent")
                col1.grid(row=0, column=1, sticky="nsew", padx=10, pady=6)

                r3 = ctk.CTkFrame(col1, fg_color="transparent")
                r3.pack(fill="x", pady=2)
                ctk.CTkLabel(r3, text="Link", font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"], width=56, anchor="w").pack(side="left")
                kv_link = ctk.CTkLabel(r3, text=iface.link_speed or "--", font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_primary"], anchor="w")
                kv_link.pack(side="left", padx=4)

                r4 = ctk.CTkFrame(col1, fg_color="transparent")
                r4.pack(fill="x", pady=2)
                ctk.CTkLabel(r4, text="Latency", font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"], width=56, anchor="w").pack(side="left")
                kv_lat = ctk.CTkLabel(r4, text=lat_str, font=("Segoe UI", 10, "bold"), text_color=COCKPIT_THEME["text_primary"], anchor="w")
                kv_lat.pack(side="left", padx=4)

                r5 = ctk.CTkFrame(col1, fg_color="transparent")
                r5.pack(fill="x", pady=2)
                ctk.CTkLabel(r5, text="Health", font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"], width=56, anchor="w").pack(side="left")
                kv_health = ctk.CTkLabel(r5, text=health_display, font=("Segoe UI", 10, "bold"), text_color=COCKPIT_THEME["emerald"], anchor="w")
                kv_health.pack(side="left", padx=4)

                offline_lbl = ctk.CTkLabel(
                    card,
                    text=offline_text,
                    font=("Segoe UI", 11, "italic"),
                    text_color=COCKPIT_THEME["text_muted"],
                    fg_color=COCKPIT_THEME["bg_card"],
                    corner_radius=6,
                    pady=8,
                )

                if is_connected:
                    grid_frame.pack(fill="x", padx=14, pady=(4, 8))
                else:
                    offline_lbl.pack(fill="x", padx=14, pady=(4, 8))

                bottom_row = ctk.CTkFrame(card, fg_color="transparent")
                bottom_row.pack(fill="x", padx=14, pady=(4, 12))

                role_desc_lbl = ctk.CTkLabel(
                    bottom_row,
                    text=role_subtext,
                    font=("Segoe UI", 10),
                    text_color=COCKPIT_THEME["text_muted"],
                    anchor="w",
                )
                role_desc_lbl.pack(side="left")

                details_btn = ctk.CTkButton(
                    bottom_row,
                    text="Details →",
                    font=("Segoe UI", 10, "bold"),
                    fg_color=COCKPIT_THEME["bg_card"],
                    hover_color=COCKPIT_THEME["border_highlight"],
                    width=78,
                    height=26,
                    command=lambda i=iface: self._show_interface_detail_modal(i),
                )
                details_btn.pack(side="right", padx=(6, 0))

                if iface.state == InterfaceState.DISABLED:
                    action_btn = ctk.CTkButton(
                        bottom_row,
                        text="Enable",
                        font=("Segoe UI", 10, "bold"),
                        fg_color=COCKPIT_THEME["emerald"],
                        hover_color=COCKPIT_THEME["emerald_glow"],
                        width=68,
                        height=26,
                        command=lambda name=iface.name: self._confirm_enable_interface(name),
                    )
                else:
                    action_btn = ctk.CTkButton(
                        bottom_row,
                        text="Disable",
                        font=("Segoe UI", 10),
                        fg_color=COCKPIT_THEME["bg_card"],
                        hover_color=COCKPIT_THEME["red"],
                        width=68,
                        height=26,
                        command=lambda name=iface.name: self._confirm_disable_interface(name),
                    )
                action_btn.pack(side="right")

                card.bind("<Button-1>", lambda e, i=iface: self._show_interface_detail_modal(i))

                self._interface_cards[iface.id] = {
                    "card": card,
                    "top_row": top_row,
                    "badge": badge_lbl,
                    "role": role_lbl,
                    "name": name_lbl,
                    "sys_id": sys_id_lbl,
                    "grid": grid_frame,
                    "offline_lbl": offline_lbl,
                    "kv_ipv4": kv_ipv4,
                    "kv_gw": kv_gw,
                    "kv_extra_k": kv_extra_k,
                    "kv_extra_v": kv_extra_v,
                    "kv_link": kv_link,
                    "kv_lat": kv_lat,
                    "kv_health": kv_health,
                    "role_desc": role_desc_lbl,
                    "btn": action_btn,
                    "details_btn": details_btn,
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
        """Opens comprehensive technical details modal (Section 10)."""
        if not HAS_CTK:
            return
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Interface Details — {iface.friendly_name}")
        dialog.geometry("540x530")
        dialog.configure(fg_color=COCKPIT_THEME["bg_dark"])
        dialog.transient(self.parent)
        dialog.grab_set()

        # Top Header
        title_box = ctk.CTkFrame(dialog, fg_color="transparent")
        title_box.pack(fill="x", padx=20, pady=(16, 8))

        media_icon = "📶" if iface.media_type == InterfaceMediaType.WIFI else ("⚡" if iface.media_type == InterfaceMediaType.ETHERNET else "🔌")
        ctk.CTkLabel(
            title_box,
            text=f"{media_icon} {iface.friendly_name}",
            font=("Segoe UI", 15, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            title_box,
            text=iface.state.value,
            font=("Segoe UI", 10, "bold"),
            text_color="#ffffff",
            fg_color=COCKPIT_THEME.get(f"state_{iface.state.value.lower()}", COCKPIT_THEME["cyan"]),
            corner_radius=4,
            padx=8,
            pady=2,
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        def _add_section(title: str, items: List[Tuple[str, str]]):
            s_frame = ctk.CTkFrame(scroll, fg_color=COCKPIT_THEME["bg_card"], corner_radius=6)
            s_frame.pack(fill="x", pady=6)

            h_lbl = ctk.CTkLabel(
                s_frame,
                text=title,
                font=("Segoe UI", 11, "bold"),
                text_color=COCKPIT_THEME["cyan"],
                anchor="w",
            )
            h_lbl.pack(anchor="w", padx=14, pady=(10, 6))

            for label, val in items:
                r = ctk.CTkFrame(s_frame, fg_color="transparent")
                r.pack(fill="x", padx=14, pady=3)
                ctk.CTkLabel(r, text=label, font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"]).pack(side="left")
                ctk.CTkLabel(r, text=val, font=("Consolas", 10, "bold"), text_color=COCKPIT_THEME["text_primary"]).pack(side="right")
            s_frame.pack_configure(pady=(4, 6))

        # 1. GENERAL
        role_label = "ACTIVE OUTBOUND CONNECTION" if iface.state == InterfaceState.ONLINE else ("FAILOVER STANDBY CANDIDATE" if iface.state == InterfaceState.READY else iface.state.value)
        _add_section("GENERAL & IDENTITY", [
            ("Device Name:", iface.name),
            ("Friendly Name:", iface.friendly_name),
            ("Media Type:", iface.media_type.value.upper()),
            ("Assigned Role:", role_label),
            ("Physical Carrier:", "CONNECTED" if iface.carrier else "DISCONNECTED"),
            ("Admin State:", "ENABLED" if iface.admin_enabled else "DISABLED"),
        ])

        # 2. NETWORK
        _add_section("NETWORK CONFIGURATION", [
            ("IPv4 Address:", iface.ip_address or "None"),
            ("Netmask / Prefix:", iface.netmask or "None"),
            ("Default Gateway:", iface.gateway or "None"),
            ("Wi-Fi SSID:", iface.ssid or ("N/A (Wired)" if iface.media_type == InterfaceMediaType.ETHERNET else "None")),
            ("Link Speed:", iface.link_speed or "Unknown"),
        ])

        # 3. QUALITY (RFC 3550)
        m = self.orchestrator.metrics.get(iface.name)
        if m:
            rtt = getattr(m, "latency_ms", 0.0)
            jit = getattr(m, "jitter_ms", 0.0)
            loss = getattr(m, "packet_loss_pct", 0.0)
            health = getattr(m, "health_index", 0)
            rating, _ = get_health_rating(health, iface.carrier)
            score_val = PolicyEngine.compute_score(iface, self.orchestrator.config)
            _add_section("QUALITY & PERFORMANCE (RFC 3550)", [
                ("Latency (RTT):", f"{rtt:.1f} ms" if rtt > 0 else "-- ms"),
                ("RFC 3550 Jitter:", f"{jit:.2f} ms" if jit > 0 else "-- ms"),
                ("Packet Loss:", f"{loss:.1f}%"),
                ("Network Health Index:", f"{health} / 100 ({rating})"),
                ("Policy Candidate Score:", f"{score_val:.1f} pts"),
            ])

        # 4. POLICY & ARBITRATION
        is_eligible = iface.is_eligible_candidate(self.orchestrator.config.min_health_threshold)
        last_probe_str = time.strftime("%H:%M:%S", time.localtime(m.last_probe_timestamp)) if (m and m.last_probe_timestamp > 0) else "Never"
        _add_section("POLICY & FAILOVER ARBITRATION", [
            ("Failover Eligibility:", "ELIGIBLE FOR PROMOTION" if is_eligible else "INELIGIBLE"),
            ("Takeover Margin Threshold:", f"{self.orchestrator.config.takeover_margin:.1f} pts"),
            ("Last Health Probe:", last_probe_str),
        ])

        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            width=90,
            height=28,
        ).pack(pady=(6, 12))


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
