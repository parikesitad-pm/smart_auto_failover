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

        # Navigation and view state
        self._current_tab = "overview"
        self._tab_buttons: Dict[str, Any] = {}
        self._tab_frames: Dict[str, Any] = {}

        # Interface card registries
        self._overview_interface_cards: Dict[str, Dict[str, Any]] = {}
        self._full_interface_cards: Dict[str, Dict[str, Any]] = {}
        self._placeholder_overview_lbl: Optional[Any] = None
        self._placeholder_full_lbl: Optional[Any] = None
        self._show_inactive = False

        # State tracking for notification toasts
        self._prev_interface_states: Dict[str, InterfaceState] = {}
        self._notif_timer_id: Optional[str] = None

        # Speed test & event state
        self._latest_speedtest: Optional[SpeedTestResult] = None
        self._speedtest_history: List[SpeedTestResult] = []
        self._last_health_breakdown: Dict[str, Any] = {}
        self._all_events: List[FailoverEvent] = []
        self._event_filter_severity = "ALL"
        self._is_active: bool = True
        self._ui_tick_id: Optional[str] = None

        if not HAS_CTK:
            return

        self.root_frame = ctk.CTkFrame(self.parent, fg_color=COCKPIT_THEME["bg_dark"])
        self.root_frame.pack(fill="both", expand=True)

        self._build_top_bar()
        self._build_nav_bar()
        self._build_notification_banner()
        self._build_tab_views()
        self._build_bottom_status()

        # Activate default view
        self._switch_tab("overview")

        # Subscribe to orchestrator event bus and replay history
        bus = getattr(self.orchestrator, "event_bus", None) or getattr(self.orchestrator, "bus", None)
        if bus:
            bus.subscribe(self._on_bus_event)
            if hasattr(bus, "get_history"):
                for ev in bus.get_history(limit=30):
                    self._process_event(ev)
            elif hasattr(bus, "get_recent_events"):
                for ev in reversed(bus.get_recent_events(limit=30)):
                    self._process_event(ev)

        # Start periodic UI polling ticker (5 Hz)
        self._schedule_ui_tick()

    # =========================================================================
    # TOP BAR & HEADER
    # =========================================================================

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

        # Brand / Title (AutoFailover 3.0 by Modula)
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

        # Current Active Connection Header
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

    # =========================================================================
    # NAVIGATION BAR
    # =========================================================================

    def _build_nav_bar(self):
        self.nav_bar = ctk.CTkFrame(self.root_frame, fg_color="transparent", height=42)
        self.nav_bar.pack(fill="x", padx=20, pady=(10, 4))

        tabs = [
            ("overview", "Overview"),
            ("interfaces", "Interfaces"),
            ("speedtest", "Speed Test"),
            ("events", "Events"),
        ]

        for tab_id, tab_label in tabs:
            btn = ctk.CTkButton(
                self.nav_bar,
                text=tab_label,
                font=("Segoe UI", 11, "bold"),
                fg_color=COCKPIT_THEME["bg_card"],
                hover_color=COCKPIT_THEME["border_highlight"],
                text_color=COCKPIT_THEME["text_secondary"],
                height=30,
                width=100,
                corner_radius=6,
                command=lambda t=tab_id: self._switch_tab(t),
            )
            btn.pack(side="left", padx=(0, 8))
            self._tab_buttons[tab_id] = btn

    def _switch_tab(self, tab_name: str):
        self._current_tab = tab_name
        for t_name, btn in self._tab_buttons.items():
            if t_name == tab_name:
                btn.configure(
                    fg_color=COCKPIT_THEME["cyan"],
                    text_color="#080b10",
                )
                if t_name in self._tab_frames:
                    self._tab_frames[t_name].pack(fill="both", expand=True, padx=20, pady=0)
            else:
                btn.configure(
                    fg_color=COCKPIT_THEME["bg_card"],
                    text_color=COCKPIT_THEME["text_secondary"],
                )
                if t_name in self._tab_frames:
                    self._tab_frames[t_name].pack_forget()

    # =========================================================================
    # NOTIFICATION BANNER / TOAST
    # =========================================================================

    def _build_notification_banner(self):
        self.notif_banner = ctk.CTkFrame(
            self.root_frame,
            fg_color=COCKPIT_THEME["bg_card"],
            border_width=1,
            border_color=COCKPIT_THEME["cyan"],
            corner_radius=8,
            height=40,
        )
        # Not packed initially

        self.notif_icon = ctk.CTkLabel(
            self.notif_banner,
            text="ℹ️",
            font=("Segoe UI", 12),
        )
        self.notif_icon.pack(side="left", padx=(14, 6), pady=6)

        self.notif_text_lbl = ctk.CTkLabel(
            self.notif_banner,
            text="",
            font=("Segoe UI", 11),
            text_color=COCKPIT_THEME["text_primary"],
        )
        self.notif_text_lbl.pack(side="left", padx=4, pady=6)

        self.notif_action_btn = ctk.CTkButton(
            self.notif_banner,
            text="View Interfaces →",
            font=("Segoe UI", 10, "bold"),
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            text_color=COCKPIT_THEME["cyan"],
            height=24,
            width=120,
            command=lambda: self._switch_tab("interfaces"),
        )
        self.notif_action_btn.pack(side="left", padx=10, pady=6)

        self.notif_dismiss_btn = ctk.CTkButton(
            self.notif_banner,
            text="✕",
            font=("Segoe UI", 10),
            fg_color="transparent",
            hover_color=COCKPIT_THEME["bg_surface"],
            text_color=COCKPIT_THEME["text_muted"],
            height=24,
            width=24,
            command=self._dismiss_notification,
        )
        self.notif_dismiss_btn.pack(side="right", padx=10, pady=6)

    def _show_notification(self, message: str, is_alert: bool = False):
        if not HAS_CTK:
            return
        border_color = COCKPIT_THEME["amber"] if is_alert else COCKPIT_THEME["cyan"]
        self.notif_icon.configure(text="⚠️" if is_alert else "ℹ️")
        self.notif_banner.configure(border_color=border_color)
        self.notif_text_lbl.configure(text=message)
        self.notif_banner.pack(fill="x", padx=20, pady=(2, 8), before=self.tab_container)

        if self._notif_timer_id:
            try:
                self.parent.after_cancel(self._notif_timer_id)
            except Exception:
                pass
        self._notif_timer_id = self.parent.after(9000, self._dismiss_notification)

    def _dismiss_notification(self):
        try:
            self.notif_banner.pack_forget()
        except Exception:
            pass
        self._notif_timer_id = None

    # =========================================================================
    # TAB VIEWS SETUP
    # =========================================================================

    def _build_tab_views(self):
        self.tab_container = ctk.CTkFrame(self.root_frame, fg_color="transparent")
        self.tab_container.pack(fill="both", expand=True, padx=0, pady=0)

        # 1. Overview Tab
        tab_overview = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self._tab_frames["overview"] = tab_overview
        self._build_overview_tab(tab_overview)

        # 2. Interfaces Tab
        tab_interfaces = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self._tab_frames["interfaces"] = tab_interfaces
        self._build_interfaces_tab(tab_interfaces)

        # 3. Speed Test Tab
        tab_speedtest = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self._tab_frames["speedtest"] = tab_speedtest
        self._build_speedtest_tab(tab_speedtest)

        # 4. Events Tab
        tab_events = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self._tab_frames["events"] = tab_events
        self._build_events_tab(tab_events)

    # =========================================================================
    # OVERVIEW TAB
    # =========================================================================

    def _build_overview_tab(self, parent: Any):
        # 4 KPI Cards
        self._build_kpi_cards(parent)

        # Main Split
        overview_split = ctk.CTkFrame(parent, fg_color="transparent")
        overview_split.pack(fill="both", expand=True, padx=0, pady=0)

        overview_split.columnconfigure(0, weight=3)
        overview_split.columnconfigure(1, weight=2)
        overview_split.rowconfigure(0, weight=1)

        # Left Column: Active & Standby Interfaces Deck
        left_frame = ctk.CTkFrame(
            overview_split,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        left_frame.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        # Deck Header with toggle
        deck_header = ctk.CTkFrame(left_frame, fg_color="transparent")
        deck_header.pack(fill="x", padx=16, pady=(12, 6))

        deck_title = ctk.CTkLabel(
            deck_header,
            text="NETWORK INTERFACES DECK",
            font=("Segoe UI", 12, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        deck_title.pack(side="left")

        self.inactive_toggle = ctk.CTkCheckBox(
            deck_header,
            text="Show Inactive",
            font=("Segoe UI", 10),
            text_color=COCKPIT_THEME["text_muted"],
            checkmark_color="#000000",
            fg_color=COCKPIT_THEME["cyan"],
            hover_color=COCKPIT_THEME["border_highlight"],
            command=self._on_toggle_inactive,
            height=20,
        )
        self.inactive_toggle.pack(side="right")

        self.overview_interfaces_scroll = ctk.CTkScrollableFrame(
            left_frame,
            fg_color="transparent",
            scrollbar_button_color=COCKPIT_THEME["border"],
        )
        self.overview_interfaces_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Right Column: Quick Speed Benchmark + Recent Activity
        right_frame = ctk.CTkFrame(overview_split, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        right_frame.rowconfigure(0, weight=2)
        right_frame.rowconfigure(1, weight=3)
        right_frame.columnconfigure(0, weight=1)

        # 1. Quick Speed Benchmark Card
        self._build_overview_speedtest_panel(right_frame)

        # 2. Recent Activity Card
        self._build_overview_events_panel(right_frame)

    def _on_toggle_inactive(self):
        self._show_inactive = bool(self.inactive_toggle.get())
        snapshot = self.orchestrator.get_snapshot()
        if snapshot:
            self._render_overview_deck(snapshot)

    def _build_kpi_cards(self, parent: Any):
        kpi_container = ctk.CTkFrame(parent, fg_color="transparent", height=96)
        kpi_container.pack(fill="x", padx=0, pady=(6, 12))

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
        frame.grid(row=0, column=col, padx=5, sticky="nsew")
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

    def _build_overview_speedtest_panel(self, parent: Any):
        frame = ctk.CTkFrame(
            parent,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        frame.grid(row=0, column=0, pady=(0, 8), sticky="nsew")

        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 4))

        st_title = ctk.CTkLabel(
            top_row,
            text="BANDWIDTH BENCHMARK",
            font=("Segoe UI", 12, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        st_title.pack(side="left")

        btn_open = ctk.CTkButton(
            top_row,
            text="Open Speed Test View →",
            command=lambda: self._switch_tab("speedtest"),
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent",
            hover_color=COCKPIT_THEME["bg_surface"],
            text_color=COCKPIT_THEME["cyan"],
            height=22,
        )
        btn_open.pack(side="right")

        # Readout text
        self.overview_speed_lbl = ctk.CTkLabel(
            frame,
            text="Ready to benchmark active connection (does not alter failover)",
            font=("Consolas", 10),
            text_color=COCKPIT_THEME["text_muted"],
            anchor="w",
        )
        self.overview_speed_lbl.pack(fill="x", padx=16, pady=(4, 6))

        # Action bar
        act_row = ctk.CTkFrame(frame, fg_color="transparent")
        act_row.pack(fill="x", padx=16, pady=(2, 10))

        self.btn_overview_test = ctk.CTkButton(
            act_row,
            text="Run Quick Test",
            command=self._start_speed_test,
            font=("Segoe UI", 10, "bold"),
            fg_color=COCKPIT_THEME["emerald"],
            hover_color=COCKPIT_THEME["emerald_glow"],
            height=26,
            width=110,
        )
        self.btn_overview_test.pack(side="left", padx=(0, 6))

        self.btn_overview_details = ctk.CTkButton(
            act_row,
            text="Details",
            command=self._show_speedtest_detail_modal,
            font=("Segoe UI", 10),
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            height=26,
            width=70,
        )
        self.btn_overview_details.pack(side="left")

    def _build_overview_events_panel(self, parent: Any):
        frame = ctk.CTkFrame(
            parent,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        frame.grid(row=1, column=0, pady=(8, 0), sticky="nsew")

        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 6))

        ev_title = ctk.CTkLabel(
            top_row,
            text="RECENT ACTIVITY",
            font=("Segoe UI", 12, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        ev_title.pack(side="left")

        btn_all_events = ctk.CTkButton(
            top_row,
            text="View All Events →",
            command=lambda: self._switch_tab("events"),
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent",
            hover_color=COCKPIT_THEME["bg_surface"],
            text_color=COCKPIT_THEME["cyan"],
            height=22,
        )
        btn_all_events.pack(side="right")

        self.overview_events_scroll = ctk.CTkScrollableFrame(
            frame,
            fg_color="transparent",
            scrollbar_button_color=COCKPIT_THEME["border"],
        )
        self.overview_events_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # =========================================================================
    # INTERFACES TAB (ALL HARDWARE)
    # =========================================================================

    def _build_interfaces_tab(self, parent: Any):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=0, pady=(12, 8))

        title = ctk.CTkLabel(
            header_frame,
            text="ALL NETWORK HARDWARE & ADAPTERS",
            font=("Segoe UI", 14, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Operating system interface registry monitored by AutoFailover 3.0 runtime",
            font=("Segoe UI", 11),
            text_color=COCKPIT_THEME["text_muted"],
        )
        subtitle.pack(anchor="w")

        self.full_interfaces_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
            scrollbar_button_color=COCKPIT_THEME["border"],
        )
        self.full_interfaces_scroll.pack(fill="both", expand=True, padx=0, pady=6)

    # =========================================================================
    # SPEED TEST TAB
    # =========================================================================

    def _build_speedtest_tab(self, parent: Any):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=0, pady=(12, 8))

        title = ctk.CTkLabel(
            header_frame,
            text="BANDWIDTH & SPEED BENCHMARK",
            font=("Segoe UI", 14, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Passive on-demand throughput measurement across real-time providers (isolated from failover decisions)",
            font=("Segoe UI", 11),
            text_color=COCKPIT_THEME["text_muted"],
        )
        subtitle.pack(anchor="w")

        card = ctk.CTkFrame(
            parent,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
        )
        card.pack(fill="both", expand=True, padx=0, pady=6)

        # Control row
        ctrl_frame = ctk.CTkFrame(card, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            ctrl_frame,
            text="Provider:",
            font=("Segoe UI", 11, "bold"),
            text_color=COCKPIT_THEME["text_muted"],
        ).pack(side="left", padx=(0, 6))

        self.provider_menu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=["Cloudflare", "FAST.com", "Ookla Speedtest", "nPerf"],
            fg_color=COCKPIT_THEME["bg_surface"],
            button_color=COCKPIT_THEME["border_highlight"],
            text_color=COCKPIT_THEME["cyan"],
            font=("Segoe UI", 11),
            width=135,
            height=30,
        )
        self.provider_menu.set("Cloudflare")
        self.provider_menu.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            ctrl_frame,
            text="Interface:",
            font=("Segoe UI", 11, "bold"),
            text_color=COCKPIT_THEME["text_muted"],
        ).pack(side="left", padx=(4, 6))

        self.speedtest_iface_menu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=["Active Outbound (Default)"],
            fg_color=COCKPIT_THEME["bg_surface"],
            button_color=COCKPIT_THEME["border_highlight"],
            text_color=COCKPIT_THEME["text_primary"],
            font=("Segoe UI", 11),
            width=175,
            height=30,
        )
        self.speedtest_iface_menu.set("Active Outbound (Default)")
        self.speedtest_iface_menu.pack(side="left", padx=(0, 10))

        self.btn_run_test = ctk.CTkButton(
            ctrl_frame,
            text="Run Speed Test",
            command=self._start_speed_test,
            font=("Segoe UI", 11, "bold"),
            fg_color=COCKPIT_THEME["emerald"],
            hover_color=COCKPIT_THEME["emerald_glow"],
            height=30,
            width=120,
        )
        self.btn_run_test.pack(side="left", padx=3)

        self.btn_bulk_test = ctk.CTkButton(
            ctrl_frame,
            text="Bulk Test (All 4)",
            command=self._start_bulk_test,
            font=("Segoe UI", 11),
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            height=30,
            width=130,
        )
        self.btn_bulk_test.pack(side="left", padx=3)

        self.btn_cancel_speedtest = ctk.CTkButton(
            ctrl_frame,
            text="Cancel",
            command=self._cancel_speed_test,
            font=("Segoe UI", 11),
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["red"],
            text_color=COCKPIT_THEME["text_muted"],
            height=30,
            width=70,
            state="disabled",
        )
        self.btn_cancel_speedtest.pack(side="left", padx=3)

        self.btn_clear_speedtest = ctk.CTkButton(
            ctrl_frame,
            text="Clear",
            command=self._clear_speedtest_history,
            font=("Segoe UI", 11),
            fg_color="transparent",
            hover_color=COCKPIT_THEME["bg_surface"],
            text_color=COCKPIT_THEME["text_muted"],
            height=30,
            width=60,
        )
        self.btn_clear_speedtest.pack(side="left", padx=3)

        # Status & Progress banner
        self.speed_status_frame = ctk.CTkFrame(card, fg_color=COCKPIT_THEME["bg_surface"], corner_radius=6)
        self.speed_status_frame.pack(fill="x", padx=16, pady=(4, 8))

        self.speed_readout_lbl = ctk.CTkLabel(
            self.speed_status_frame,
            text="Ready to benchmark active connection (passive measurement; does not alter failover decisions)",
            font=("Consolas", 11),
            text_color=COCKPIT_THEME["text_secondary"],
            anchor="w",
            padx=12,
            pady=8,
        )
        self.speed_readout_lbl.pack(fill="x")

        # Gauges Frame (4 gauges)
        gauges_frame = ctk.CTkFrame(card, fg_color="transparent")
        gauges_frame.pack(fill="x", padx=16, pady=(0, 8))

        for col in range(4):
            gauges_frame.columnconfigure(col, weight=1, uniform="speed_gauges")

        self.gauge_dl = self._create_card(gauges_frame, 0, "DOWNLOAD SPEED", "-- Mbps", "Ready")
        self.gauge_ul = self._create_card(gauges_frame, 1, "UPLOAD SPEED", "-- Mbps", "Ready")
        self.gauge_ping = self._create_card(gauges_frame, 2, "SERVER PING", "-- ms", "Ready")
        self.gauge_jitter = self._create_card(gauges_frame, 3, "RFC 3550 JITTER", "-- ms", "Ready")

        # Results History Table Container
        hist_header = ctk.CTkFrame(card, fg_color="transparent")
        hist_header.pack(fill="x", padx=16, pady=(4, 2))

        ctk.CTkLabel(
            hist_header,
            text="BENCHMARK HISTORY & AUDIT TRAIL",
            font=("Segoe UI", 11, "bold"),
            text_color=COCKPIT_THEME["text_muted"],
        ).pack(side="left")

        # Table Column Headers
        tbl_hdr_frame = ctk.CTkFrame(card, fg_color=COCKPIT_THEME["bg_surface"], height=28, corner_radius=4)
        tbl_hdr_frame.pack(fill="x", padx=16, pady=(0, 2))
        tbl_hdr_frame.pack_propagate(False)

        headers = [
            ("PROVIDER", 110, "w"),
            ("INTERFACE", 130, "w"),
            ("DOWNLOAD", 95, "e"),
            ("UPLOAD", 95, "e"),
            ("PING", 75, "e"),
            ("JITTER", 75, "e"),
            ("STATUS", 100, "center"),
            ("DETAILS", 80, "center"),
        ]
        for title_text, col_width, align in headers:
            col_lbl = ctk.CTkLabel(
                tbl_hdr_frame,
                text=title_text,
                font=("Segoe UI", 10, "bold"),
                text_color=COCKPIT_THEME["text_muted"],
                width=col_width,
                anchor=align,
            )
            col_lbl.pack(side="left", padx=4)

        # Scrollable table body
        self.speedtest_history_scroll = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            scrollbar_button_color=COCKPIT_THEME["border"],
        )
        self.speedtest_history_scroll.pack(fill="both", expand=True, padx=16, pady=(2, 10))

        self.speedtest_placeholder = ctk.CTkLabel(
            self.speedtest_history_scroll,
            text="No speed benchmarks run yet in this session. Select a provider and click Run Speed Test.",
            font=("Segoe UI", 11, "italic"),
            text_color=COCKPIT_THEME["text_muted"],
            pady=24,
        )
        self.speedtest_placeholder.pack()

    # =========================================================================
    # EVENTS TAB
    # =========================================================================

    def _build_events_tab(self, parent: Any):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=0, pady=(12, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="SYSTEM & FAILOVER EVENTS",
            font=("Segoe UI", 14, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        title.pack(anchor="w")

        # Filter bar
        filter_bar = ctk.CTkFrame(parent, fg_color="transparent")
        filter_bar.pack(fill="x", padx=0, pady=(0, 10))

        ctk.CTkLabel(
            filter_bar,
            text="Filter:",
            font=("Segoe UI", 11, "bold"),
            text_color=COCKPIT_THEME["text_muted"],
        ).pack(side="left", padx=(0, 8))

        self._filter_btns = {}
        for sev in ["ALL", "CRITICAL", "WARNING", "INFO"]:
            b = ctk.CTkButton(
                filter_bar,
                text=sev,
                font=("Segoe UI", 10, "bold"),
                fg_color=COCKPIT_THEME["cyan"] if sev == "ALL" else COCKPIT_THEME["bg_card"],
                text_color="#080b10" if sev == "ALL" else COCKPIT_THEME["text_secondary"],
                hover_color=COCKPIT_THEME["border_highlight"],
                height=26,
                width=65,
                command=lambda s=sev: self._set_events_filter(s),
            )
            b.pack(side="left", padx=3)
            self._filter_btns[sev] = b

        self.btn_clear_events = ctk.CTkButton(
            filter_bar,
            text="Clear Log",
            font=("Segoe UI", 10),
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["red"],
            height=26,
            width=80,
            command=self._clear_events_log,
        )
        self.btn_clear_events.pack(side="right")

        self.full_events_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
            scrollbar_button_color=COCKPIT_THEME["border"],
        )
        self.full_events_scroll.pack(fill="both", expand=True, padx=0, pady=6)

    def _set_events_filter(self, severity: str):
        self._event_filter_severity = severity
        for s, b in self._filter_btns.items():
            if s == severity:
                b.configure(fg_color=COCKPIT_THEME["cyan"], text_color="#080b10")
            else:
                b.configure(fg_color=COCKPIT_THEME["bg_card"], text_color=COCKPIT_THEME["text_secondary"])

        # Re-render full events list
        for child in self.full_events_scroll.winfo_children():
            child.destroy()
        for ev in self._all_events:
            self._render_single_event_to_scroll(self.full_events_scroll, ev, check_filter=True)

    def _clear_events_log(self):
        self._all_events.clear()
        for child in self.full_events_scroll.winfo_children():
            child.destroy()
        for child in self.overview_events_scroll.winfo_children():
            child.destroy()

    # =========================================================================
    # BOTTOM STATUS BAR
    # =========================================================================

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

        # Right Footer with clickable author attribution
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

    # =========================================================================
    # WORKLOAD & SPEED TEST LOGIC
    # =========================================================================

    def _on_workload_change(self, choice: str):
        profile_map = {
            "VIDEO_CONFERENCE": WorkloadProfile.VIDEO_CONFERENCE,
            "LIVE_STREAMING": WorkloadProfile.LIVE_STREAMING,
            "GENERAL": WorkloadProfile.GENERAL,
        }
        selected = profile_map.get(choice, WorkloadProfile.VIDEO_CONFERENCE)
        self.orchestrator.policy_engine.config.workload_profile = selected
        self.card_workload["val"].configure(text=choice)

    def _cancel_speed_test(self):
        self.speedtest_runner.cancel()
        self.speed_readout_lbl.configure(text="Cancelling speed benchmark... please wait for current request to abort.")
        if hasattr(self, "btn_cancel_speedtest"):
            self.btn_cancel_speedtest.configure(state="disabled", text_color=COCKPIT_THEME["text_muted"])

    def _clear_speedtest_history(self):
        self._speedtest_history.clear()
        if hasattr(self, "speedtest_history_scroll"):
            for child in self.speedtest_history_scroll.winfo_children():
                child.destroy()
            self.speedtest_placeholder = ctk.CTkLabel(
                self.speedtest_history_scroll,
                text="No speed benchmarks run yet in this session. Select a provider and click Run Speed Test.",
                font=("Segoe UI", 11, "italic"),
                text_color=COCKPIT_THEME["text_muted"],
                pady=24,
            )
            self.speedtest_placeholder.pack()

    def _start_speed_test(self):
        provider_choice = self.provider_menu.get() if hasattr(self, "provider_menu") else "Cloudflare"
        provider_map = {
            "Cloudflare": "cloudflare",
            "FAST.com": "fast",
            "Ookla Speedtest": "ookla",
            "nPerf": "nperf",
            "cloudflare": "cloudflare",
            "fast_com": "fast",
            "ookla": "ookla",
            "nperf": "nperf",
        }
        provider_key = provider_map.get(provider_choice, provider_choice.lower().replace(".com", ""))

        target_iface_id = "default"
        source_ip = None
        iface_choice = self.speedtest_iface_menu.get() if hasattr(self, "speedtest_iface_menu") else "Active Outbound (Default)"

        snapshot = self.orchestrator.get_snapshot() if hasattr(self.orchestrator, "get_snapshot") else None
        if snapshot and iface_choice != "Active Outbound (Default)":
            for iface in snapshot.interfaces:
                if iface.friendly_name in iface_choice or iface.name in iface_choice:
                    target_iface_id = iface.id
                    source_ip = iface.ip_address
                    break

        msg = f"Testing bandwidth via {provider_choice.upper()} on {iface_choice}..."
        self.speed_readout_lbl.configure(text=msg)
        self.overview_speed_lbl.configure(text=msg)

        if hasattr(self, "btn_run_test"):
            self.btn_run_test.configure(state="disabled")
        if hasattr(self, "btn_bulk_test"):
            self.btn_bulk_test.configure(state="disabled")
        if hasattr(self, "btn_overview_test"):
            self.btn_overview_test.configure(state="disabled")
        if hasattr(self, "btn_cancel_speedtest"):
            self.btn_cancel_speedtest.configure(state="normal", text_color=COCKPIT_THEME["red"])

        def _worker():
            res = self.speedtest_runner.run_single_test(
                provider_name=provider_key,
                interface_id=target_iface_id,
                source_ip=source_ip,
            )
            self.parent.after(0, lambda: self._on_speed_test_done(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_speed_test_done(self, res: SpeedTestResult):
        if hasattr(self, "btn_run_test"):
            self.btn_run_test.configure(state="normal")
        if hasattr(self, "btn_bulk_test"):
            self.btn_bulk_test.configure(state="normal")
        if hasattr(self, "btn_overview_test"):
            self.btn_overview_test.configure(state="normal")
        if hasattr(self, "btn_cancel_speedtest"):
            self.btn_cancel_speedtest.configure(state="disabled", text_color=COCKPIT_THEME["text_muted"])

        self._latest_speedtest = res
        self._add_speedtest_result_row(res)

        if res.status == "SUCCESS":
            txt = (
                f"Result ({res.provider}): DL: {res.download_mbps:.1f} Mbps | "
                f"UL: {res.upload_mbps:.1f} Mbps | Ping: {res.latency_ms:.1f} ms | Jitter: {res.jitter_ms:.1f} ms"
            )
            self.gauge_dl["val"].configure(text=f"{res.download_mbps:.1f} Mbps")
            self.gauge_dl["sub"].configure(text=f"Provider: {res.provider.upper()}")

            self.gauge_ul["val"].configure(text=f"{res.upload_mbps:.1f} Mbps")
            self.gauge_ul["sub"].configure(text=f"Provider: {res.provider.upper()}")

            self.gauge_ping["val"].configure(text=f"{res.latency_ms:.1f} ms")
            self.gauge_ping["sub"].configure(text="Server Ping")

            if hasattr(self, "gauge_jitter"):
                self.gauge_jitter["val"].configure(text=f"{res.jitter_ms:.1f} ms")
                self.gauge_jitter["sub"].configure(text="RFC 3550")
        elif res.status == "UNAVAILABLE":
            txt = f"{res.provider.upper()} unavailable: {res.error}"
            self.gauge_dl["val"].configure(text="N/A")
            self.gauge_dl["sub"].configure(text="Unavailable")
            self.gauge_ul["val"].configure(text="N/A")
            self.gauge_ul["sub"].configure(text="Unavailable")
        elif res.status == "CANCELLED":
            txt = f"{res.provider.upper()} test cancelled."
        else:
            txt = f"Test error ({res.provider}): {res.error}"
            self.gauge_dl["val"].configure(text="ERR")
            self.gauge_dl["sub"].configure(text="Failed")

        self.speed_readout_lbl.configure(text=txt)
        self.overview_speed_lbl.configure(text=txt)

    def _start_bulk_test(self):
        target_iface_id = "default"
        source_ip = None
        iface_choice = self.speedtest_iface_menu.get() if hasattr(self, "speedtest_iface_menu") else "Active Outbound (Default)"

        snapshot = self.orchestrator.get_snapshot() if hasattr(self.orchestrator, "get_snapshot") else None
        if snapshot and iface_choice != "Active Outbound (Default)":
            for iface in snapshot.interfaces:
                if iface.friendly_name in iface_choice or iface.name in iface_choice:
                    target_iface_id = iface.id
                    source_ip = iface.ip_address
                    break

        msg = f"Starting bulk benchmark across 4 providers on {iface_choice}..."
        self.speed_readout_lbl.configure(text=msg)
        self.overview_speed_lbl.configure(text=msg)

        if hasattr(self, "btn_run_test"):
            self.btn_run_test.configure(state="disabled")
        if hasattr(self, "btn_bulk_test"):
            self.btn_bulk_test.configure(state="disabled")
        if hasattr(self, "btn_overview_test"):
            self.btn_overview_test.configure(state="disabled")
        if hasattr(self, "btn_cancel_speedtest"):
            self.btn_cancel_speedtest.configure(state="normal", text_color=COCKPIT_THEME["red"])

        statuses = {
            "cloudflare": "QUEUED",
            "fast": "QUEUED",
            "ookla": "QUEUED",
            "nperf": "QUEUED",
        }

        def _on_progress(idx: int, total: int, key: str, status: str, result: Optional[SpeedTestResult]):
            statuses[key] = status
            progress_msg = (
                f"Bulk Test {idx}/{total}: "
                f"Cloudflare [{statuses['cloudflare']}] | "
                f"FAST.com [{statuses['fast']}] | "
                f"Ookla [{statuses['ookla']}] | "
                f"nPerf [{statuses['nperf']}]"
            )
            def _apply_ui():
                self.speed_readout_lbl.configure(text=progress_msg)
                self.overview_speed_lbl.configure(text=progress_msg)
                if result:
                    self._add_speedtest_result_row(result)
                    if result.status == "SUCCESS":
                        self.gauge_dl["val"].configure(text=f"{result.download_mbps:.1f} Mbps")
                        self.gauge_dl["sub"].configure(text=f"Provider: {result.provider.upper()}")
                        self.gauge_ul["val"].configure(text=f"{result.upload_mbps:.1f} Mbps")
                        self.gauge_ul["sub"].configure(text=f"Provider: {result.provider.upper()}")
                        self.gauge_ping["val"].configure(text=f"{result.latency_ms:.1f} ms")
                        if hasattr(self, "gauge_jitter"):
                            self.gauge_jitter["val"].configure(text=f"{result.jitter_ms:.1f} ms")

            self.parent.after(0, _apply_ui)

        def _worker():
            results = self.speedtest_runner.run_bulk_tests(
                interface_id=target_iface_id,
                source_ip=source_ip,
                on_progress=_on_progress,
            )
            self.parent.after(0, lambda: self._on_bulk_test_done(results))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_bulk_test_done(self, results: List[SpeedTestResult]):
        if hasattr(self, "btn_run_test"):
            self.btn_run_test.configure(state="normal")
        if hasattr(self, "btn_bulk_test"):
            self.btn_bulk_test.configure(state="normal")
        if hasattr(self, "btn_overview_test"):
            self.btn_overview_test.configure(state="normal")
        if hasattr(self, "btn_cancel_speedtest"):
            self.btn_cancel_speedtest.configure(state="disabled", text_color=COCKPIT_THEME["text_muted"])

        successful = [r for r in results if r.status == "SUCCESS"]
        if successful:
            avg_dl = sum(r.download_mbps for r in successful) / len(successful)
            avg_ul = sum(r.upload_mbps for r in successful) / len(successful)
            avg_ping = sum(r.latency_ms for r in successful) / len(successful)
            txt = (
                f"Bulk Complete: {len(successful)}/{len(results)} passed | "
                f"Avg DL: {avg_dl:.1f} Mbps | Avg UL: {avg_ul:.1f} Mbps | Avg Ping: {avg_ping:.1f} ms"
            )
            self.gauge_dl["val"].configure(text=f"{avg_dl:.1f} Mbps")
            self.gauge_dl["sub"].configure(text=f"Bulk Avg ({len(successful)} providers)")
            self.gauge_ul["val"].configure(text=f"{avg_ul:.1f} Mbps")
            self.gauge_ul["sub"].configure(text="Bulk Avg")
            self.gauge_ping["val"].configure(text=f"{avg_ping:.1f} ms")
            self.gauge_ping["sub"].configure(text="Bulk Avg")
        else:
            txt = f"Bulk benchmark finished: {len(results)} executed (check audit table below)"

        self.speed_readout_lbl.configure(text=txt)
        self.overview_speed_lbl.configure(text=txt)

    def _add_speedtest_result_row(self, res: SpeedTestResult):
        self._speedtest_history.insert(0, res)
        if len(self._speedtest_history) > 50:
            self._speedtest_history = self._speedtest_history[:50]

        if not hasattr(self, "speedtest_history_scroll"):
            return

        # Clear placeholder if it exists
        if hasattr(self, "speedtest_placeholder") and self.speedtest_placeholder.winfo_exists():
            self.speedtest_placeholder.destroy()

        row_frame = ctk.CTkFrame(
            self.speedtest_history_scroll,
            fg_color=COCKPIT_THEME["bg_surface"],
            height=30,
            corner_radius=4,
        )
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)

        prov_lbl = ctk.CTkLabel(
            row_frame,
            text=res.provider.upper(),
            font=("Segoe UI", 10, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
            width=110,
            anchor="w",
        )
        prov_lbl.pack(side="left", padx=4)

        iface_name = res.interface if res.interface != "default" else "Active (Default)"
        iface_lbl = ctk.CTkLabel(
            row_frame,
            text=iface_name[:18],
            font=("Segoe UI", 10),
            text_color=COCKPIT_THEME["text_muted"],
            width=130,
            anchor="w",
        )
        iface_lbl.pack(side="left", padx=4)

        dl_str = f"{res.download_mbps:.1f} Mbps" if res.status == "SUCCESS" else "--"
        dl_lbl = ctk.CTkLabel(
            row_frame,
            text=dl_str,
            font=("Consolas", 10, "bold"),
            text_color=COCKPIT_THEME["emerald"] if res.status == "SUCCESS" else COCKPIT_THEME["text_muted"],
            width=95,
            anchor="e",
        )
        dl_lbl.pack(side="left", padx=4)

        ul_str = f"{res.upload_mbps:.1f} Mbps" if res.status == "SUCCESS" else "--"
        ul_lbl = ctk.CTkLabel(
            row_frame,
            text=ul_str,
            font=("Consolas", 10),
            text_color=COCKPIT_THEME["text_primary"] if res.status == "SUCCESS" else COCKPIT_THEME["text_muted"],
            width=95,
            anchor="e",
        )
        ul_lbl.pack(side="left", padx=4)

        ping_str = f"{res.latency_ms:.1f} ms" if res.status == "SUCCESS" else "--"
        ping_lbl = ctk.CTkLabel(
            row_frame,
            text=ping_str,
            font=("Consolas", 10),
            text_color=COCKPIT_THEME["cyan"] if res.status == "SUCCESS" else COCKPIT_THEME["text_muted"],
            width=75,
            anchor="e",
        )
        ping_lbl.pack(side="left", padx=4)

        jit_str = f"{res.jitter_ms:.1f} ms" if res.status == "SUCCESS" else "--"
        jit_lbl = ctk.CTkLabel(
            row_frame,
            text=jit_str,
            font=("Consolas", 10),
            text_color=COCKPIT_THEME["text_secondary"] if res.status == "SUCCESS" else COCKPIT_THEME["text_muted"],
            width=75,
            anchor="e",
        )
        jit_lbl.pack(side="left", padx=4)

        status_colors = {
            "SUCCESS": COCKPIT_THEME["emerald"],
            "FAILED": COCKPIT_THEME["red"],
            "UNAVAILABLE": COCKPIT_THEME["amber"],
            "CANCELLED": COCKPIT_THEME["text_muted"],
            "RUNNING": COCKPIT_THEME["cyan"],
        }
        st_color = status_colors.get(res.status, COCKPIT_THEME["text_muted"])
        st_lbl = ctk.CTkLabel(
            row_frame,
            text=res.status,
            font=("Segoe UI", 9, "bold"),
            text_color=st_color,
            width=100,
            anchor="center",
        )
        st_lbl.pack(side="left", padx=4)

        btn_det = ctk.CTkButton(
            row_frame,
            text="Details",
            command=lambda r=res: self._show_speedtest_detail_modal(r),
            font=("Segoe UI", 10),
            fg_color=COCKPIT_THEME["bg_card"],
            hover_color=COCKPIT_THEME["border_highlight"],
            width=70,
            height=22,
        )
        btn_det.pack(side="left", padx=4)

    # =========================================================================
    # EVENT DISPATCH & RENDERING
    # =========================================================================

    def _on_bus_event(self, event: FailoverEvent):
        if HAS_CTK:
            self.parent.after(0, lambda: self._process_event(event))

    def _process_event(self, event: FailoverEvent):
        self._all_events.append(event)
        # Keep internal history bounded
        if len(self._all_events) > 200:
            self._all_events.pop(0)

        # 1. Render to Overview Recent Activity
        self._render_single_event_to_scroll(self.overview_events_scroll, event, max_items=6)

        # 2. Render to Full Events Tab (if matches filter)
        self._render_single_event_to_scroll(self.full_events_scroll, event, max_items=100, check_filter=True)

    def _render_single_event_to_scroll(
        self,
        scroll_container: Any,
        event: FailoverEvent,
        max_items: int = 100,
        check_filter: bool = False,
    ):
        severity = getattr(event, "severity", "INFO")

        if check_filter and self._event_filter_severity != "ALL":
            if severity != self._event_filter_severity:
                return

        children = scroll_container.winfo_children()
        if len(children) >= max_items:
            children[0].destroy()

        color = COCKPIT_THEME["text_secondary"]
        if severity == "WARNING":
            color = COCKPIT_THEME["amber"]
        elif severity == "CRITICAL":
            color = COCKPIT_THEME["red"]
        elif severity == "INFO":
            color = COCKPIT_THEME["cyan"]

        ts = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        msg = f"[{ts}]  {event.event_type.value:<20}  {event.message}"
        lbl = ctk.CTkLabel(
            scroll_container,
            text=msg,
            font=("Consolas", 10),
            text_color=color,
            justify="left",
            anchor="w",
            wraplength=480,
        )
        lbl.pack(anchor="w", fill="x", pady=2)

    # =========================================================================
    # RUNTIME STATE REFRESH TICKER (5 HZ)
    # =========================================================================

    def _schedule_ui_tick(self):
        if not getattr(self, "_is_active", True):
            return
        self._refresh_state()
        if getattr(self, "_is_active", True):
            self._ui_tick_id = self.parent.after(200, self._schedule_ui_tick)

    def stop(self):
        """
        Gracefully terminates all scheduled tickers, toast timers, and background tasks.
        """
        self._is_active = False
        if self._ui_tick_id:
            try:
                self.parent.after_cancel(self._ui_tick_id)
            except Exception:
                pass
            self._ui_tick_id = None

        if hasattr(self, "_notif_timer_id") and self._notif_timer_id:
            try:
                self.parent.after_cancel(self._notif_timer_id)
            except Exception:
                pass
            self._notif_timer_id = None

        if hasattr(self, "speedtest_runner") and self.speedtest_runner:
            try:
                self.speedtest_runner.cancel()
            except Exception:
                pass

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

        # Dynamically sync speedtest interface dropdown if interfaces changed
        if hasattr(self, "speedtest_iface_menu") and snapshot.interfaces:
            avail_ifaces = ["Active Outbound (Default)"] + [
                f"{i.friendly_name} ({i.name})" for i in snapshot.interfaces if i.carrier or i.admin_enabled
            ]
            if getattr(self, "_cached_speedtest_ifaces", None) != avail_ifaces:
                self._cached_speedtest_ifaces = avail_ifaces
                curr_sel = self.speedtest_iface_menu.get()
                self.speedtest_iface_menu.configure(values=avail_ifaces)
                if curr_sel not in avail_ifaces:
                    self.speedtest_iface_menu.set("Active Outbound (Default)")

        # 1. Update Active Connection Header
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

                # Update KPI 2: Network Health Index
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

            # Update KPI 4: Engine Status
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

            self.card_engine["val"].configure(text="NO ELIGIBLE PATH")
            self.card_engine["sub"].configure(text="Waiting for usable interface")

        # 2. Update KPI 3: Workload
        active_apps = snapshot.workload_apps
        if active_apps:
            self.card_workload["val"].configure(text="SESSION PROTECTED")
            self.card_workload["sub"].configure(text=f"Apps: {', '.join(active_apps)}")
        else:
            self.card_workload["val"].configure(text="PASSIVE MONITOR")
            self.card_workload["sub"].configure(text="Watching Zoom, OBS, Teams")

        # 3. Update Decoupled Host Telemetry
        device_health = snapshot.device_health
        ui_refresh_ms = (time.monotonic() - t0) * 1000.0
        if device_health:
            sub_info = f" | Subprocesses: {snapshot.subprocess_count_per_min}/min | UI Tick: {ui_refresh_ms:.1f}ms"
            self.host_telemetry_lbl.configure(
                text=f"Host Telemetry (Decoupled): CPU: {device_health.cpu_percent:.1f}% | RAM: {device_health.ram_percent:.1f}% | Pressure: {device_health.pressure.upper()}{sub_info}"
            )

        # 4. Check interface state transitions for toast notifications
        self._check_interface_state_changes(snapshot.interfaces)

        # 5. Render Overview & Full Interface decks
        self._render_overview_deck(snapshot)
        self._render_full_deck(snapshot)

    # =========================================================================
    # STATE TRANSITIONS & TOAST NOTIFICATION
    # =========================================================================

    def _check_interface_state_changes(self, interfaces: List[NetworkInterface]):
        for iface in interfaces:
            prev = self._prev_interface_states.get(iface.id)
            curr = iface.state

            if prev is not None and prev != curr:
                # Connected / recovered
                if curr in (InterfaceState.ONLINE, InterfaceState.READY) and prev in (InterfaceState.OFFLINE, InterfaceState.DISABLED):
                    self._show_notification(
                        f"Connection available: {iface.friendly_name} is now {curr.name} for automatic failover.",
                        is_alert=False,
                    )
                # Disconnected / failed
                elif curr == InterfaceState.OFFLINE and prev in (InterfaceState.ONLINE, InterfaceState.READY, InterfaceState.ALERT):
                    self._show_notification(
                        f"Connection lost: {iface.friendly_name} was disconnected.",
                        is_alert=True,
                    )
                # Degraded
                elif curr == InterfaceState.ALERT and prev in (InterfaceState.ONLINE, InterfaceState.READY):
                    self._show_notification(
                        f"Degradation detected: {iface.friendly_name} is experiencing packet loss / high jitter.",
                        is_alert=True,
                    )

            self._prev_interface_states[iface.id] = curr

    # =========================================================================
    # INTERFACE DECK RENDERING
    # =========================================================================

    def _render_overview_deck(self, snapshot: RuntimeSnapshot):
        interfaces = snapshot.interfaces

        # Filter for Overview: show connected/active/ready/alert, or all if toggled
        if self._show_inactive:
            filtered = interfaces
        else:
            filtered = [
                i for i in interfaces
                if i.state in (InterfaceState.ONLINE, InterfaceState.READY, InterfaceState.ALERT)
            ]
            # If no connected interfaces, show whatever exists so it's not totally empty
            if not filtered:
                filtered = interfaces

        self._render_deck_into_container(
            container=self.overview_interfaces_scroll,
            cards_map=self._overview_interface_cards,
            interfaces=filtered,
            snapshot=snapshot,
        )

    def _render_full_deck(self, snapshot: RuntimeSnapshot):
        # Full deck shows all interfaces
        self._render_deck_into_container(
            container=self.full_interfaces_scroll,
            cards_map=self._full_interface_cards,
            interfaces=snapshot.interfaces,
            snapshot=snapshot,
        )

    def _render_deck_into_container(
        self,
        container: Any,
        cards_map: Dict[str, Dict[str, Any]],
        interfaces: List[NetworkInterface],
        snapshot: RuntimeSnapshot,
    ):
        if not interfaces:
            return

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

        # Remove vanished cards
        for iface_id in list(cards_map.keys()):
            if iface_id not in current_ids:
                widgets = cards_map.pop(iface_id)
                try:
                    widgets["card"].destroy()
                except Exception:
                    pass

        # Update or create cards
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

            if iface.id in cards_map:
                w = cards_map[iface.id]
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
                    container,
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

                cards_map[iface.id] = {
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

    # =========================================================================
    # MODALS & ADMINISTRATIVE ACTIONS
    # =========================================================================

    def _show_health_detail_modal(self):
        """Opens interactive Network Health breakdown modal."""
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

    def _show_speedtest_detail_modal(self, target_result: Optional[SpeedTestResult] = None):
        """Opens interactive Speed Benchmark detail modal."""
        if not HAS_CTK:
            return
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Bandwidth & Speed Benchmark Details")
        dialog.geometry("520x460")
        dialog.configure(fg_color=COCKPIT_THEME["bg_dark"])
        dialog.transient(self.parent)
        dialog.grab_set()

        res = target_result if target_result is not None else self._latest_speedtest

        title_lbl = ctk.CTkLabel(
            dialog,
            text="BANDWIDTH & SPEED BENCHMARK AUDIT",
            font=("Segoe UI", 13, "bold"),
            text_color=COCKPIT_THEME["cyan"],
        )
        title_lbl.pack(pady=(16, 8))

        content_frame = ctk.CTkFrame(dialog, fg_color=COCKPIT_THEME["bg_card"], corner_radius=6)
        content_frame.pack(fill="both", expand=True, padx=16, pady=8)

        active = self.orchestrator.active_interface
        active_str = active.friendly_name if active else "Default Outbound Route"

        if res:
            ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(res.timestamp)) if res.timestamp else "N/A"
            dur_str = f"{res.duration:.2f} s" if res.duration > 0 else "N/A"
            items = [
                ("Provider:", res.provider.upper()),
                ("Tested Interface:", res.interface if res.interface != "default" else active_str),
                ("Download Speed:", f"{res.download_mbps:.1f} Mbps" if res.status == "SUCCESS" else "N/A"),
                ("Upload Speed:", f"{res.upload_mbps:.1f} Mbps" if res.status == "SUCCESS" else "N/A"),
                ("Server Latency (Ping):", f"{res.latency_ms:.1f} ms" if res.status == "SUCCESS" else "N/A"),
                ("RFC 3550 Jitter:", f"{res.jitter_ms:.1f} ms" if res.status == "SUCCESS" else "N/A"),
                ("Benchmark Duration:", dur_str),
                ("Timestamp:", ts_str),
                ("Execution Status:", res.status),
            ]
        else:
            items = [
                ("Provider:", self.provider_menu.get().upper() if hasattr(self, "provider_menu") else "CLOUDFLARE"),
                ("Tested Interface:", active_str),
                ("Execution Status:", "No benchmark run yet in this session"),
            ]

        for label, val in items:
            r_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            r_frame.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(r_frame, text=label, font=("Segoe UI", 10), text_color=COCKPIT_THEME["text_muted"]).pack(side="left")
            val_color = COCKPIT_THEME["text_primary"]
            if label == "Execution Status:":
                if val == "SUCCESS":
                    val_color = COCKPIT_THEME["emerald"]
                elif val == "UNAVAILABLE":
                    val_color = COCKPIT_THEME["amber"]
                elif val == "FAILED":
                    val_color = COCKPIT_THEME["red"]
            ctk.CTkLabel(r_frame, text=val, font=("Segoe UI", 10, "bold"), text_color=val_color).pack(side="right")

        if res and res.error:
            err_box = ctk.CTkFrame(content_frame, fg_color=COCKPIT_THEME["bg_surface"], corner_radius=4)
            err_box.pack(fill="x", padx=14, pady=6)
            ctk.CTkLabel(
                err_box,
                text=f"Notice: {res.error}",
                font=("Consolas", 9),
                text_color=COCKPIT_THEME["amber"] if res.status == "UNAVAILABLE" else COCKPIT_THEME["red"],
                wraplength=450,
                justify="left",
                padx=8,
                pady=6,
            ).pack(anchor="w")

        note_lbl = ctk.CTkLabel(
            dialog,
            text="Note: Speed benchmarks are isolated on-demand measurements and do NOT alter failover policy decisions.\nAutoFailover 3.0 complies with vendor APIs & licensing without scraping.",
            font=("Segoe UI", 9, "italic"),
            text_color=COCKPIT_THEME["text_muted"],
            wraplength=480,
            justify="center",
        )
        note_lbl.pack(pady=(2, 8))

        ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            fg_color=COCKPIT_THEME["bg_surface"],
            hover_color=COCKPIT_THEME["border_highlight"],
            width=90,
            height=28,
        ).pack(pady=(0, 12))

    def _show_interface_detail_modal(self, iface: NetworkInterface):
        """Opens comprehensive technical details modal."""
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
