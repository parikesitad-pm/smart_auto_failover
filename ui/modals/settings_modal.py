"""
MODULA - Smart Auto Failover
Settings Modal: Custom Ping Targets & Keyboard Shortcuts Manager (v2.3)
"""

import re
from typing import Callable, Dict, Optional
import customtkinter as ctk

from core.models import DEFAULT_SHORTCUTS, FailoverConfig
from core.sound_engine import SoundEngine, SoundType


class SettingsModal(ctk.CTkToplevel):
    """
    Comprehensive Configuration Modal for MODULA:
    - Custom Ping Targets (Simple IP entry & Advanced ICMP/TCP Probing parameters)
    - Custom Keyboard Shortcuts Manager with Hot-Remapping
    """

    def __init__(self, master, config: FailoverConfig, on_save: Optional[Callable[[FailoverConfig], None]] = None):
        super().__init__(master)
        self.title("⚙️ MODULA • Pengaturan Jaringan & Shortcut")
        self.geometry("720x620")
        self.minsize(640, 520)

        self.config = config
        self.on_save = on_save

        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 6), sticky="ew")

        ctk.CTkLabel(
            header,
            text="⚙️ MODULA Configuration & Probing Engine",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Kustomisasi IP target probing ICMP, interval failover, dan shortcut keyboard.",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # 2. Main Tab View
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#2D3139"),
            fg_color=("#FFFFFF", "#181A22"),
            segmented_button_selected_color="#D97706",
            segmented_button_selected_hover_color="#B45309",
        )
        self.tabview.grid(row=1, column=0, padx=20, pady=6, sticky="nsew")

        # Tab 1: Ping Targets
        self.tab_ping = self.tabview.add("🎯 Custom Ping & Probing")
        # Tab 2: Shortcuts
        self.tab_shortcuts = self.tabview.add("⌨️ Keyboard Shortcuts")

        self._build_ping_tab()
        self._build_shortcuts_tab()

        # 3. Bottom Action Bar
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, padx=20, pady=(6, 14), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self.msg_label = ctk.CTkLabel(
            bottom,
            text="",
            font=("Segoe UI", 10, "bold"),
            text_color=("#10B981", "#34D399"),
        )
        self.msg_label.grid(row=0, column=0, sticky="w")

        btns_box = ctk.CTkFrame(bottom, fg_color="transparent")
        btns_box.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            btns_box,
            text="Batal",
            command=self.destroy,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=80,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btns_box,
            text="💾 Simpan & Terapkan",
            command=self._save_settings,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#D97706", "#F59E0B"),
            hover_color=("#B45309", "#D97706"),
            text_color=("#FFFFFF", "#0F172A"),
            width=150,
            height=32,
        ).pack(side="left")

    def _build_ping_tab(self):
        tab = self.tab_ping
        tab.grid_columnconfigure(0, weight=1)

        # Mode Switcher (Simple vs Advanced)
        mode_box = ctk.CTkFrame(tab, fg_color="transparent")
        mode_box.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(
            mode_box,
            text="Pilih Mode Konfigurasi:",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(side="left", padx=(0, 10))

        self.ping_mode_seg = ctk.CTkSegmentedButton(
            mode_box,
            values=["Simple (Hanya IP Target)", "Advanced (Full Probing Tuning)"],
            command=self._on_ping_mode_changed,
            font=("Segoe UI", 10, "bold"),
            width=260,
        )
        self.ping_mode_seg.set("Simple (Hanya IP Target)")
        self.ping_mode_seg.pack(side="left")

        # Presets Bar
        preset_box = ctk.CTkFrame(
            tab,
            fg_color=("#F8FAFC", "#1E222D"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#2E3345"),
        )
        preset_box.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            preset_box,
            text="PRESET IP CEPAT:",
            font=("Segoe UI", 9, "bold"),
            text_color=("#64748B", "#94A3B8"),
        ).pack(side="left", padx=10, pady=8)

        ctk.CTkButton(
            preset_box,
            text="🌐 Cloudflare + Google + Quad9",
            command=lambda: self._apply_ip_preset("1.1.1.1", "8.8.8.8", "9.9.9.9"),
            font=("Segoe UI", 9, "bold"),
            fg_color=("#E2E8F0", "#2A2E3D"),
            hover_color=("#CBD5E1", "#3B4254"),
            text_color=("#0F172A", "#F8FAFC"),
            height=24,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            preset_box,
            text="🛡️ OpenDNS + Google",
            command=lambda: self._apply_ip_preset("208.67.222.222", "8.8.8.8", "1.1.1.1"),
            font=("Segoe UI", 9, "bold"),
            fg_color=("#E2E8F0", "#2A2E3D"),
            hover_color=("#CBD5E1", "#3B4254"),
            text_color=("#0F172A", "#F8FAFC"),
            height=24,
        ).pack(side="left", padx=4)

        # Simple IP Frame
        self.simple_ip_frame = ctk.CTkFrame(
            tab,
            fg_color=("#F8FAFC", "#1E222D"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#2E3345"),
        )
        self.simple_ip_frame.pack(fill="x", pady=4, padx=2)

        # Target 1 (Primary)
        self.t1_entry = self._create_ip_field(
            self.simple_ip_frame,
            "Target Primer (P1 / Active Backbone):",
            self.config.ping_target_primary,
            "1.1.1.1",
            "Anycast global dengan peering latensi terendah (Cloudflare DNS)",
            row=0,
        )

        # Target 2 (Secondary)
        self.t2_entry = self._create_ip_field(
            self.simple_ip_frame,
            "Target Sekunder (P2 / Verifikasi):",
            self.config.ping_target_secondary,
            "8.8.8.8",
            "Mencegah false positive jika node primer ada maintenance (Google DNS)",
            row=1,
        )

        # Target 3 (Tertiary)
        self.t3_entry = self._create_ip_field(
            self.simple_ip_frame,
            "Target Tersier (P3 / Redundansi Tambahan):",
            self.config.ping_target_tertiary,
            "9.9.9.9",
            "Redundansi Swiss/Global untuk konfirmasi rute darurat (Quad9 DNS)",
            row=2,
        )

        # Advanced Tuning Frame
        self.adv_frame = ctk.CTkFrame(
            tab,
            fg_color=("#F8FAFC", "#1E222D"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#2E3345"),
        )
        # Hidden by default in simple mode
        self._build_advanced_tuning()

    def _create_ip_field(self, parent, label: str, val: str, placeholder: str, hint: str, row: int) -> ctk.CTkEntry:
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(
            box,
            text=label,
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(anchor="w")

        entry = ctk.CTkEntry(
            box,
            placeholder_text=placeholder,
            font=("Consolas", 11),
            height=30,
        )
        entry.insert(0, val)
        entry.pack(fill="x", pady=(2, 2))

        ctk.CTkLabel(
            box,
            text=f"💡 {hint}",
            font=("Segoe UI", 9),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        return entry

    def _build_advanced_tuning(self):
        f = self.adv_frame

        # Probing Interval & Timeout
        row1 = ctk.CTkFrame(f, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=6)
        row1.grid_columnconfigure((0, 1), weight=1)

        # Interval
        b1 = ctk.CTkFrame(row1, fg_color="transparent")
        b1.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(b1, text="Interval Probing (Detik):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.interval_entry = ctk.CTkEntry(b1, font=("Consolas", 11), height=28)
        self.interval_entry.insert(0, str(self.config.ping_interval_sec))
        self.interval_entry.pack(fill="x", pady=2)
        ctk.CTkLabel(b1, text="Standar: 1.0s (Cepat & hemat bandwidth)", font=("Segoe UI", 8), text_color="#64748B").pack(anchor="w")

        # Timeout
        b2 = ctk.CTkFrame(row1, fg_color="transparent")
        b2.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(b2, text="Timeout Ping (Milidetik):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.timeout_entry = ctk.CTkEntry(b2, font=("Consolas", 11), height=28)
        self.timeout_entry.insert(0, str(self.config.ping_timeout_ms))
        self.timeout_entry.pack(fill="x", pady=2)
        ctk.CTkLabel(b2, text="Standar: 800ms (Sebelum dianggap RTO)", font=("Segoe UI", 8), text_color="#64748B").pack(anchor="w")

        # RTO Threshold & Recovery Threshold
        row2 = ctk.CTkFrame(f, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=6)
        row2.grid_columnconfigure((0, 1), weight=1)

        # RTO Threshold
        b3 = ctk.CTkFrame(row2, fg_color="transparent")
        b3.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(b3, text="Ambang Batas RTO (Failover Threshold):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.rto_entry = ctk.CTkEntry(b3, font=("Consolas", 11), height=28)
        self.rto_entry.insert(0, str(self.config.failover_rto_threshold))
        self.rto_entry.pack(fill="x", pady=2)
        ctk.CTkLabel(b3, text="Standar: 2 kali RTO langsung failover (<2s)", font=("Segoe UI", 8), text_color="#64748B").pack(anchor="w")

        # Recovery Threshold
        b4 = ctk.CTkFrame(row2, fg_color="transparent")
        b4.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(b4, text="Ambang Batas Pemulihan (Anti-Flapping):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.rec_entry = ctk.CTkEntry(b4, font=("Consolas", 11), height=28)
        self.rec_entry.insert(0, str(self.config.recovery_success_threshold))
        self.rec_entry.pack(fill="x", pady=2)
        ctk.CTkLabel(b4, text="Standar: 5x berturut-turut sukses", font=("Segoe UI", 8), text_color="#64748B").pack(anchor="w")

        # Payload Size & Protocol
        row3 = ctk.CTkFrame(f, fg_color="transparent")
        row3.pack(fill="x", padx=14, pady=6)
        row3.grid_columnconfigure((0, 1), weight=1)

        # Payload Size
        b5 = ctk.CTkFrame(row3, fg_color="transparent")
        b5.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(b5, text="Ukuran Paket Payload (Bytes):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.payload_entry = ctk.CTkEntry(b5, font=("Consolas", 11), height=28)
        self.payload_entry.insert(0, str(getattr(self.config, "ping_payload_size", 32)))
        self.payload_entry.pack(fill="x", pady=2)
        ctk.CTkLabel(b5, text="Standar ICMP: 32 bytes (Ringan)", font=("Segoe UI", 8), text_color="#64748B").pack(anchor="w")

        # Source IP Binding Switch
        b6 = ctk.CTkFrame(row3, fg_color="transparent")
        b6.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(b6, text="Source IP Binding Interface:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.bind_switch = ctk.CTkSwitch(
            b6,
            text="Aktifkan Multi-Interface Bind (-S)",
            font=("Segoe UI", 10),
            progress_color="#D97706",
        )
        if getattr(self.config, "source_ip_binding", True):
            self.bind_switch.select()
        else:
            self.bind_switch.deselect()
        self.bind_switch.pack(anchor="w", pady=4)
        ctk.CTkLabel(b6, text="Uji jalur LAN 1, LAN 2, Wi-Fi secara independen", font=("Segoe UI", 8), text_color="#64748B").pack(anchor="w")

    def _on_ping_mode_changed(self, mode: str):
        SoundEngine.play(SoundType.ACTION)
        if "Advanced" in mode:
            self.adv_frame.pack(fill="x", pady=4, padx=2)
        else:
            self.adv_frame.pack_forget()

    def _apply_ip_preset(self, p1: str, p2: str, p3: str):
        SoundEngine.play(SoundType.ACTION)
        self.t1_entry.delete(0, "end")
        self.t1_entry.insert(0, p1)
        self.t2_entry.delete(0, "end")
        self.t2_entry.insert(0, p2)
        self.t3_entry.delete(0, "end")
        self.t3_entry.insert(0, p3)
        self.msg_label.configure(text=f"Preset {p1}, {p2}, {p3} dipilih!", text_color=("#059669", "#10B981"))

    def _build_shortcuts_tab(self):
        tab = self.tab_shortcuts
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab,
            text="Kustomisasi Tombol Pintas (Keyboard Shortcuts):",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(anchor="w", pady=(4, 8))

        scroll = ctk.CTkScrollableFrame(
            tab,
            fg_color=("#F8FAFC", "#1E222D"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#2E3345"),
            height=320,
        )
        scroll.pack(fill="both", expand=True, pady=4)
        scroll.grid_columnconfigure(1, weight=1)

        self.shortcut_entries: Dict[str, ctk.CTkEntry] = {}

        action_labels = {
            "fullscreen": ("Layar Penuh (Toggle Fullscreen)", "Masuk / keluar layar penuh"),
            "refresh": ("Refresh & Preloader Semua Modul", "Panggil preloader & hardware rescan"),
            "toggle_monitoring": ("Mulai / Berhenti Monitoring", "Toggle failover engine"),
            "speedtest": ("Buka Modal Speedtest 4-Engine", "Akses benchmark kecepatan"),
            "bandwidth_qos": ("Buka Bandwidth QoS Allocator", "Atur prioritas Zoom / OBS / Stream"),
            "toggle_sound": ("Mute / Unmute Efek Suara", "Saklar audio notifikasi global"),
            "settings": ("Buka Pengaturan & Custom Ping", "Buka jendela settings ini"),
        }

        current_shortcuts = getattr(self.config, "shortcuts", DEFAULT_SHORTCUTS) or DEFAULT_SHORTCUTS

        for i, (key, (title, desc)) in enumerate(action_labels.items()):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=6)
            row.grid_columnconfigure(0, weight=1)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left")

            ctk.CTkLabel(left, text=title, font=("Segoe UI", 11, "bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=desc, font=("Segoe UI", 9), text_color=("#64748B", "#94A3B8")).pack(anchor="w")

            val = current_shortcuts.get(key, DEFAULT_SHORTCUTS.get(key, ""))
            entry = ctk.CTkEntry(row, font=("Consolas", 11, "bold"), width=130, height=28)
            entry.insert(0, val)
            entry.pack(side="right", padx=6)
            self.shortcut_entries[key] = entry

        # Reset button
        reset_bar = ctk.CTkFrame(tab, fg_color="transparent")
        reset_bar.pack(fill="x", pady=(8, 2))

        ctk.CTkButton(
            reset_bar,
            text="🔄 Kembalikan Shortcut ke Standar",
            command=self._reset_shortcuts_to_default,
            font=("Segoe UI", 10),
            fg_color=("#E2E8F0", "#2D3139"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            height=26,
        ).pack(side="left")

    def _reset_shortcuts_to_default(self):
        SoundEngine.play(SoundType.ACTION)
        for k, v in DEFAULT_SHORTCUTS.items():
            if k in self.shortcut_entries:
                self.shortcut_entries[k].delete(0, "end")
                self.shortcut_entries[k].insert(0, v)
        self.msg_label.configure(text="Shortcut dikembalikan ke default!", text_color=("#059669", "#10B981"))

    def _save_settings(self):
        # 1. Validate IP targets
        ip_regex = r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
        t1 = self.t1_entry.get().strip()
        t2 = self.t2_entry.get().strip()
        t3 = self.t3_entry.get().strip()

        if not t1 or not re.match(ip_regex, t1):
            self.msg_label.configure(text="❌ Target Primer tidak valid (harus IPv4, misal: 1.1.1.1)", text_color="#EF4444")
            return

        if t2 and not re.match(ip_regex, t2):
            self.msg_label.configure(text="❌ Target Sekunder tidak valid (harus IPv4, misal: 8.8.8.8)", text_color="#EF4444")
            return

        if t3 and not re.match(ip_regex, t3):
            self.msg_label.configure(text="❌ Target Tersier tidak valid (harus IPv4, misal: 9.9.9.9)", text_color="#EF4444")
            return

        self.config.ping_target_primary = t1
        self.config.ping_target_secondary = t2 or "8.8.8.8"
        self.config.ping_target_tertiary = t3 or "9.9.9.9"

        # 2. Advanced settings
        try:
            self.config.ping_interval_sec = max(0.2, float(self.interval_entry.get().strip()))
            self.config.ping_timeout_ms = max(100, int(self.timeout_entry.get().strip()))
            self.config.failover_rto_threshold = max(1, int(self.rto_entry.get().strip()))
            self.config.recovery_success_threshold = max(1, int(self.rec_entry.get().strip()))
            self.config.ping_payload_size = max(0, int(self.payload_entry.get().strip()))
            self.config.source_ip_binding = bool(self.bind_switch.get())
        except Exception as e:
            self.msg_label.configure(text=f"❌ Nilai parameter lanjutan tidak valid: {e}", text_color="#EF4444")
            return

        # 3. Shortcuts
        new_shortcuts = {}
        for k, entry in self.shortcut_entries.items():
            new_shortcuts[k] = entry.get().strip()
        self.config.shortcuts = new_shortcuts

        SoundEngine.play(SoundType.SUCCESS)
        if self.on_save:
            self.on_save(self.config)

        self.destroy()
