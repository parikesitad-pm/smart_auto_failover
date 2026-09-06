import threading
import tkinter as tk
from typing import Dict, List, Optional
import customtkinter as ctk

from core.bandwidth_qos import AppTrafficInfo, BandwidthQoSEngine
from core.sound_engine import SoundEngine, SoundType


class BandwidthQoSModal(ctk.CTkToplevel):
    """
    MODULA Interactive Application Bandwidth Allocation & QoS Modal.
    Allows users to allocate bandwidth percentages across Zoom, OBS, vMix, Spotify, etc.
    """

    def __init__(self, master, on_applied: Optional[callable] = None):
        super().__init__(master)
        self.title("🎛️ MODULA • Bandwidth Allocation & App QoS Manager")
        self.geometry("740x640")
        self.minsize(660, 520)

        self.on_applied = on_applied
        self.apps: List[AppTrafficInfo] = []
        self.slider_vars: Dict[str, ctk.DoubleVar] = {}
        self.slider_labels: Dict[str, ctk.CTkLabel] = {}
        self.rate_labels: Dict[str, ctk.CTkLabel] = {}

        self.transient(master)
        self.grab_set()

        self._build_ui()
        self._load_apps()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="ew")

        ctk.CTkLabel(
            header,
            text="🎛️ MODULA Bandwidth Allocation & App Prioritizer",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Alokasikan total bandwidth internet laptop ke aplikasi spesifik (Zoom, OBS, vMix, Spotify) agar video stream tidak tersendat.",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # 2. Preset Quick-Select Row
        presets_box = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        presets_box.grid(row=1, column=0, padx=20, pady=6, sticky="ew")

        ctk.CTkLabel(
            presets_box,
            text="PROFIL ALOKASI CEPAT:",
            font=("Segoe UI", 10, "bold"),
            text_color=("#64748B", "#94A3B8"),
        ).pack(side="left", padx=12, pady=10)

        btn_zoom = ctk.CTkButton(
            presets_box,
            text="🎥 Zoom VIP (75%)",
            command=self._preset_zoom_vip,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#D97706", "#F59E0B"),
            hover_color=("#B45309", "#D97706"),
            text_color=("#FFFFFF", "#0F172A"),
            height=28,
            width=130,
        )
        btn_zoom.pack(side="left", padx=4)

        btn_obs = ctk.CTkButton(
            presets_box,
            text="🔴 Broadcast (70%)",
            command=self._preset_broadcast,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#DC2626", "#E11D48"),
            hover_color=("#B91C1C", "#BE123C"),
            height=28,
            width=135,
        )
        btn_obs.pack(side="left", padx=4)

        btn_balance = ctk.CTkButton(
            presets_box,
            text="⚖️ Seimbang",
            command=self._preset_balanced,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#242938"),
            text_color=("#0F172A", "#F8FAFC"),
            height=28,
            width=90,
        )
        btn_balance.pack(side="left", padx=4)

        refresh_btn = ctk.CTkButton(
            presets_box,
            text="🔄 Scan Apps",
            command=self._load_apps,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#242938"),
            text_color=("#0F172A", "#F8FAFC"),
            height=28,
            width=90,
        )
        refresh_btn.pack(side="right", padx=12)

        # 3. Scrollable List of Apps with Sliders
        self.app_list_box = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        self.app_list_box.grid(row=2, column=0, padx=20, pady=6, sticky="nsew")
        self.app_list_box.grid_columnconfigure(1, weight=1)

        # 4. Bottom Total & Apply Bar
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, padx=20, pady=(4, 12), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self.total_label = ctk.CTkLabel(
            bottom,
            text="Total Alokasi: 100% • DSCP Expedited Forwarding Aktif",
            font=("Segoe UI", 11, "bold"),
            text_color=("#059669", "#10B981"),
        )
        self.total_label.grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        self.apply_btn = ctk.CTkButton(
            btn_box,
            text="⚡ Terapkan Alokasi Bandwidth",
            command=self._apply_allocation,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#D97706", "#F59E0B"),
            hover_color=("#B45309", "#D97706"),
            text_color=("#FFFFFF", "#0F172A"),
            height=34,
            width=220,
        )
        self.apply_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="Tutup",
            command=self.destroy,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#242938"),
            text_color=("#0F172A", "#F8FAFC"),
            height=34,
            width=80,
        ).pack(side="left")

    def _load_apps(self):
        SoundEngine.play(SoundType.ACTION)
        # Clear previous items
        for widget in self.app_list_box.winfo_children():
            widget.destroy()

        self.slider_vars.clear()
        self.slider_labels.clear()
        self.rate_labels.clear()

        self.apps = BandwidthQoSEngine.get_active_media_apps()

        if not self.apps:
            # Add simulation entries for Zoom and OBS so user can still customize even if not currently running
            self.apps = [
                AppTrafficInfo(pid=0, name="Zoom.exe", friendly_name="Zoom Meeting", icon="🎥", exe_path="C:\\Zoom\\bin\\Zoom.exe", allocated_pct=70.0),
                AppTrafficInfo(pid=0, name="obs64.exe", friendly_name="OBS Studio", icon="🔴", exe_path="C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe", allocated_pct=20.0),
                AppTrafficInfo(pid=0, name="Spotify.exe", friendly_name="Spotify Music", icon="🎵", exe_path="C:\\Spotify\\Spotify.exe", allocated_pct=5.0),
                AppTrafficInfo(pid=0, name="chrome.exe", friendly_name="Google Chrome", icon="🌐", exe_path="C:\\Chrome\\chrome.exe", allocated_pct=5.0),
            ]

        is_dark = (ctk.get_appearance_mode() == "Dark")

        for idx, app in enumerate(self.apps):
            card = ctk.CTkFrame(
                self.app_list_box,
                corner_radius=8,
                border_width=1,
                border_color=("#E2E8F0", "#242938"),
                fg_color=("#F8FAFC", "#1E222D"),
            )
            card.pack(fill="x", pady=4, padx=4)
            card.grid_columnconfigure(1, weight=1)

            # Left: Icon & Name
            left_info = ctk.CTkFrame(card, fg_color="transparent")
            left_info.grid(row=0, column=0, padx=12, pady=10, sticky="w")

            icon_lbl = ctk.CTkLabel(left_info, text=app.icon, font=("Segoe UI", 18))
            icon_lbl.pack(side="left", padx=(0, 8))

            name_box = ctk.CTkFrame(left_info, fg_color="transparent")
            name_box.pack(side="left")

            ctk.CTkLabel(
                name_box,
                text=app.friendly_name,
                font=("Segoe UI", 12, "bold"),
                text_color=("#0F172A", "#F8FAFC"),
            ).pack(anchor="w")

            rate_text = f"{app.name} • PID: {app.pid if app.pid else 'Standby'}"
            r_lbl = ctk.CTkLabel(
                name_box,
                text=rate_text,
                font=("Segoe UI", 9),
                text_color=("#64748B", "#94A3B8"),
            )
            r_lbl.pack(anchor="w")
            self.rate_labels[app.name] = r_lbl

            # Middle: Slider
            var = ctk.DoubleVar(value=app.allocated_pct)
            self.slider_vars[app.name] = var

            slider = ctk.CTkSlider(
                card,
                from_=0,
                to=100,
                variable=var,
                command=lambda val, name=app.name: self._on_slider_change(name, val),
                button_color=("#D97706", "#F59E0B"),
                progress_color=("#D97706", "#F59E0B"),
                height=16,
            )
            slider.grid(row=0, column=1, padx=16, pady=10, sticky="ew")

            # Right: Percentage display
            pct_lbl = ctk.CTkLabel(
                card,
                text=f"{int(app.allocated_pct)}%",
                font=("Segoe UI", 13, "bold"),
                text_color=("#D97706", "#F59E0B"),
                width=55,
            )
            pct_lbl.grid(row=0, column=2, padx=12, pady=10, sticky="e")
            self.slider_labels[app.name] = pct_lbl

        self._update_total_display()

    def _on_slider_change(self, name: str, val: float):
        int_val = int(val)
        if name in self.slider_labels:
            self.slider_labels[name].configure(text=f"{int_val}%")
        self._update_total_display()

    def _update_total_display(self):
        total = sum(int(v.get()) for v in self.slider_vars.values())
        if total == 100:
            self.total_label.configure(
                text=f"Total Alokasi: {total}% • Sempurna (100% Bandwidth)",
                text_color=("#059669", "#10B981"),
            )
            self.apply_btn.configure(state="normal")
        else:
            self.total_label.configure(
                text=f"Total Alokasi: {total}% (Sesuaikan agar total mencapai 100%)",
                text_color=("#DC2626", "#F87171"),
            )

    def _preset_zoom_vip(self):
        SoundEngine.play(SoundType.ACTION)
        for name, var in self.slider_vars.items():
            if "zoom" in name.lower():
                var.set(75)
            elif "obs" in name.lower() or "vmix" in name.lower():
                var.set(15)
            else:
                var.set(5)
            self.slider_labels[name].configure(text=f"{int(var.get())}%")
        self._update_total_display()

    def _preset_broadcast(self):
        SoundEngine.play(SoundType.ACTION)
        for name, var in self.slider_vars.items():
            if "obs" in name.lower() or "vmix" in name.lower():
                var.set(70)
            elif "zoom" in name.lower():
                var.set(20)
            else:
                var.set(5)
            self.slider_labels[name].configure(text=f"{int(var.get())}%")
        self._update_total_display()

    def _preset_balanced(self):
        SoundEngine.play(SoundType.ACTION)
        count = max(1, len(self.slider_vars))
        share = int(100 / count)
        for name, var in self.slider_vars.items():
            var.set(share)
            self.slider_labels[name].configure(text=f"{share}%")
        self._update_total_display()

    def _apply_allocation(self):
        allocations = {name: var.get() for name, var in self.slider_vars.items()}
        SoundEngine.play(SoundType.QOS_APPLIED)
        ok, msg = BandwidthQoSEngine.apply_qos_policy(allocations)
        if self.on_applied:
            self.on_applied(allocations, msg)
        self.destroy()
