import json
import os
import queue
import sys
import time
from typing import Dict, List, Optional
import webbrowser
import customtkinter as ctk

from core.failover_engine import FailoverEngine
from core.models import (
    AdapterInfo,
    FailoverConfig,
    InterfaceStatus,
    LogEvent,
    LogLevel,
    MonitoredInterfaceState,
    PriorityLevel,
)
from core.network_manager import NetworkManager
from core.traffic_monitor import TrafficMonitor
from .components import (
    AdapterSummaryBar,
    InterfaceCard,
    LogPanel,
    SettingsDialog,
    TrafficChartWidget,
)
from .modals import ChangelogModal, HelpFaqModal, SpeedtestModal


CONFIG_FILE = "config.json"
GITHUB_URL = "https://github.com/parikesitad-pm"


class AppWindow(ctk.CTk):
    """
    Main application window for Smart Auto-Failover Network Monitor v2.0.
    Supports Dual Mode (Dark/Light), Speedtest Suite, Adapter Toggles, and Traffic Monitor.
    """

    def __init__(self):
        super().__init__()

        # Load or create configuration
        self.config = self._load_config()

        # Set appearance theme mode
        ctk.set_appearance_mode(self.config.theme_mode)
        ctk.set_default_color_theme("blue")

        # Window configuration
        self.title("Smart Auto-Failover Network Monitor v2.0 • Zero-Drop Zoom")
        self.geometry("1060x820")
        self.minsize(960, 720)

        # Thread-safe event queue for GUI updates
        self.update_queue = queue.Queue()

        # Failover Engine & Traffic Monitor
        self.engine = FailoverEngine(
            config=self.config,
            on_state_update=self._queue_state_update,
            on_log=self._queue_log_event,
        )
        self.traffic_monitor = TrafficMonitor()
        self.all_adapters: List[AdapterInfo] = []

        # Metrics & Failover Stats
        self.total_failovers = 0
        self.start_time: Optional[float] = None

        # Build UI layout
        self._build_ui()

        # Populate adapters into dropdowns
        self.refresh_adapters()

        # Start periodic GUI queue processor
        self.after(100, self._process_queue)

        # Periodic traffic throughput monitor update
        self.after(1000, self._process_traffic_update)

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
        self.configure(fg_color=("#F1F5F9", "#12141A"))

        # Configure root layout grid
        self.grid_rowconfigure(5, weight=1)  # Log Panel expands
        self.grid_columnconfigure(0, weight=1)

        # 1. Top Header Bar
        header = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#181A20"), corner_radius=0, height=56)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=16, pady=8, sticky="w")

        app_title = ctk.CTkLabel(
            title_box,
            text="🚀 Smart Auto-Failover Monitor v2.0",
            font=("Segoe UI", 16, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        app_title.pack(anchor="w")

        app_sub = ctk.CTkLabel(
            title_box,
            text="Route Metric Orchestrator • Zero-Drop Zoom / UDP Failover • Dibuat oleh parikesitad-pm",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        )
        app_sub.pack(anchor="w")

        # Right Header: Dual Mode Switcher & Admin Badge
        right_header = ctk.CTkFrame(header, fg_color="transparent")
        right_header.grid(row=0, column=2, padx=16, pady=8, sticky="e")

        # Theme Switcher (Light / Dark)
        self.theme_btn = ctk.CTkSegmentedButton(
            right_header,
            values=["Light", "Dark"],
            command=self._on_theme_changed,
            font=("Segoe UI", 10, "bold"),
            width=110,
            height=26,
        )
        self.theme_btn.set(self.config.theme_mode)
        self.theme_btn.pack(side="left", padx=(0, 10))

        # Admin Badge & Elevation
        os_name = NetworkManager.get_os_name()
        is_admin = NetworkManager.is_admin()
        if is_admin:
            self.admin_badge = ctk.CTkLabel(
                right_header,
                text=f"🛡️ Elevated Mode ({os_name})",
                font=("Segoe UI", 11, "bold"),
                fg_color=("#D1FAE5", "#064E3B"),
                text_color=("#065F46", "#6EE7B7"),
                corner_radius=6,
                padx=10,
                pady=4,
            )
            self.admin_badge.pack(side="right")
        else:
            self.admin_badge = ctk.CTkLabel(
                right_header,
                text=f"⚠️ Simulation Mode ({os_name})",
                font=("Segoe UI", 11, "bold"),
                fg_color=("#FEF3C7", "#78350F"),
                text_color=("#92400E", "#FDE68A"),
                corner_radius=6,
                padx=10,
                pady=4,
            )
            self.admin_badge.pack(side="left", padx=(0, 8))

            elevate_btn = ctk.CTkButton(
                right_header,
                text="Elevate to Admin" if os_name == "Windows" else "Elevate (Sudo)",
                command=self._elevate_admin,
                font=("Segoe UI", 11, "bold"),
                fg_color=("#3B82F6", "#2563EB"),
                hover_color=("#2563EB", "#1D4ED8"),
                width=120,
                height=26,
                corner_radius=6,
            )
            elevate_btn.pack(side="right")

        # 2. Adapter Summary Bar
        self.summary_bar = AdapterSummaryBar(self)
        self.summary_bar.grid(row=1, column=0, padx=16, pady=(8, 4), sticky="ew")

        # 3. Control Action Bar
        action_bar = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#1E212B"),
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#2D3139"),
        )
        action_bar.grid(row=2, column=0, padx=16, pady=(4, 6), sticky="ew")
        action_bar.grid_columnconfigure(0, weight=1)

        left_actions = ctk.CTkFrame(action_bar, fg_color="transparent")
        left_actions.pack(side="left", padx=12, pady=8)

        # Start / Stop Button
        self.toggle_btn = ctk.CTkButton(
            left_actions,
            text="▶ Start Monitoring",
            command=self._toggle_monitoring,
            font=("Segoe UI", 13, "bold"),
            fg_color=("#10B981", "#059669"),
            hover_color=("#059669", "#047857"),
            width=150,
            height=34,
            corner_radius=8,
        )
        self.toggle_btn.pack(side="left", padx=(0, 8))

        # Auto-detect button
        detect_btn = ctk.CTkButton(
            left_actions,
            text="🔍 Auto-Detect",
            command=self._auto_detect_interfaces,
            font=("Segoe UI", 12),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=120,
            height=34,
            corner_radius=8,
        )
        detect_btn.pack(side="left", padx=4)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            left_actions,
            text="🔄 Refresh",
            command=self.refresh_adapters,
            font=("Segoe UI", 12),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=100,
            height=34,
            corner_radius=8,
        )
        refresh_btn.pack(side="left", padx=4)

        # Speedtest Button
        speedtest_btn = ctk.CTkButton(
            left_actions,
            text="⚡ Speedtest Suite",
            command=self._open_speedtest,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#6366F1", "#4F46E5"),
            hover_color=("#4F46E5", "#4338CA"),
            text_color="#FFFFFF",
            width=140,
            height=34,
            corner_radius=8,
        )
        speedtest_btn.pack(side="left", padx=6)

        # Right Actions
        right_actions = ctk.CTkFrame(action_bar, fg_color="transparent")
        right_actions.pack(side="right", padx=12, pady=8)

        reset_btn = ctk.CTkButton(
            right_actions,
            text="Reset Auto-Metrics",
            command=self._reset_metrics,
            font=("Segoe UI", 12),
            fg_color=("#E2E8F0", "#374151"),
            hover_color=("#CBD5E1", "#4B5563"),
            text_color=("#0F172A", "#F8FAFC"),
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
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=90,
            height=34,
            corner_radius=8,
        )
        settings_btn.pack(side="left", padx=(4, 0))

        # 4. Status Banner & Traffic Visualizer (Side by side)
        banner_container = ctk.CTkFrame(self, fg_color="transparent")
        banner_container.grid(row=3, column=0, padx=16, pady=(4, 6), sticky="ew")
        banner_container.grid_columnconfigure(0, weight=1)

        self.active_banner = ctk.CTkLabel(
            banner_container,
            text="STATUS: Monitoring Stopped. Tekan 'Start Monitoring' untuk memulai failover.",
            font=("Segoe UI", 12, "bold"),
            fg_color=("#FFFFFF", "#20232B"),
            text_color=("#64748B", "#94A3B8"),
            corner_radius=8,
            height=34,
        )
        self.active_banner.pack(fill="x", pady=(0, 4))

        # Live Traffic Chart Widget
        self.traffic_chart = TrafficChartWidget(banner_container, height=52)
        self.traffic_chart.pack(fill="x")

        # 5. Interface Cards Container (3 Columns)
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=4, column=0, padx=16, pady=4, sticky="ew")
        for i in range(3):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="col")

        self.cards: Dict[PriorityLevel, InterfaceCard] = {}

        # Priority 1: LAN 1
        self.cards[PriorityLevel.P1] = InterfaceCard(
            cards_frame,
            priority=PriorityLevel.P1,
            on_adapter_selected=self._on_adapter_assigned,
            on_toggle_adapter=self._on_toggle_adapter,
        )
        self.cards[PriorityLevel.P1].grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        # Priority 2: LAN 2
        self.cards[PriorityLevel.P2] = InterfaceCard(
            cards_frame,
            priority=PriorityLevel.P2,
            on_adapter_selected=self._on_adapter_assigned,
            on_toggle_adapter=self._on_toggle_adapter,
        )
        self.cards[PriorityLevel.P2].grid(row=0, column=1, padx=4, sticky="nsew")

        # Priority 3: Wi-Fi
        self.cards[PriorityLevel.P3] = InterfaceCard(
            cards_frame,
            priority=PriorityLevel.P3,
            on_adapter_selected=self._on_adapter_assigned,
            on_toggle_adapter=self._on_toggle_adapter,
        )
        self.cards[PriorityLevel.P3].grid(row=0, column=2, padx=(6, 0), sticky="nsew")

        # 6. Activity Log Panel
        self.log_panel = LogPanel(self)
        self.log_panel.grid(row=5, column=0, padx=16, pady=(6, 6), sticky="nsew")

        # 7. Enhanced Footer Bar
        footer = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#181A20"), corner_radius=0, height=32)
        footer.grid(row=6, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_columnconfigure(2, weight=1)

        # Left: Status & Failovers
        self.footer_left = ctk.CTkLabel(
            footer,
            text="Ready • Failover Events: 0",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        )
        self.footer_left.grid(row=0, column=0, padx=16, pady=4, sticky="w")

        # Center: Version, Changelog, Help & FAQ, Author Link
        center_footer = ctk.CTkFrame(footer, fg_color="transparent")
        center_footer.grid(row=0, column=1, pady=2, sticky="n")

        # Version Pill
        ver_pill = ctk.CTkLabel(
            center_footer,
            text=" v2.0 ",
            font=("Segoe UI", 10, "bold"),
            fg_color=("#E0E7FF", "#1E1B4B"),
            text_color=("#3730A3", "#818CF8"),
            corner_radius=4,
        )
        ver_pill.pack(side="left", padx=3)

        # Changelog button
        changelog_btn = ctk.CTkButton(
            center_footer,
            text="📜 Changelog",
            command=self._open_changelog,
            font=("Segoe UI", 10),
            fg_color="transparent",
            hover_color=("#E2E8F0", "#2D3139"),
            text_color=("#2563EB", "#60A5FA"),
            width=75,
            height=22,
        )
        changelog_btn.pack(side="left", padx=2)

        # Help & FAQ button
        help_btn = ctk.CTkButton(
            center_footer,
            text="❓ Help & FAQ",
            command=self._open_help_faq,
            font=("Segoe UI", 10),
            fg_color="transparent",
            hover_color=("#E2E8F0", "#2D3139"),
            text_color=("#2563EB", "#60A5FA"),
            width=75,
            height=22,
        )
        help_btn.pack(side="left", padx=2)

        # Author Clickable Link to GitHub
        author_btn = ctk.CTkButton(
            center_footer,
            text="Dibuat oleh: parikesitad-pm ↗",
            command=self._open_github,
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent",
            hover_color=("#E2E8F0", "#2D3139"),
            text_color=("#0284C7", "#38BDF8"),
            width=150,
            height=22,
        )
        author_btn.pack(side="left", padx=3)

        # Right: Target info
        self.footer_right = ctk.CTkLabel(
            footer,
            text=f"Target: {self.config.ping_target_primary} • Ping: 1000ms / 800ms timeout",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        )
        self.footer_right.grid(row=0, column=2, padx=16, pady=4, sticky="e")

    def _on_theme_changed(self, mode: str):
        self.config.theme_mode = mode
        ctk.set_appearance_mode(mode)
        self._save_config()

    def _elevate_admin(self):
        """Trigger UAC elevation to restart as admin."""
        self._save_config()
        if NetworkManager.request_elevation():
            self.destroy()
            sys.exit(0)

    def refresh_adapters(self):
        """Scan system adapters, update summary bar, and refresh dropdown options."""
        self.all_adapters = NetworkManager.get_all_adapters()
        adapter_names = [a.alias for a in self.all_adapters]

        self.cards[PriorityLevel.P1].set_adapter_options(adapter_names, self.config.p1_alias)
        self.cards[PriorityLevel.P2].set_adapter_options(adapter_names, self.config.p2_alias)
        self.cards[PriorityLevel.P3].set_adapter_options(adapter_names, self.config.p3_alias)

        summary = NetworkManager.get_port_summary(self.all_adapters, self._get_active_alias())
        self.summary_bar.update_summary(summary)

        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.INFO,
                message=f"Discovered {len(self.all_adapters)} network adapters: {', '.join(adapter_names)}",
            )
        )

    def _auto_detect_interfaces(self):
        """Automatically identify and assign Ethernet 1, Ethernet 2, and Wi-Fi adapters."""
        self.all_adapters = NetworkManager.get_all_adapters()

        ethernets = [a for a in self.all_adapters if a.adapter_type == "Ethernet"]
        wifis = [a for a in self.all_adapters if a.adapter_type == "Wireless"]

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

    def _on_toggle_adapter(self, alias: str, enabled: bool):
        """Manually connect/disconnect network adapter."""
        action = "Enable (Konek)" if enabled else "Disable (Putus)"
        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.WARNING,
                message=f"Manual Action: Setting port '{alias}' to {action}...",
            )
        )
        ok, msg = NetworkManager.set_adapter_enabled(alias, enabled)
        if ok:
            self.log_panel.append_log(
                LogEvent(
                    timestamp=time.strftime("%H:%M:%S"),
                    level=LogLevel.SUCCESS,
                    message=f"Port '{alias}' successfully set to {action}.",
                )
            )
        else:
            self.log_panel.append_log(
                LogEvent(
                    timestamp=time.strftime("%H:%M:%S"),
                    level=LogLevel.ERROR,
                    message=f"Failed to toggle port '{alias}': {msg}",
                )
            )
        self.after(1200, self.refresh_adapters)

    def _open_speedtest(self):
        SpeedtestModal(self, adapters=self.all_adapters)

    def _open_changelog(self):
        ChangelogModal(self)

    def _open_help_faq(self):
        HelpFaqModal(self)

    def _open_github(self):
        webbrowser.open(GITHUB_URL)

    def _toggle_monitoring(self):
        if not self.engine._is_running:
            if not any([self.config.p1_alias, self.config.p2_alias, self.config.p3_alias]):
                self.log_panel.append_log(
                    LogEvent(
                        timestamp=time.strftime("%H:%M:%S"),
                        level=LogLevel.ERROR,
                        message="Pilih setidaknya satu adapter sebelum memulai monitoring.",
                    )
                )
                return

            self.start_time = time.time()
            self.engine.start()
            self.toggle_btn.configure(
                text="■ Stop Monitoring",
                fg_color=("#EF4444", "#DC2626"),
                hover_color=("#DC2626", "#B91C1C"),
            )
        else:
            self.engine.stop(restore_metrics=True)
            self.toggle_btn.configure(
                text="▶ Start Monitoring",
                fg_color=("#10B981", "#059669"),
                hover_color=("#059669", "#047857"),
            )
            self.active_banner.configure(
                text="STATUS: Monitoring Stopped. Metrics restored to Automatic Metric.",
                fg_color=("#FFFFFF", "#20232B"),
                text_color=("#64748B", "#94A3B8"),
            )
            summary = NetworkManager.get_port_summary(self.all_adapters, "")
            self.summary_bar.update_summary(summary)

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
                message="Konfigurasi diperbarui.",
            )
        )

    def _queue_state_update(self, states: Dict[PriorityLevel, MonitoredInterfaceState]):
        self.update_queue.put(("state", states))

    def _queue_log_event(self, event: LogEvent):
        self.update_queue.put(("log", event))

    def _process_queue(self):
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

    def _process_traffic_update(self):
        """Update live traffic throughput stats every second."""
        try:
            stats_map = self.traffic_monitor.update()

            # Find active adapter alias
            active_alias = ""
            for p, s in self.engine.states.items():
                if s.is_active_route and s.alias:
                    active_alias = s.alias
                    if s.last_latency_ms > 0:
                        self.traffic_monitor.record_latency_sample(s.alias, s.last_latency_ms)
                    break

            if not active_alias:
                # Fallback to P1 alias if available
                active_alias = self.config.p1_alias or (self.all_adapters[0].alias if self.all_adapters else "")

            if active_alias and active_alias in stats_map:
                st = stats_map[active_alias]
                dl_hist = self.traffic_monitor.download_history.get(active_alias, [])
                up_hist = self.traffic_monitor.upload_history.get(active_alias, [])
                self.traffic_chart.update_traffic(st, dl_hist, up_hist)
        except Exception as e:
            print(f"Traffic update error: {e}")

        self.after(1000, self._process_traffic_update)

    def _get_active_alias(self) -> str:
        for p, s in self.engine.states.items():
            if s.is_active_route:
                return f"{p.short_label} ('{s.alias}')"
        return ""

    def _update_ui_state(self, states: Dict[PriorityLevel, MonitoredInterfaceState]):
        for p, state in states.items():
            card = self.cards.get(p)
            if card:
                card.update_state(state)

        # Update Summary Bar
        summary = NetworkManager.get_port_summary(self.all_adapters, self._get_active_alias())
        self.summary_bar.update_summary(summary)

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
                    fg_color=("#D1FAE5", "#064E3B"),
                    text_color=("#065F46", "#6EE7B7"),
                )
            elif p == PriorityLevel.P2:
                self.active_banner.configure(
                    text=f"⚡ FAILOVER ROUTE ACTIVE: LAN 2 ('{s.alias}') • Promoted to Metric: {s.assigned_metric or s.current_metric} • Latency: {s.last_latency_ms:.0f}ms",
                    fg_color=("#FFEDD5", "#7C2D12"),
                    text_color=("#C2410C", "#FDBA74"),
                )
            else:
                self.active_banner.configure(
                    text=f"⚡ TERTIARY FAILOVER ACTIVE: Wi-Fi ('{s.alias}') • Promoted to Metric: {s.assigned_metric or s.current_metric} • Latency: {s.last_latency_ms:.0f}ms",
                    fg_color=("#F3E8FF", "#581C87"),
                    text_color=("#7E22CE", "#E9D5FF"),
                )
        else:
            self.active_banner.configure(
                text="⚠️ ALERT: No active healthy route! All monitored interfaces are experiencing RTO or disconnected.",
                fg_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#991B1B", "#FCA5A5"),
            )

    def _on_closing(self):
        try:
            self.engine.stop(restore_metrics=True)
            self._save_config()
        except Exception as e:
            print(f"Error on shutdown: {e}")
        self.destroy()
