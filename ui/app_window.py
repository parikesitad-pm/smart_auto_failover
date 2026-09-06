import json
import os
import queue
import sys
import time
from typing import Dict, List, Optional
import webbrowser
import customtkinter as ctk
from PIL import Image

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
from core.sound_engine import SoundEngine, SoundType
from core.system_telemetry import SystemTelemetry
from core.traffic_monitor import TrafficMonitor
from .components import (
    AdapterSummaryBar,
    AppQoSWidget,
    InterfaceCard,
    LogPanel,
    SettingsDialog,
    SkeletonLoader,
    SportsCarGaugeWidget,
    ToastNotificationManager,
    TrafficChartWidget,
)
from .modals import (
    AddTargetModal,
    BandwidthQoSModal,
    ChangelogModal,
    HelpFaqModal,
    LogDetailModal,
    SettingsModal,
    SpeedtestModal,
    SystemDiagnosticsModal,
    TelemetrySourcesModal,
)


CONFIG_FILE = "config.json"
GITHUB_URL = "https://github.com/parikesitad-pm"
PROJECT_ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")


class AppWindow(ctk.CTk):
    """
    Main application window for MODULA - Smart Auto Failover v2.4.
    Supports Dual Mode (Dark/Light), 4-Engine Speedtest, Fullscreen (F11),
    Sports Car Gauge HUD, Inline Bandwidth QoS, Custom Ping (up to 4 targets),
    and Dynamic 1-8 Adapter Interface Cards.
    """

    def __init__(self):
        super().__init__()
        # Ensure window is hidden immediately so splash screen shows with zero flicker!
        self.withdraw()

        # Load or create configuration
        self.config = self._load_config()

        # Set appearance theme mode
        ctk.set_appearance_mode(self.config.theme_mode)
        ctk.set_default_color_theme("blue")

        # Configure Sound Engine from config
        SoundEngine.set_enabled(getattr(self.config, "sound_enabled", True))

        # Window configuration - Auto-maximized for zero-clipping responsive view
        self.title("MODULA - Smart Auto Failover v2.4 • Zero-Drop Zoom")
        self.geometry("1100x820")
        self.minsize(820, 560)
        self.is_fullscreen = False

        # Set Window Icon
        ico_path = os.path.join(ASSETS_DIR, "modula.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # Global Keyboard Shortcuts
        self._bind_shortcuts()

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
        self._prev_conn_status: Dict[str, bool] = {}
        self._initial_adapter_scan = True

        # Metrics & Failover Stats
        self.total_failovers = 0
        self.start_time: Optional[float] = None
        self.cards: Dict[PriorityLevel, InterfaceCard] = {}
        self.cards_frame: Optional[ctk.CTkFrame] = None

        # Build UI layout
        self._build_ui()

        # Toast Notification Manager
        self.toast = ToastNotificationManager(self)

        # GitHub-style animated skeleton preloader
        self.skeleton = SkeletonLoader(self, on_finish=self._on_skeleton_ready, min_duration=1.3)

        # Populate adapters into dropdowns
        self.refresh_adapters()

        # Start periodic GUI queue processor
        self.after(100, self._process_queue)

        # Periodic traffic throughput monitor update
        self.after(1000, self._process_traffic_update)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def show_window(self):
        """Called after splash screen finishes fadeout to smoothly display main window."""
        try:
            if sys.platform == "win32":
                self.state("zoomed")
            elif sys.platform.startswith("linux"):
                self.attributes("-zoomed", True)
        except Exception:
            pass
        self.deiconify()

    def _on_skeleton_ready(self):
        """Called when skeleton preloader finishes animating."""
        pass


    def _get_config_path(self) -> str:
        if os.path.exists(CONFIG_FILE) and os.access(CONFIG_FILE, os.W_OK):
            return CONFIG_FILE
        if os.access(".", os.W_OK):
            return CONFIG_FILE
        home_cfg = os.path.expanduser("~/.modula")
        os.makedirs(home_cfg, exist_ok=True)
        return os.path.join(home_cfg, "config.json")

    def _load_config(self) -> FailoverConfig:
        cfg_path = self._get_config_path()
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return FailoverConfig.from_dict(data)
            except Exception as e:
                print(f"Failed to load {cfg_path}: {e}")
        return FailoverConfig()

    def _save_config(self):
        cfg_path = self._get_config_path()
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(self.config.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Failed to save {cfg_path}: {e}")

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
        title_box.grid(row=0, column=0, padx=16, pady=6, sticky="w")

        # Barong Logo Badge
        logo_path = os.path.join(ASSETS_DIR, "modula_logo.png")
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                aspect = pil_img.width / pil_img.height
                logo_h = 40
                logo_w = int(logo_h * aspect)
                self.logo_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(logo_w, logo_h))
                logo_lbl = ctk.CTkLabel(title_box, image=self.logo_ctk, text="")
                logo_lbl.pack(side="left", padx=(0, 10))
            except Exception:
                pass

        text_title_box = ctk.CTkFrame(title_box, fg_color="transparent")
        text_title_box.pack(side="left")

        app_title = ctk.CTkLabel(
            text_title_box,
            text="MODULA  •  SMART AUTO FAILOVER",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        )
        app_title.pack(anchor="w")

        app_sub = ctk.CTkLabel(
            text_title_box,
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
        self.theme_btn.pack(side="left", padx=(0, 6))

        # Audio Alert Sound Toggle (Enable / Mute)
        self.sound_btn = ctk.CTkButton(
            right_header,
            text="🔊 Sound: ON" if SoundEngine.is_enabled() else "🔇 Sound: MUTE",
            command=self._toggle_sound,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#E2E8F0", "#2D3139") if SoundEngine.is_enabled() else ("#FEE2E2", "#7F1D1D"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=100,
            height=26,
            corner_radius=6,
        )
        self.sound_btn.pack(side="left", padx=(0, 6))

        # OS Info & Logo Badge
        os_sys = NetworkManager.get_os_name()
        if os_sys == "macOS":
            os_badge_text = "🍎 macOS"
        elif os_sys == "Windows":
            os_badge_text = "🪟 Windows"
        else:
            os_badge_text = "🐧 Linux"

        self.os_badge = ctk.CTkLabel(
            right_header,
            text=os_badge_text,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#F1F5F9", "#1E212B"),
            text_color=("#0284C7", "#38BDF8"),
            corner_radius=6,
            padx=8,
            pady=2,
        )
        self.os_badge.pack(side="left", padx=(0, 8))

        # Fullscreen Toggle Button (F11)
        self.fs_btn = ctk.CTkButton(
            right_header,
            text="⛶ F11",
            command=self._toggle_fullscreen,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=58,
            height=26,
            corner_radius=6,
        )
        self.fs_btn.pack(side="left", padx=(0, 8))

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
            font=("Segoe UI", 12, "bold"),
            fg_color=("#10B981", "#059669"),
            hover_color=("#059669", "#047857"),
            width=140,
            height=32,
            corner_radius=8,
        )
        self.toggle_btn.pack(side="left", padx=(0, 6))

        # Auto-detect button
        detect_btn = ctk.CTkButton(
            left_actions,
            text="🔍 Auto-Detect",
            command=self._auto_detect_interfaces,
            font=("Segoe UI", 12),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=110,
            height=32,
            corner_radius=8,
        )
        detect_btn.pack(side="left", padx=3)

        # Refresh button (triggers unified preloader & full rescan)
        refresh_btn = ctk.CTkButton(
            left_actions,
            text="🔄 Refresh",
            command=self.trigger_refresh,
            font=("Segoe UI", 12),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=95,
            height=32,
            corner_radius=8,
        )
        refresh_btn.pack(side="left", padx=3)

        # Speedtest Button (Barong Gold)
        speedtest_btn = ctk.CTkButton(
            left_actions,
            text="⚡ Speedtest (4 Engines)",
            command=self._open_speedtest,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#D97706", "#F59E0B"),
            hover_color=("#B45309", "#D97706"),
            text_color=("#FFFFFF", "#0F172A"),
            width=165,
            height=32,
            corner_radius=8,
        )
        speedtest_btn.pack(side="left", padx=3)

        # App Bandwidth QoS Button (Cyan / Accent)
        qos_btn = ctk.CTkButton(
            left_actions,
            text="🎛️ Bandwidth QoS",
            command=self._open_bandwidth_qos,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#0284C7", "#0EA5E9"),
            hover_color=("#0369A1", "#0284C7"),
            text_color=("#FFFFFF", "#0F172A"),
            width=140,
            height=32,
            corner_radius=8,
        )
        qos_btn.pack(side="left", padx=3)

        # Right Actions
        right_actions = ctk.CTkFrame(action_bar, fg_color="transparent")
        right_actions.pack(side="right", padx=12, pady=8)

        reset_btn = ctk.CTkButton(
            right_actions,
            text="Reset Auto-Metrics",
            command=self._reset_metrics,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#374151"),
            hover_color=("#CBD5E1", "#4B5563"),
            text_color=("#0F172A", "#F8FAFC"),
            width=130,
            height=32,
            corner_radius=8,
        )
        reset_btn.pack(side="left", padx=4)

        settings_btn = ctk.CTkButton(
            right_actions,
            text="⚙️ Settings",
            command=self._open_settings,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=85,
            height=32,
            corner_radius=8,
        )
        settings_btn.pack(side="left", padx=(3, 0))

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

        # Probing Targets Pill Bar (Dynamically updated based on Custom Ping config)
        self.targets_pill_bar = ctk.CTkFrame(
            banner_container,
            fg_color=("#F8FAFC", "#181B24"),
            corner_radius=8,
            border_width=1,
            border_color=("#CBD5E1", "#2D3345"),
            height=30,
        )
        self.targets_pill_bar.pack(fill="x", pady=(0, 4))
        self._update_targets_pill_bar()

        # Sports Car Tachometer Gauge HUD + Backbone Spectrum Bars (Inspired by Supercar Cluster)
        self.sports_gauge = SportsCarGaugeWidget(banner_container, height=140)
        self.sports_gauge.pack(fill="x", pady=(0, 4))

        # Inline Bandwidth QoS Priority Monitor (Zoom, Teams, Meet, OBS, vMix)
        self.app_qos = AppQoSWidget(banner_container)
        self.app_qos.pack(fill="x", pady=(0, 4))

        # 5. Interface Cards Container (Dynamically 1 up to 8 cards responsive grid)
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=4, column=0, padx=16, pady=4, sticky="ew")
        self._rebuild_adapter_cards()

        # 6. Activity Log Panel (Compacted with Full History Modal)
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

        # Version Pill (v2.4 Gold/Amber)
        ver_pill = ctk.CTkLabel(
            center_footer,
            text=" v2.4 ",
            font=("Segoe UI", 10, "bold"),
            fg_color=("#FEF3C7", "#78350F"),
            text_color=("#92400E", "#FDE68A"),
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

        # Probing Targets & RFC 3550 Sources Info button
        sources_btn = ctk.CTkButton(
            center_footer,
            text="🎯 Target & Jitter Info",
            command=self._open_telemetry_sources,
            font=("Segoe UI", 10),
            fg_color="transparent",
            hover_color=("#E2E8F0", "#2D3139"),
            text_color=("#D97706", "#F59E0B"),
            width=110,
            height=22,
        )
        sources_btn.pack(side="left", padx=2)

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

        # Right: Fastfetch Diagnostics mini button + Target info
        right_footer = ctk.CTkFrame(footer, fg_color="transparent")
        right_footer.grid(row=0, column=2, padx=16, pady=2, sticky="e")

        self.sys_diag_btn = ctk.CTkButton(
            right_footer,
            text="💻 CPU: --%  🧠 RAM: --%  🎮 GPU: --%",
            command=self._open_system_diagnostics,
            font=("Segoe UI", 9, "bold"),
            fg_color=("#F1F5F9", "#1E212B"),
            hover_color=("#E2E8F0", "#2D3139"),
            text_color=("#0F172A", "#38BDF8"),
            border_width=1,
            border_color=("#CBD5E1", "#334155"),
            height=24,
            corner_radius=6,
        )
        self.sys_diag_btn.pack(side="left", padx=(0, 8))

        self.footer_right = ctk.CTkLabel(
            right_footer,
            text=f"Target: {self.config.ping_target_primary}",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        )
        self.footer_right.pack(side="left")

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

    def _toggle_fullscreen(self):
        """Toggle borderless fullscreen mode (F11)."""
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        if self.is_fullscreen:
            self.fs_btn.configure(text="🗗 F11")
            self.toast.info("Fullscreen Aktif (Tekan F11 atau Esc untuk keluar)")
        else:
            self.fs_btn.configure(text="⛶ F11")
            self.toast.info("Keluar dari mode Fullscreen")
        SoundEngine.play(SoundType.ACTION)

    def _exit_fullscreen(self):
        """Exit fullscreen if active (Escape key)."""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)
            self.fs_btn.configure(text="⛶ F11")
            self.toast.info("Keluar dari mode Fullscreen")
            SoundEngine.play(SoundType.ACTION)

    def _toggle_sound(self):
        """Toggle master audio effects on/off."""
        new_state = not SoundEngine.is_enabled()
        SoundEngine.set_enabled(new_state)
        self.config.sound_enabled = new_state
        self._save_config()
        if new_state:
            self.sound_btn.configure(text="🔊 Sound: ON", fg_color=("#E2E8F0", "#2D3139"))
            SoundEngine.play(SoundType.SUCCESS)
            self.toast.success("Sound Effects: AKTIF 🔊")
        else:
            self.sound_btn.configure(text="🔇 Sound: MUTE", fg_color=("#FEE2E2", "#7F1D1D"))
            self.toast.warning("Sound Effects: DIMATIKAN 🔇")

    def _open_bandwidth_qos(self):
        """Open the Application Bandwidth Allocation & QoS Modal."""
        SoundEngine.play(SoundType.ACTION)
        BandwidthQoSModal(self)

    def _open_system_diagnostics(self):
        """Open Fastfetch-style Hardware Diagnostics & Junk Cleaner modal."""
        SoundEngine.play(SoundType.ACTION)
        SystemDiagnosticsModal(self)

    def _rebuild_adapter_cards(self):
        """
        Dynamically rebuild adapter interface cards to match active/detected hardware (1 up to 8 cards).
        - 1 adapter: 1 full-width card
        - 2 adapters: 2 columns
        - 3 adapters: 3 columns
        - 4 adapters: 4 columns
        - 5 to 8 adapters: 2 rows responsive grid
        """
        if not hasattr(self, "cards_frame") or self.cards_frame is None:
            return

        for child in self.cards_frame.winfo_children():
            child.destroy()
        self.cards.clear()

        adapter_names = [a.alias for a in self.all_adapters]
        num_cards = max(1, min(len(self.all_adapters), 8))

        if num_cards <= 4:
            cols = num_cards
            for c in range(8):
                self.cards_frame.grid_columnconfigure(c, weight=1 if c < cols else 0, uniform="card_col" if c < cols else "")

            for i in range(num_cards):
                priority = PriorityLevel(i + 1)
                card = InterfaceCard(
                    self.cards_frame,
                    priority=priority,
                    on_adapter_selected=self._on_adapter_assigned,
                    on_toggle_adapter=self._on_toggle_adapter,
                )
                padx_l = 0 if i == 0 else 4
                padx_r = 0 if i == num_cards - 1 else 4
                card.grid(row=0, column=i, padx=(padx_l, padx_r), pady=2, sticky="nsew")

                alias_val = getattr(self.config, f"p{priority.value}_alias", "")
                card.set_adapter_options(adapter_names, alias_val)
                self.cards[priority] = card
        else:
            cols = (num_cards + 1) // 2
            for c in range(8):
                self.cards_frame.grid_columnconfigure(c, weight=1 if c < cols else 0, uniform="card_col" if c < cols else "")

            for i in range(num_cards):
                priority = PriorityLevel(i + 1)
                r = i // cols
                c = i % cols
                card = InterfaceCard(
                    self.cards_frame,
                    priority=priority,
                    on_adapter_selected=self._on_adapter_assigned,
                    on_toggle_adapter=self._on_toggle_adapter,
                )
                card.grid(row=r, column=c, padx=4, pady=3, sticky="nsew")

                alias_val = getattr(self.config, f"p{priority.value}_alias", "")
                card.set_adapter_options(adapter_names, alias_val)
                self.cards[priority] = card

    def refresh_adapters(self):
        """Scan system adapters, update summary bar, and detect plug/unplug events with sound."""
        prev_status = dict(self._prev_conn_status)
        self.all_adapters = NetworkManager.get_all_adapters()
        adapter_names = [a.alias for a in self.all_adapters]

        # Detect connection / disconnection transitions
        for a in self.all_adapters:
            was_connected = prev_status.get(a.alias)
            if was_connected is not None and not self._initial_adapter_scan:
                if not was_connected and a.is_connected:
                    SoundEngine.play(SoundType.CONNECT)
                    icon = "📶" if a.adapter_type == "Wireless" else "🔌"
                    self.toast.success(f"{icon} {a.adapter_type} Terhubung: '{a.alias}'")
                elif was_connected and not a.is_connected:
                    SoundEngine.play(SoundType.DISCONNECT)
                    icon = "📶" if a.adapter_type == "Wireless" else "🔌"
                    self.toast.error(f"⚠️ {icon} {a.adapter_type} Terputus: '{a.alias}'")

            self._prev_conn_status[a.alias] = a.is_connected

        # Auto-sanitize config if all configured aliases are missing from current machine (e.g. freshly cloned)
        has_any_configured = any(
            getattr(self.config, f"p{i}_alias", "") in adapter_names for i in range(1, 9) if getattr(self.config, f"p{i}_alias", "")
        )
        if not has_any_configured and self.all_adapters and self._initial_adapter_scan:
            self._initial_adapter_scan = False
            self._auto_detect_interfaces()
            return

        self._initial_adapter_scan = False

        # Dynamically render 1 to 8 cards
        self._rebuild_adapter_cards()

        summary = NetworkManager.get_port_summary(self.all_adapters, self._get_active_alias())
        self.summary_bar.update_summary(summary)

        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.INFO,
                message=f"Discovered {len(self.all_adapters)} network adapters: {', '.join(adapter_names)}",
            )
        )

    def trigger_refresh(self):
        """Unified Refresh: plays sound, clears cache, shows preloader, and rescans all hardware."""
        SoundEngine.play(SoundType.ACTION)
        backend = NetworkManager.get_backend()
        if hasattr(backend, "clear_cache"):
            backend.clear_cache()
        self.skeleton = SkeletonLoader(self, on_finish=self._on_skeleton_ready, min_duration=1.2)
        self.refresh_adapters()
        self.toast.success("🔄 Semua modul & port adapter berhasil diperbarui.")

    def _hot_reload(self):
        self.trigger_refresh()

    def _slow_reload(self):
        self.trigger_refresh()

    def _auto_detect_interfaces(self):
        """
        Automatically identify and assign Ethernet and Wi-Fi adapters.
        Strictly prioritizes physical Ethernet (docking / onboard GbE) over virtual/USB tethering.
        Dynamically populates up to 8 priorities.
        """
        SoundEngine.play(SoundType.ACTION)
        backend = NetworkManager.get_backend()
        if hasattr(backend, "clear_cache"):
            backend.clear_cache()
        self.all_adapters = NetworkManager.get_all_adapters()

        ethernets = [a for a in self.all_adapters if a.adapter_type == "Ethernet"]
        wifis = [a for a in self.all_adapters if a.adapter_type == "Wireless"]

        def score_ethernet(a: AdapterInfo) -> int:
            score = 0
            if a.is_connected:
                score += 100
            if a.gateway and a.gateway != "0.0.0.0":
                score += 50
            if a.ipv4 and not a.ipv4.startswith("169.254."):
                score += 30
            desc = (a.description or "").lower()
            alias = a.alias.lower()
            # Prioritize genuine PCIe GbE / Realtek / Intel / Docking station controllers
            if any(k in desc or k in alias for k in ["pcie", "gbe", "gigabit", "ethernet", "lan", "dock", "realtek", "intel", "asix"]):
                score += 25
            # Deprioritize phone USB tethering so physical docking Ethernet is always selected first
            if any(k in desc or k in alias for k in ["rndis", "tether", "remote ndis", "ncm", "phone"]):
                score -= 20
            return score

        def score_wifi(a: AdapterInfo) -> int:
            score = 0
            if a.is_connected:
                score += 100
            if a.gateway and a.gateway != "0.0.0.0":
                score += 50
            if a.ipv4 and not a.ipv4.startswith("169.254."):
                score += 30
            return score

        ethernets.sort(key=score_ethernet, reverse=True)
        wifis.sort(key=score_wifi, reverse=True)

        ordered: List[str] = []
        if ethernets:
            ordered.append(ethernets[0].alias)
        if len(ethernets) > 1:
            ordered.append(ethernets[1].alias)
        if wifis:
            ordered.append(wifis[0].alias)

        # Add remaining ethernets / wifis
        for a in self.all_adapters:
            if a.alias not in ordered:
                ordered.append(a.alias)

        # Assign to P1..P8
        for i in range(1, 9):
            val = ordered[i - 1] if i - 1 < len(ordered) else ""
            setattr(self.config, f"p{i}_alias", val)

        self.engine.update_config(self.config)
        self.refresh_adapters()
        self._save_config()

        SoundEngine.play(SoundType.SUCCESS)
        assigned_desc = ", ".join(f"P{i}='{getattr(self.config, f'p{i}_alias')}'" for i in range(1, min(len(ordered)+1, 9)) if getattr(self.config, f'p{i}_alias'))
        self.toast.success(f"Auto-detect: {assigned_desc or 'None'}")

        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.SUCCESS,
                message=f"Auto-assigned priorities: {assigned_desc}",
            )
        )

    def _on_adapter_assigned(self, priority: PriorityLevel, alias: str):
        setattr(self.config, f"p{priority.value}_alias", alias)
        self.engine.update_config(self.config)
        self._save_config()
        SoundEngine.play(SoundType.ACTION)
        self.toast.info(f"{priority.label} diatur ke: '{alias}'")


    def _on_toggle_adapter(self, alias: str, enabled: bool):
        """Manually connect/disconnect network adapter."""
        SoundEngine.play(SoundType.ACTION)
        action = "Enable (Konek)" if enabled else "Disable (Putus)"
        self.toast.info(f"Mengubah port '{alias}' -> {action}...")
        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.WARNING,
                message=f"Manual Action: Setting port '{alias}' to {action}...",
            )
        )
        ok, msg = NetworkManager.set_adapter_enabled(alias, enabled)
        if ok:
            SoundEngine.play(SoundType.SUCCESS)
            self.toast.success(f"Port '{alias}' -> {action} berhasil!")
            self.log_panel.append_log(
                LogEvent(
                    timestamp=time.strftime("%H:%M:%S"),
                    level=LogLevel.SUCCESS,
                    message=f"Port '{alias}' successfully set to {action}.",
                )
            )
        else:
            SoundEngine.play(SoundType.DISCONNECT)
            self.toast.error(f"Gagal ubah port '{alias}': {msg}")
            self.log_panel.append_log(
                LogEvent(
                    timestamp=time.strftime("%H:%M:%S"),
                    level=LogLevel.ERROR,
                    message=f"Failed to toggle port '{alias}': {msg}",
                )
            )
        self.after(1200, self.refresh_adapters)

    def _open_speedtest(self):
        SoundEngine.play(SoundType.ACTION)
        SpeedtestModal(self, adapters=self.all_adapters)

    def _open_changelog(self):
        SoundEngine.play(SoundType.ACTION)
        ChangelogModal(self)

    def _open_help_faq(self):
        SoundEngine.play(SoundType.ACTION)
        HelpFaqModal(self)

    def _open_telemetry_sources(self):
        SoundEngine.play(SoundType.ACTION)
        TelemetrySourcesModal(self)

    def _open_github(self):
        SoundEngine.play(SoundType.ACTION)
        webbrowser.open(GITHUB_URL)

    def _toggle_monitoring(self):
        if not self.engine._is_running:
            adapter_names = [a.alias for a in self.all_adapters]
            valid_active = [
                a for a in [self.config.p1_alias, self.config.p2_alias, self.config.p3_alias]
                if a and a in adapter_names
            ]
            if not valid_active and self.all_adapters:
                self._auto_detect_interfaces()
                valid_active = [
                    a for a in [self.config.p1_alias, self.config.p2_alias, self.config.p3_alias]
                    if a and a in adapter_names
                ]

            if not valid_active:
                SoundEngine.play(SoundType.DISCONNECT)
                self.toast.error("Pilih setidaknya satu adapter yang terhubung sebelum monitoring!")
                self.log_panel.append_log(
                    LogEvent(
                        timestamp=time.strftime("%H:%M:%S"),
                        level=LogLevel.ERROR,
                        message="Pilih setidaknya satu adapter aktif sebelum memulai monitoring.",
                    )
                )
                return

            SoundEngine.play(SoundType.ACTION)
            self.toast.info("Network monitoring aktif. Proteksi failover aktif.")
            self.start_time = time.time()
            self.engine.start()
            self.toggle_btn.configure(
                text="■ Stop Monitoring",
                fg_color=("#EF4444", "#DC2626"),
                hover_color=("#DC2626", "#B91C1C"),
            )
        else:
            SoundEngine.play(SoundType.ACTION)
            self.toast.warning("Monitoring dihentikan. Metrics dikembalikan.")
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

    def _bind_shortcuts(self):
        """Bind global keyboard shortcuts dynamically based on user configuration."""
        shortcuts = getattr(self.config, "shortcuts", {})

        mapping = {
            "start_stop": lambda e: self._toggle_monitoring(),
            "refresh": lambda e: self.trigger_refresh(),
            "auto_detect": lambda e: self._auto_detect_interfaces(),
            "speedtest": lambda e: self._open_speedtest(),
            "qos": lambda e: self._open_bandwidth_qos(),
            "settings": lambda e: self._open_settings(),
            "fullscreen": lambda e: self._toggle_fullscreen(),
        }

        # Always bind Escape to exit fullscreen
        self.bind("<Escape>", lambda e: self._exit_fullscreen())

        for action, default_key in [
            ("start_stop", shortcuts.get("start_stop", "Ctrl+M")),
            ("refresh", shortcuts.get("refresh", "F5")),
            ("auto_detect", shortcuts.get("auto_detect", "Ctrl+D")),
            ("speedtest", shortcuts.get("speedtest", "Ctrl+T")),
            ("qos", shortcuts.get("qos", "Ctrl+Q")),
            ("settings", shortcuts.get("settings", "Ctrl+P")),
            ("fullscreen", shortcuts.get("fullscreen", "F11")),
        ]:
            tk_sequence = self._to_tk_key(default_key)
            if tk_sequence and action in mapping:
                try:
                    self.bind(tk_sequence, mapping[action])
                except Exception as ex:
                    print(f"Failed to bind {tk_sequence} for {action}: {ex}")

    @staticmethod
    def _to_tk_key(key_combo: str) -> str:
        """Convert 'Ctrl+M' -> '<Control-m>', 'F11' -> '<F11>', 'Alt+R' -> '<Alt-r>'."""
        if not key_combo:
            return ""
        parts = [p.strip() for p in key_combo.split("+")]
        modifiers = []
        key = ""
        for p in parts:
            p_lower = p.lower()
            if p_lower in ("ctrl", "control"):
                modifiers.append("Control")
            elif p_lower in ("alt", "option"):
                modifiers.append("Alt")
            elif p_lower in ("shift",):
                modifiers.append("Shift")
            else:
                key = p
        if not key and modifiers:
            return ""
        if len(key) == 1:
            key = key.lower()
        if modifiers:
            return f"<{'-'.join(modifiers)}-{key}>"
        return f"<{key}>"

    def _update_targets_pill_bar(self):
        """Dynamically render the ICMP target pills based on current config."""
        for w in self.targets_pill_bar.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.targets_pill_bar,
            text="🌐 ACTIVE ICMP BACKBONES:",
            font=("Segoe UI", 10, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(side="left", padx=(10, 8), pady=3)

        pills_data = [
            (f"⚡ P1: {self.config.ping_target_primary}", "#10B981", ("#D1FAE5", "#064E3B")),
            (f"🔍 P2: {self.config.ping_target_secondary}", "#38BDF8", ("#E0F2FE", "#0C4A6E")),
            (f"🛡️ P3: {self.config.ping_target_tertiary}", "#A78BFA", ("#EDE9FE", "#4C1D95")),
        ]
        t4_val = getattr(self.config, "ping_target_quaternary", "")
        if t4_val:
            pills_data.append((f"🛰️ P4: {t4_val}", "#DB2777", ("#FDF2F8", "#831843")))

        for pill_text, pill_text_col, pill_bg in pills_data:
            ctk.CTkLabel(
                self.targets_pill_bar,
                text=pill_text,
                font=("Segoe UI", 9, "bold"),
                fg_color=pill_bg,
                text_color=pill_text_col,
                corner_radius=6,
                padx=8,
                pady=2,
            ).pack(side="left", padx=4, pady=3)

        # Quick Button to Add/Edit 4th Target
        t4_btn_text = "✏️ Edit Target 4" if t4_val else "+ Tambah Target ke-4"
        add_t4_btn = ctk.CTkButton(
            self.targets_pill_bar,
            text=t4_btn_text,
            command=self._open_add_target,
            font=("Segoe UI", 9, "bold"),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#D97706", "#F59E0B"),
            height=22,
            width=120,
            corner_radius=6,
        )
        add_t4_btn.pack(side="left", padx=(6, 4), pady=3)

        info_pill_btn = ctk.CTkButton(
            self.targets_pill_bar,
            text="ℹ️ Info Target & Jitter",
            command=self._open_telemetry_sources,
            font=("Segoe UI", 9, "bold"),
            fg_color="transparent",
            hover_color=("#E2E8F0", "#2D3139"),
            text_color=("#D97706", "#F59E0B"),
            width=115,
            height=20,
        )
        info_pill_btn.pack(side="right", padx=(0, 6))

        edit_ping_btn = ctk.CTkButton(
            self.targets_pill_bar,
            text="⚙️ Custom Ping",
            command=self._open_settings,
            font=("Segoe UI", 9, "bold"),
            fg_color="transparent",
            hover_color=("#E2E8F0", "#2D3139"),
            text_color=("#0284C7", "#38BDF8"),
            width=90,
            height=20,
        )
        edit_ping_btn.pack(side="right", padx=(0, 4))

    def _open_add_target(self):
        SoundEngine.play(SoundType.ACTION)
        AddTargetModal(self, config=self.config, on_saved=self._on_target_saved)

    def _on_target_saved(self, new_ip: str):
        self.config.ping_target_quaternary = new_ip
        self.engine.update_config(self.config)
        self._save_config()
        self._update_targets_pill_bar()
        SoundEngine.play(SoundType.SUCCESS)
        if new_ip:
            self.toast.success(f"🎯 Target ke-4 aktif: {new_ip}! Bilah spectrum kini 8 bilah.")
        else:
            self.toast.info("Target ke-4 dinonaktifkan. Bilah spectrum kembali 6 bilah.")

    @staticmethod
    def _render_smooth_bar(pct: float, length: int = 4) -> str:
        pct = max(0.0, min(100.0, pct))
        total_steps = length * 4
        current_step = int(round((pct / 100.0) * total_steps))
        full_blocks = min(length, current_step // 4)
        remainder = current_step % 4
        shades = ["", "░", "▒", "▓"]
        bar = "█" * full_blocks
        if full_blocks < length:
            if remainder > 0:
                bar += shades[remainder]
                bar += "░" * (length - full_blocks - 1)
            else:
                bar += "░" * (length - full_blocks)
        return bar[:length]

    def _reset_metrics(self):
        SoundEngine.play(SoundType.ACTION)
        self.engine.restore_automatic_metrics()
        self.toast.info("Route metrics direset ke otomatis")

    def _open_settings(self):
        SoundEngine.play(SoundType.ACTION)
        SettingsModal(self, config=self.config, on_save=self._on_settings_saved)

    def _on_settings_saved(self, new_config: FailoverConfig):
        self.config = new_config
        self.engine.update_config(new_config)
        self._save_config()
        self._bind_shortcuts()
        self._update_targets_pill_bar()
        self.footer_right.configure(
            text=f"Target: {self.config.ping_target_primary} • Ping: {int(self.config.ping_interval_sec * 1000)}ms / {self.config.ping_timeout_ms}ms"
        )
        self.toast.success("⚙️ Pengaturan & Shortcut Berhasil Disimpan!")
        targets_str = ", ".join(self.config.get_configured_targets())
        self.log_panel.append_log(
            LogEvent(
                timestamp=time.strftime("%H:%M:%S"),
                level=LogLevel.INFO,
                message=f"Konfigurasi diperbarui: Targets [{targets_str}] | Method: {self.config.probe_method}",
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
                        SoundEngine.play(SoundType.FAILOVER)
                        self.toast.error(f"🚨 FAILOVER: {event.message}")
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
        """Update live traffic throughput stats, sports car gauge, and QoS telemetry every second."""
        try:
            # Update telemetry mini meter on footer with smooth bars & high-load alert
            try:
                metrics = SystemTelemetry.get_live_metrics()
                SystemTelemetry.record_history_sample(metrics.cpu_percent, metrics.ram_percent, metrics.gpu_percent)

                cpu_bar = self._render_smooth_bar(metrics.cpu_percent, length=4)
                ram_bar = self._render_smooth_bar(metrics.ram_percent, length=4)
                gpu_bar = self._render_smooth_bar(metrics.gpu_percent, length=4)
                self.sys_diag_btn.configure(
                    text=f"💻 CPU {cpu_bar} {metrics.cpu_percent:.0f}%  🧠 RAM {ram_bar} {metrics.ram_percent:.0f}%  🎮 GPU {gpu_bar} {metrics.gpu_percent:.0f}%"
                )

                # Audio alert when CPU, RAM, or GPU load > 85% (obeying global mute)
                if (metrics.cpu_percent > 85.0 or metrics.ram_percent > 85.0 or metrics.gpu_percent > 85.0):
                    now_t = time.time()
                    if (now_t - getattr(self, "_last_high_load_alert", 0.0)) > 30.0:
                        self._last_high_load_alert = now_t
                        if SoundEngine.is_enabled():
                            SoundEngine.play(SoundType.HIGH_LOAD)
                        if metrics.cpu_percent > 85.0:
                            load_src = "CPU"
                            val = metrics.cpu_percent
                        elif metrics.ram_percent > 85.0:
                            load_src = "RAM"
                            val = metrics.ram_percent
                        else:
                            load_src = "GPU"
                            val = metrics.gpu_percent
                        self.toast.warning(f"⚠️ Beban Tinggi: {load_src} mencapai {val:.0f}%! (>85%)")
            except Exception:
                pass

            stats_map = self.traffic_monitor.update()

            # Find active adapter alias
            active_alias = ""
            active_latency = 12.0
            active_jitter = 1.2
            for p, s in self.engine.states.items():
                if s.is_active_route and s.alias:
                    active_alias = s.alias
                    if s.last_latency_ms > 0:
                        active_latency = s.last_latency_ms
                        active_jitter = s.jitter_ms
                        self.traffic_monitor.record_latency_sample(s.alias, s.last_latency_ms)
                    break

            if not active_alias:
                active_alias = self.config.p1_alias or (self.all_adapters[0].alias if self.all_adapters else "")

            speed_mbps = 0.0
            if active_alias and active_alias in stats_map:
                st = stats_map[active_alias]
                speed_mbps = st.download_mbps + st.upload_mbps

            # Update Sports Car Tachometer Gauge HUD + Backbone Spectrum Bars
            targets = self.config.get_configured_targets()
            self.sports_gauge.update_gauge(
                speed_mbps=speed_mbps,
                latency_ms=active_latency,
                jitter_ms=active_jitter,
                targets=targets,
            )

            # Update Inline Bandwidth QoS Monitor
            self.app_qos.update_stats()

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
            badge_title = f"{p.label} ('{s.alias}')"
            bg_col = ("#D1FAE5", "#064E3B") if p == PriorityLevel.P1 else (("#FFEDD5", "#7C2D12") if p == PriorityLevel.P2 else ("#F3E8FF", "#581C87"))
            text_col = ("#065F46", "#6EE7B7") if p == PriorityLevel.P1 else (("#C2410C", "#FDBA74") if p == PriorityLevel.P2 else ("#7E22CE", "#E9D5FF"))

            self.active_banner.configure(
                text=f"★ ACTIVE ROUTE: {badge_title} • Metric: {s.assigned_metric or s.current_metric} • Latency: {s.last_latency_ms:.0f}ms • Zero-Drop Protected",
                fg_color=bg_col,
                text_color=text_col,
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
