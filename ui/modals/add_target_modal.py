"""
MODULA - Smart Auto Failover v2.6
Modal dialog to add, edit, or remove the 4th custom ICMP ping target.
Spawns the 4th circular backbone tachometer gauge on the sports car cluster.
"""
import re
from typing import Callable, Optional
import customtkinter as ctk

from core.sound_engine import SoundEngine, SoundType


class AddTargetModal(ctk.CTkToplevel):
    """
    Popup dialog to add, edit, or remove the 4th ICMP target IP.
    """

    def __init__(
        self,
        master,
        current_ip: str = "",
        on_save: Optional[Callable[[str], None]] = None,
        config=None,
        on_saved: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(master)
        self.title("➕ Target ICMP Backbone ke-4 • MODULA v2.6")
        self.geometry("540x380")
        self.minsize(460, 320)

        self.transient(master)
        self.grab_set()

        # Support both (current_ip, on_save) and (config, on_saved) signatures
        if config is not None and not current_ip:
            current_ip = getattr(config, "ping_target_quaternary", "")
        self.on_save = on_saved if on_saved is not None else on_save
        self.current_ip = current_ip.strip()

        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 10))

        ctk.CTkLabel(
            hdr,
            text="➕ Tambah IP Target Pengujian ke-4",
            font=("Segoe UI", 15, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            hdr,
            text="Tambahkan 1 alamat server tambahan untuk redundansi pengujian koneksi.\nKluster instrumen otomatis menampilkan dial sirkular ICMP ke-4 (100% circular dial).",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        # Main Input Card
        card = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#181A24"),
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
        )
        card.pack(fill="x", padx=24, pady=8)

        ctk.CTkLabel(
            card,
            text="Alamat IP Target ke-4 (IPv4):",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.ip_entry = ctk.CTkEntry(
            card,
            placeholder_text="Contoh: 1.0.0.1 atau 208.67.222.222 atau 192.168.1.1",
            font=("Consolas", 12),
            height=34,
        )
        self.ip_entry.pack(fill="x", padx=16, pady=(0, 8))
        if self.current_ip:
            self.ip_entry.insert(0, self.current_ip)

        # Presets Bar
        preset_box = ctk.CTkFrame(card, fg_color="transparent")
        preset_box.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            preset_box,
            text="Preset Rekomendasi:",
            font=("Segoe UI", 9, "bold"),
            text_color=("#64748B", "#94A3B8"),
        ).pack(side="left", padx=(0, 6))

        for name, ip_val in [
            ("⚡ Cloudflare 1.0.0.1", "1.0.0.1"),
            ("🛡️ OpenDNS", "208.67.222.222"),
            ("🏠 Router Lokal", "192.168.1.1"),
        ]:
            ctk.CTkButton(
                preset_box,
                text=name,
                command=lambda val=ip_val: self._set_ip_preset(val),
                font=("Segoe UI", 9),
                fg_color=("#E2E8F0", "#282C3D"),
                hover_color=("#CBD5E1", "#374151"),
                text_color=("#0F172A", "#F8FAFC"),
                height=22,
                corner_radius=5,
            ).pack(side="left", padx=2)

        # Error / Feedback label
        self.err_lbl = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 10, "bold"),
            text_color="#EF4444",
        )
        self.err_lbl.pack(pady=2)

        # Bottom Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=24, pady=(6, 16))

        if self.current_ip:
            ctk.CTkButton(
                btn_box,
                text="🗑️ Hapus Target 4",
                command=self._delete_target,
                font=("Segoe UI", 11),
                fg_color=("#FEE2E2", "#7F1D1D"),
                hover_color=("#FECACA", "#991B1B"),
                text_color=("#991B1B", "#FCA5A5"),
                width=120,
                height=32,
                corner_radius=6,
            ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text="Batal",
            command=self.destroy,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#282C3D"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=80,
            height=32,
            corner_radius=6,
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_box,
            text="💾 Simpan & Aktifkan",
            command=self._save_target,
            font=("Segoe UI", 11, "bold"),
            fg_color=("#D97706", "#F59E0B"),
            hover_color=("#B45309", "#D97706"),
            text_color=("#FFFFFF", "#0F172A"),
            width=160,
            height=32,
            corner_radius=6,
        ).pack(side="right")

    def _set_ip_preset(self, val: str):
        self.ip_entry.delete(0, "end")
        self.ip_entry.insert(0, val)
        self.err_lbl.configure(text="")

    def _delete_target(self):
        SoundEngine.play(SoundType.ACTION)
        if self.on_save:
            self.on_save("")
        self.destroy()

    def _save_target(self):
        val = self.ip_entry.get().strip()
        if not val:
            self.err_lbl.configure(text="Alamat IP tidak boleh kosong.", text_color="#EF4444")
            return

        # Validate IPv4 format
        pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
        m = re.match(pattern, val)
        if not m or any(int(octet) > 255 for octet in m.groups()):
            self.err_lbl.configure(text="Format IP tidak valid! Masukkan IPv4 seperti 1.0.0.1", text_color="#EF4444")
            return

        SoundEngine.play(SoundType.SUCCESS)
        if self.on_save:
            self.on_save(val)
        self.destroy()
