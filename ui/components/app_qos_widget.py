"""
MODULA - Smart Auto Failover v2.4
Inline Application Bandwidth Allocation & QoS Monitor Widget.
Mounted directly beneath the Live Gauge on the main dashboard.
Provides live throughput per media application and 1-click priority boost controls.
"""
import time
import tkinter as tk
from typing import Callable, Dict, List, Optional
import customtkinter as ctk

from core.bandwidth_qos import BandwidthQoSEngine, AppTrafficInfo
from core.sound_engine import SoundEngine, SoundType


class AppQoSWidget(ctk.CTkFrame):
    """
    Inline dashboard monitor showing real-time bandwidth consumption
    per application (Zoom, Meet, Teams, OBS, vMix) with 1-click priority presets.
    """

    def __init__(self, master, on_open_modal: Optional[Callable[[], None]] = None, on_toast: Optional[Callable[[str, str], None]] = None, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#141620"),
            **kwargs,
        )
        self.on_open_modal = on_open_modal
        self.on_toast = on_toast
        self.apps: List[AppTrafficInfo] = []
        self._last_scan_time = 0.0

        self._build_ui()
        self.refresh_apps()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header bar with title and quick 1-click action buttons
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(6, 4))
        header.grid_columnconfigure(0, weight=1)

        left_hdr = ctk.CTkFrame(header, fg_color="transparent")
        left_hdr.pack(side="left")

        ctk.CTkLabel(
            left_hdr,
            text="🎛️ MONITOR PRIORITAS & ALOKASI BANDWIDTH PER APLIKASI:",
            font=("Segoe UI", 10, "bold"),
            text_color=("#0284C7", "#38BDF8"),
        ).pack(side="left", padx=(0, 8))

        self.mode_label = ctk.CTkLabel(
            left_hdr,
            text="MODE: NORMAL",
            font=("Segoe UI", 9, "bold"),
            fg_color=("#E0F2FE", "#0C4A6E"),
            text_color=("#0284C7", "#38BDF8"),
            corner_radius=4,
            padx=6,
            pady=1,
        )
        self.mode_label.pack(side="left", padx=(0, 4))

        # Quick preset buttons
        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.pack(side="right")


        self.btn_conf = ctk.CTkButton(
            btn_box,
            text="🎥 Boost Meeting",
            command=lambda: self._apply_preset("conference"),
            font=("Segoe UI", 9, "bold"),
            fg_color=("#0284C7", "#0369A1"),
            hover_color=("#0369A1", "#0284C7"),
            text_color="#FFFFFF",
            width=100,
            height=22,
            corner_radius=6,
        )
        self.btn_conf.pack(side="left", padx=2)

        self.btn_stream = ctk.CTkButton(
            btn_box,
            text="🔴 Boost Stream",
            command=lambda: self._apply_preset("streaming"),
            font=("Segoe UI", 9, "bold"),
            fg_color=("#DC2626", "#991B1B"),
            hover_color=("#991B1B", "#DC2626"),
            text_color="#FFFFFF",
            width=100,
            height=22,
            corner_radius=6,
        )
        self.btn_stream.pack(side="left", padx=2)

        self.btn_balance = ctk.CTkButton(
            btn_box,
            text="⚖️ Seimbangkan",
            command=lambda: self._apply_preset("balanced"),
            font=("Segoe UI", 9),
            fg_color=("#E2E8F0", "#242938"),
            hover_color=("#CBD5E1", "#333A4D"),
            text_color=("#0F172A", "#F8FAFC"),
            width=90,
            height=22,
            corner_radius=6,
        )
        self.btn_balance.pack(side="left", padx=2)

        if self.on_open_modal:
            ctk.CTkButton(
                btn_box,
                text="⚙️ Detail Slider",
                command=self.on_open_modal,
                font=("Segoe UI", 9),
                fg_color="transparent",
                hover_color=("#E2E8F0", "#242938"),
                text_color=("#D97706", "#F59E0B"),
                width=80,
                height=22,
                corner_radius=6,
            ).pack(side="left", padx=(4, 0))

        # Content container where app cards or standby note is rendered
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="x", padx=12, pady=(0, 6))

    def refresh_apps(self):
        """Query active streaming and conference apps and update inline display."""
        now = time.time()
        # Scan every 2.0 seconds to prevent unnecessary process enumerations
        if now - self._last_scan_time < 2.0 and self.apps:
            return

        self._last_scan_time = now
        try:
            self.apps = BandwidthQoSEngine.get_active_media_apps()
        except Exception:
            self.apps = []

        self._render_app_cards()

    def _render_app_cards(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

        if not self.apps:
            # Standby message when no heavy media apps are open
            box = ctk.CTkFrame(self.content_frame, fg_color=("#F8FAFC", "#1A1D27"), corner_radius=6, height=32)
            box.pack(fill="x", pady=2)
            ctk.CTkLabel(
                box,
                text="ℹ️ Semua aplikasi berjalan normal. Buka Zoom, Google Meet, Teams, atau OBS Studio untuk memprioritaskan alokasi bandwidth internet Anda.",
                font=("Segoe UI", 9),
                text_color=("#64748B", "#94A3B8"),
            ).pack(side="left", padx=12, pady=5)
            return

        # Render active app cards horizontally
        apps_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        apps_row.pack(fill="x")

        # Display up to 4 top active apps in horizontal pills
        for app in self.apps[:4]:
            card = ctk.CTkFrame(
                apps_row,
                fg_color=("#F1F5F9", "#1A1D27"),
                corner_radius=8,
                border_width=1,
                border_color=("#E2E8F0", "#282C3D"),
            )
            card.pack(side="left", padx=4, pady=2, fill="x", expand=True)

            # Left app icon + name
            info_box = ctk.CTkFrame(card, fg_color="transparent")
            info_box.pack(side="left", padx=8, pady=4)

            name_lbl = ctk.CTkLabel(
                info_box,
                text=f"{app.icon} {app.friendly_name}",
                font=("Segoe UI", 10, "bold"),
                text_color=("#0F172A", "#F8FAFC"),
            )
            name_lbl.pack(anchor="w")

            # Rates
            rates_lbl = ctk.CTkLabel(
                info_box,
                text=f"↓ {app.dl_kbps:.0f} Kbps  ↑ {app.up_kbps:.0f} Kbps",
                font=("Consolas", 8),
                text_color=("#0284C7", "#38BDF8"),
            )
            rates_lbl.pack(anchor="w")

            # Right allocation bar & badge
            right_box = ctk.CTkFrame(card, fg_color="transparent")
            right_box.pack(side="right", padx=8, pady=4)

            # Category / Priority Badge
            cat_color = "#10B981" if app.category == "Video Conference" else ("#DC2626" if app.category == "Live Broadcast" else "#3B82F6")
            cat_badge = ctk.CTkLabel(
                right_box,
                text=f"{app.allocated_pct:.0f}% ALOKASI",
                font=("Segoe UI", 9, "bold"),
                text_color=cat_color,
            )
            cat_badge.pack(anchor="e")

            # Mini Progress Bar
            pbar = ctk.CTkProgressBar(right_box, width=65, height=5, corner_radius=3)
            pbar.configure(progress_color=cat_color, fg_color=("#CBD5E1", "#282C3D"))
            pbar.set(max(0.05, min(1.0, app.allocated_pct / 100.0)))
            pbar.pack(anchor="e", pady=(2, 0))

    def _apply_preset(self, preset_type: str):
        SoundEngine.play(SoundType.ACTION)
        if not self.apps:
            if self.on_toast:
                self.on_toast("info", "Tidak ada aplikasi media aktif. Buka Zoom, Teams, atau OBS terlebih dahulu.")
            return

        allocs = BandwidthQoSEngine.calculate_preset(preset_type, self.apps)
        for app in self.apps:
            if app.name in allocs:
                app.allocated_pct = allocs[app.name]

        # Apply system NetQoS policies
        BandwidthQoSEngine.apply_qos_policy(allocs)

        SoundEngine.play(SoundType.SUCCESS)
        self._render_app_cards()

        preset_titles = {
            "conference": "🎥 Prioritas Video Conference (75%) Diaktifkan!",
            "streaming": "🔴 Prioritas Live Streaming (75%) Diaktifkan!",
            "balanced": "⚖️ Alokasi Bandwidth Seimbang Diterapkan!",
        }
        msg = preset_titles.get(preset_type, "Prioritas QoS Berhasil Diperbarui!")
        if self.on_toast:
            self.on_toast("success", msg)

    def update_stats(self):
        """Update active app stats."""
        self.refresh_apps()

    def _boost_meeting(self):
        self._apply_preset("conference")
        if hasattr(self, "mode_label"):
            self.mode_label.configure(text="MODE: 🎥 MEETING")

    def _boost_streaming(self):
        self._apply_preset("streaming")
        if hasattr(self, "mode_label"):
            self.mode_label.configure(text="MODE: 🔴 STREAMING")

    def _balance_all(self):
        self._apply_preset("balanced")
        if hasattr(self, "mode_label"):
            self.mode_label.configure(text="MODE: ⚖️ SEIMBANG")
