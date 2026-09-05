import json
import os
import queue
import sys
import time
from typing import Dict, List, Optional
import customtkinter as ctk

from core.failover_engine import FailoverEngine
from core.models import (
    FailoverConfig,
    InterfaceStatus,
    LogEvent,
    LogLevel,
    MonitoredInterfaceState,
    PriorityLevel,
)
from core.network_manager import NetworkManager
from .components import InterfaceCard, LogPanel, SettingsDialog


CONFIG_FILE = "config.json"


class AppWindow(ctk.CTk):
    """
    Main application window for Smart Auto-Failover Network Monitor.
    """

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("Smart Auto-Failover Network Monitor v1.0 • Zero-Drop Zoom")
        self.geometry("1020x760")
        self.minsize(940, 700)

        # Thread-safe event queue for GUI updates
        self.update_queue = queue.Queue()

        # Load or create configuration
        self.config = self._load_config()

        # Failover Engine
        self.engine = FailoverEngine(
            config=self.config,
            on_state_update=self._queue_state_update,
            on_log=self._queue_log_event,
        )

        # Metrics & Failover Stats
        self.total_failovers = 0
        self.start_time: Optional[float] = None

        # Build UI layout
        self._build_ui()

        # Populate adapters into dropdowns
        self.refresh_adapters()

        # Start periodic GUI queue processor
        self.after(100, self._process_queue)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_config(self) -> FailoverConfig:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return FailoverConfig.from_dict(data)
            except Exception as e:
                print(f"Failed to load {CONFIG_FILE}: {e}")
        return FailoverConfig()

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Failed to save {CONFIG_FILE}: {e}")

    def _build_ui(self):
        # Configure root layout
        self.grid_rowconfigure(2, weight=0)  # Active banner
        self.grid_rowconfigure(3, weight=0)  # Interface Cards
        self.grid_rowconfigure(4, weight=1)  # Log Panel
        self.grid_columnconfigure(0, weight=1)

        # 1. Top Header Bar
        header = ctk.CTkFrame(self, fg_color="#181A20", corner_radius=0, height=54)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=16, pady=8, sticky="w")

        app_title = ctk.CTkLabel(
            title_box,
            text="🚀 Smart Auto-Failover Monitor v1.0",
            font=("Segoe UI", 16, "bold"),
            text_color="#F8FAFC",
        )
        app_title.pack(anchor="w")

        app_sub = ctk.CTkLabel(
            title_box,
            text="Route Metric Orchestrator • Zero-Drop Zoom / UDP Failover • Dibuat oleh parikesitad-pm",
            font=("Segoe UI", 10),
            text_color="#94A3B8",
        )
        app_sub.pack(anchor="w")

        # Admin Badge & Elevation Button
        admin_box = ctk.CTkFrame(header, fg_color="transparent")
        admin_box.grid(row=0, column=2, padx=16, pady=8, sticky="e")

        os_name = NetworkManager.get_os_name()
        is_admin = NetworkManager.is_admin()
        if is_admin:
            self.admin_badge = ctk.CTkLabel(
                admin_box,
                text=f"🛡️ Elevated Mode ({os_name})",
                font=("Segoe UI", 11, "bold"),
                fg_color="#064E3B",
                text_color="#6EE7B7",
                corner_radius=6,
                padx=10,
                pady=4,
            )
            self.admin_badge.pack(side="right")
        else:
            self.admin_badge = ctk.CTkLabel(
                admin_box,
                text=f"⚠️ Simulation Mode ({os_name})",
                font=("Segoe UI", 11, "bold"),
                fg_color="#78350F",
                text_color="#FDE68A",
                corner_radius=6,
                padx=10,
                pady=4,
            )
            self.admin_badge.pack(side="left", padx=(0, 8))

            elevate_btn = ctk.CTkButton(
                admin_box,
                text="Elevate to Admin" if os_name == "Windows" else "Elevate (Sudo)",
                command=self._elevate_admin,
                font=("Segoe UI", 11, "bold"),
                fg_color="#3B82F6",
                hover_color="#2563EB",
                width=120,
                height=26,
                corner_radius=6,
            )
            elevate_btn.pack(side="right")

        # 2. Control Action Bar
        action_bar = ctk.CTkFrame(self, fg_color="#1E212B", corner_radius=10)
        action_bar.grid(row=1, column=0, padx=16, pady=(10, 6), sticky="ew")
        action_bar.grid_columnconfigure(0, weight=1)

        left_actions = ctk.CTkFrame(action_bar, fg_color="transparent")
        left_actions.pack(side="left", padx=12, pady=8)

        # Start / Stop Button
        self.toggle_btn = ctk.CTkButton(
            left_actions,
            text="▶ Start Monitoring",
            command=self._toggle_monitoring,
            font=("Segoe UI", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            width=160,
            height=34,
            corner_radius=8,
        )
        self.toggle_btn.pack(side="left", padx=(0, 10))

        # Auto-detect button
        detect_btn = ctk.CTkButton(
            left_actions,
            text="🔍 Auto-Detect Interfaces",
            command=self._auto_detect_interfaces,
            font=("Segoe UI", 12),
            fg_color="#2D3139",
            hover_color="#374151",
            width=150,
            height=34,
            corner_radius=8,
        )
        detect_btn.pack(side="left", padx=4)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            left_actions,
            text="🔄 Refresh Adapters",
            command=self.refresh_adapters,
            font=("Segoe UI", 12),
            fg_color="#2D3139",
            hover_color="#374151",
            width=130,
            height=34,
            corner_radius=8,
        )
        refresh_btn.pack(side="left", padx=4)

        # Right Actions
        right_actions = ctk.CTkFrame(action_bar, fg_color="transparent")
        right_actions.pack(side="right", padx=12, pady=8)

        reset_btn = ctk.CTkButton(
            right_actions,
            text="Reset Auto-Metrics",
            command=self._reset_metrics,
            font=("Segoe UI", 12),
            fg_color="#374151",
            hover_color="#4B5563",
            width=140,
            height=34,
            corner_radius=8,
        )
        reset_btn.pack(side="left", padx=6)

        settings_btn = ctk.CTkButton(
            right_actions,
            text="⚙️ Settings",
            command=self._open_settings,
            font=("Segoe UI", 12),
            fg_color="#2D3139",
            hover_color="#374151",
            width=90,
            height=34,
            corner_radius=8,
        )
        settings_btn.pack(side="left", padx=(4, 0))

        # 3. Active Default Route Status Banner
        self.active_banner = ctk.CTkLabel(
            self,
            text="STATUS: Monitoring Stopped. Press 'Start Monitoring' to begin route management.",
            font=("Segoe UI", 12, "bold"),
            fg_color="#20232B",
            text_color="#94A3B8",
            corner_radius=8,
            height=32,
        )
        self.active_banner.grid(row=2, column=0, padx=16, pady=(4, 6), sticky="ew")

        # 4. Interface Cards Container (3 Columns)
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=3, column=0, padx=16, pady=4, sticky="ew")
        for i in range(3):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="col")

        self.cards: Dict[PriorityLevel, InterfaceCard] = {}

        # Priority 1: LAN 1
        self.cards[PriorityLevel.P1] = InterfaceCard(
            cards_frame,
            priority=PriorityLevel.P1,
            on_adapter_selected=self._on_adapter_assigned,
        )
        self.cards[PriorityLevel.P1].grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        # Priority 2: LAN 2
        self.cards[PriorityLevel.P2] = InterfaceCard(
            cards_frame,
            priority=PriorityLevel.P2,
            on_adapter_selected=self._on_adapter_assigned,
        )
        self.cards[PriorityLevel.P2].grid(row=0, column=1, padx=4, sticky="nsew")

        # Priority 3: Wi-Fi
        self.cards[PriorityLevel.P3] = InterfaceCard(
            cards_frame,
            priority=PriorityLevel.P3,
            on_adapter_selected=self._on_adapter_assigned,
        )
        self.cards[PriorityLevel.P3].grid(row=0, column=2, padx=(6, 0), sticky="nsew")

        # 5. Activity Log Panel
        self.log_panel = LogPanel(self)
        self.log_panel.grid(row=4, column=0, padx=16, pady=(8, 6), sticky="nsew")

        # 6. Bottom Status Bar
        footer = ctk.CTkFrame(self, fg_color="#181A20", corner_radius=0, height=28)
        footer.grid(row=5, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_columnconfigure(2, weight=1)

        self.footer_left = ctk.CTkLabel(
            footer,
            text="Ready • Failover Events: 0",
            font=("Segoe UI", 10),
            text_color="#64748B",
        )
        self.footer_left.grid(row=0, column=0, padx=16, pady=4, sticky="w")

        # Watermark / Author Credit & Version
        self.footer_watermark = ctk.CTkLabel(
            footer,
            text="v1.0 | Dibuat oleh parikesitad-pm",
            font=("Segoe UI", 10, "bold"),
            text_color="#38BDF8",
        )
        self.footer_watermark.grid(row=0, column=1, pady=4, sticky="n")

        self.footer_right = ctk.CTkLabel(
            footer,
            text=f"Target: {self.config.ping_target_primary} • Ping: 1000ms / 800ms timeout",
            font=("Segoe UI", 10),
            text_color="#64748B",
        )
        self.footer_right.grid(row=0, column=2, padx=16, pady=4, sticky="e")

    def _elevate_admin(self):
        """Trigger UAC elevation to restart as admin."""
        self._save_config()
        if NetworkManager.request_elevation():
            self.destroy()
            sys.exit(0)

    def refresh_adapters(self):
        """Scan system adapters and refresh dropdown options."""
        adapters = NetworkManager.get_all_adapters()
        adapter_names = [a.alias for a in adapters]

        self.cards[PriorityLevel.P1].set_adapter_options(adapter_names, self.config.p1_alias)
        self.cards[PriorityLevel.P2].set_adapter_options(adapter_names, self.config.p2_alias)
        self.cards[PriorityLevel.P3].set_adapter_options(adapter_names, self.config.p3_alias)

        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.INFO,
                message=f"Discovered {len(adapters)} IPv4 network adapters: {', '.join(adapter_names)}",
            )
        )

    def _auto_detect_interfaces(self):
        """Automatically identify and assign Ethernet 1, Ethernet 2, and Wi-Fi adapters."""
        adapters = NetworkManager.get_all_adapters()

        ethernets = [a for a in adapters if a.adapter_type == "Ethernet"]
        wifis = [a for a in adapters if a.adapter_type == "Wireless"]

        # Sort ethernets by index or name
        ethernets.sort(key=lambda a: a.alias)

        if len(ethernets) >= 1:
            self.config.p1_alias = ethernets[0].alias
        if len(ethernets) >= 2:
            self.config.p2_alias = ethernets[1].alias
        elif len(ethernets) == 1 and not self.config.p2_alias:
            self.config.p2_alias = ""

        if wifis:
            self.config.p3_alias = wifis[0].alias

        self.engine.update_config(self.config)
        self.refresh_adapters()
        self._save_config()

        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.SUCCESS,
                message=(
                    f"Auto-assigned: LAN 1='{self.config.p1_alias}', "
                    f"LAN 2='{self.config.p2_alias}', "
                    f"Wi-Fi='{self.config.p3_alias}'"
                ),
            )
        )

    def _on_adapter_assigned(self, priority: PriorityLevel, alias: str):
        if priority == PriorityLevel.P1:
            self.config.p1_alias = alias
        elif priority == PriorityLevel.P2:
            self.config.p2_alias = alias
        elif priority == PriorityLevel.P3:
            self.config.p3_alias = alias

        self.engine.update_config(self.config)
        self._save_config()

    def _toggle_monitoring(self):
        if not self.engine._is_running:
            # Check if at least one adapter selected
            if not any([self.config.p1_alias, self.config.p2_alias, self.config.p3_alias]):
                self.log_panel.append_log(
                    LogEvent(
                        timestamp=time.strftime("%H:%M:%S"),
                        level=LogLevel.ERROR,
                        message="Please assign at least one network adapter before starting monitoring.",
                    )
                )
                return

            self.start_time = time.time()
            self.engine.start()
            self.toggle_btn.configure(
                text="■ Stop Monitoring",
                fg_color="#EF4444",
                hover_color="#DC2626",
            )
        else:
            self.engine.stop(restore_metrics=True)
            self.toggle_btn.configure(
                text="▶ Start Monitoring",
                fg_color="#10B981",
                hover_color="#059669",
            )
            self.active_banner.configure(
                text="STATUS: Monitoring Stopped. Metrics restored to Automatic Metric.",
                fg_color="#20232B",
                text_color="#94A3B8",
            )

    def _reset_metrics(self):
        self.engine.restore_automatic_metrics()

    def _open_settings(self):
        SettingsDialog(self, config=self.config, on_save=self._on_settings_saved)

    def _on_settings_saved(self, new_config: FailoverConfig):
        self.config = new_config
        self.engine.update_config(new_config)
        self._save_config()
        self.footer_right.configure(
            text=f"Target: {self.config.ping_target_primary} • Ping: {int(self.config.ping_interval_sec * 1000)}ms / {self.config.ping_timeout_ms}ms timeout"
        )
        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.INFO,
                message="Configuration updated and applied to failover engine.",
            )
        )

    def _queue_state_update(self, states: Dict[PriorityLevel, MonitoredInterfaceState]):
        self.update_queue.put(("state", states))

    def _queue_log_event(self, event: LogEvent):
        self.update_queue.put(("log", event))

    def _process_queue(self):
        """Drain events from queue and update UI elements."""
        try:
            while not self.update_queue.empty():
                item_type, data = self.update_queue.get_nowait()
                if item_type == "log":
                    event: LogEvent = data
                    self.log_panel.append_log(event)
                    if event.level == LogLevel.FAILOVER:
                        self.total_failovers += 1
                        self.footer_left.configure(
                            text=f"Failover Events: {self.total_failovers} • Active Primary: {self._get_active_alias()}"
                        )
                elif item_type == "state":
                    states: Dict[PriorityLevel, MonitoredInterfaceState] = data
                    self._update_ui_state(states)
        except Exception as e:
            print(f"Queue processing error: {e}")

        self.after(100, self._process_queue)

    def _get_active_alias(self) -> str:
        for p, s in self.engine.states.items():
            if s.is_active_route:
                return f"{p.short_label} ('{s.alias}')"
        return "None"

    def _update_ui_state(self, states: Dict[PriorityLevel, MonitoredInterfaceState]):
        for p, state in states.items():
            card = self.cards.get(p)
            if card:
                card.update_state(state)

        # Update Active Route Banner
        active_p = None
        for p, s in states.items():
            if s.is_active_route:
                active_p = (p, s)
                break

        if active_p:
            p, s = active_p
            if p == PriorityLevel.P1:
                self.active_banner.configure(
                    text=f"★ ACTIVE ROUTE: LAN 1 ('{s.alias}') • Metric: {s.assigned_metric or s.current_metric} • Latency: {s.last_latency_ms:.0f}ms • Zero-Drop Protected",
                    fg_color="#064E3B",
                    text_color="#6EE7B7",
                )
            elif p == PriorityLevel.P2:
                self.active_banner.configure(
                    text=f"⚡ FAILOVER ROUTE ACTIVE: LAN 2 ('{s.alias}') • Promoted to Metric: {s.assigned_metric or s.current_metric} • Latency: {s.last_latency_ms:.0f}ms",
                    fg_color="#7C2D12",
                    text_color="#FDBA74",
                )
            else:
                self.active_banner.configure(
                    text=f"⚡ TERTIARY FAILOVER ACTIVE: Wi-Fi ('{s.alias}') • Promoted to Metric: {s.assigned_metric or s.current_metric} • Latency: {s.last_latency_ms:.0f}ms",
                    fg_color="#581C87",
                    text_color="#E9D5FF",
                )
        else:
            self.active_banner.configure(
                text="⚠️ ALERT: No active healthy route! All monitored interfaces are experiencing RTO or disconnected.",
                fg_color="#7F1D1D",
                text_color="#FCA5A5",
            )

    def _on_closing(self):
        """Cleanup before exiting window."""
        try:
            self.engine.stop(restore_metrics=True)
            self._save_config()
        except Exception as e:
            print(f"Error on shutdown: {e}")
        self.destroy()

