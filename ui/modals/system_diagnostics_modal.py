import os
import tkinter as tk
from typing import Optional
import customtkinter as ctk

from core.sound_engine import SoundEngine, SoundType
from core.system_telemetry import HardwareSpecs, SystemTelemetry


class SystemDiagnosticsModal(ctk.CTkToplevel):
    """
    MODULA System Diagnostics & CCleaner-Style Junk Maintenance Hub.
    Displays Linux Fastfetch-style PC hardware specifications, live CPU/RAM gauges,
    and provides a 1-click cleaner for obsolete builds and temporary cache files.
    """

    def __init__(self, master, project_root: Optional[str] = None, on_cleaned: Optional[callable] = None):
        super().__init__(master)
        self.title("💻 MODULA • System Diagnostics & CCleaner Clean Hub")
        self.geometry("740x660")
        self.minsize(680, 560)

        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.on_cleaned = on_cleaned
        self.specs: HardwareSpecs = SystemTelemetry.get_hardware_specs()

        self.transient(master)
        self.grab_set()

        self._build_ui()
        self._scan_junk_status()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text="💻 MODULA Hardware Telemetry & Maintenance Hub",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Informasi Sistem ala Fastfetch • Live Resource Monitor • CCleaner Build Cleaner",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # 2. Main Scrollable Container
        scroll_box = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        scroll_box.grid(row=1, column=0, padx=20, pady=6, sticky="nsew")
        scroll_box.grid_columnconfigure(0, weight=1)

        # 2a. Fastfetch Hardware Card
        ff_card = ctk.CTkFrame(
            scroll_box,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#242938"),
            fg_color=("#F8FAFC", "#10121A"),
        )
        ff_card.pack(fill="x", padx=4, pady=6)
        ff_card.grid_columnconfigure(1, weight=1)

        # Fastfetch Title
        ctk.CTkLabel(
            ff_card,
            text="🐧 FASTFETCH HARDWARE REPORT",
            font=("Consolas", 10, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).grid(row=0, column=0, columnspan=2, padx=14, pady=(10, 6), sticky="w")

        specs_rows = [
            ("OS", self.specs.os_name, "#38BDF8"),
            ("Host", self.specs.model_name, "#F59E0B"),
            ("CPU", self.specs.cpu_name, "#34D399"),
            ("GPU (Integrated)", self.specs.gpu_integrated, "#60A5FA"),
            ("GPU (Discrete)", self.specs.gpu_discrete, "#A78BFA"),
            ("Memory", f"{self.specs.ram_used_gib} GiB / {self.specs.ram_total_gib} GiB ({self.specs.ram_percent}%)", "#F43F5E"),
        ]

        for idx, (label, val, col) in enumerate(specs_rows, start=1):
            ctk.CTkLabel(
                ff_card,
                text=f"{label}:",
                font=("Consolas", 11, "bold"),
                text_color=("#64748B", "#94A3B8"),
            ).grid(row=idx, column=0, padx=(14, 8), pady=2, sticky="w")

            ctk.CTkLabel(
                ff_card,
                text=val,
                font=("Consolas", 11),
                text_color=col,
            ).grid(row=idx, column=1, padx=4, pady=2, sticky="w")

        # Disks rows
        disk_row_start = len(specs_rows) + 1
        for d_idx, d in enumerate(self.specs.disks):
            ctk.CTkLabel(
                ff_card,
                text=f"Disk ({d['device']}):",
                font=("Consolas", 11, "bold"),
                text_color=("#64748B", "#94A3B8"),
            ).grid(row=disk_row_start + d_idx, column=0, padx=(14, 8), pady=2, sticky="w")

            ctk.CTkLabel(
                ff_card,
                text=d['summary'],
                font=("Consolas", 11),
                text_color="#FBBF24",
            ).grid(row=disk_row_start + d_idx, column=1, padx=4, pady=2, sticky="w")

        # 2b. Live CPU & RAM Performance Bar
        perf_card = ctk.CTkFrame(
            scroll_box,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#242938"),
            fg_color=("#F8FAFC", "#1E222D"),
        )
        perf_card.pack(fill="x", padx=4, pady=6)
        perf_card.grid_columnconfigure(0, weight=1)
        perf_card.grid_columnconfigure(1, weight=1)

        # CPU Meter
        cpu_box = ctk.CTkFrame(perf_card, fg_color="transparent")
        cpu_box.grid(row=0, column=0, padx=12, pady=10, sticky="ew")

        cpu, ram, ram_txt = SystemTelemetry.get_live_cpu_ram()
        self.cpu_lbl = ctk.CTkLabel(
            cpu_box,
            text=f"CPU USAGE: {cpu:.1f}%",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        self.cpu_lbl.pack(anchor="w")

        self.cpu_bar = ctk.CTkProgressBar(cpu_box, height=8, progress_color=("#D97706", "#F59E0B"))
        self.cpu_bar.set(cpu / 100.0)
        self.cpu_bar.pack(fill="x", pady=4)

        # RAM Meter
        ram_box = ctk.CTkFrame(perf_card, fg_color="transparent")
        ram_box.grid(row=0, column=1, padx=12, pady=10, sticky="ew")

        self.ram_lbl = ctk.CTkLabel(
            ram_box,
            text=f"RAM USAGE: {ram:.1f}% ({ram_txt})",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        self.ram_lbl.pack(anchor="w")

        self.ram_bar = ctk.CTkProgressBar(ram_box, height=8, progress_color=("#DC2626", "#E11D48"))
        self.ram_bar.set(ram / 100.0)
        self.ram_bar.pack(fill="x", pady=4)

        # 2c. CCleaner-Style Junk Cleaner Tool Card
        clean_card = ctk.CTkFrame(
            scroll_box,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#242938"),
            fg_color=("#F8FAFC", "#1E222D"),
        )
        clean_card.pack(fill="x", padx=4, pady=6)
        clean_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            clean_card,
            text="🧹 CCLEANER PROYEK • PEMBERSIH BUILD LAMA & SAMPAH",
            font=("Segoe UI", 11, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.junk_status_lbl = ctk.CTkLabel(
            clean_card,
            text="Memindai folder build lama (dist/, build/, pycache)...",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
            justify="left",
        )
        self.junk_status_lbl.pack(anchor="w", padx=14, pady=2)

        self.clean_btn = ctk.CTkButton(
            clean_card,
            text="🧹 Bersihkan File Sampah & Build Lama",
            command=self._do_clean_junk,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#DC2626", "#E11D48"),
            hover_color=("#B91C1C", "#BE123C"),
            height=32,
            width=260,
        )
        self.clean_btn.pack(anchor="w", padx=14, pady=(8, 12))

        # 3. Bottom Close Button
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, padx=20, pady=10, sticky="e")

        ctk.CTkButton(
            bottom,
            text="Tutup",
            command=self.destroy,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#242938"),
            text_color=("#0F172A", "#F8FAFC"),
            width=90,
            height=30,
        ).pack(side="right")

    def _scan_junk_status(self):
        items, total_bytes = SystemTelemetry.scan_junk(self.project_root)
        mb = total_bytes / (1024 * 1024)
        if items:
            self.junk_status_lbl.configure(
                text=f"Ditemukan {len(items)} item sampah & build lama ({mb:.1f} MB) yang dapat dibersihkan.",
                text_color=("#DC2626", "#F87171"),
            )
            self.clean_btn.configure(state="normal")
        else:
            self.junk_status_lbl.configure(
                text="Direktori proyek bersih! Tidak ada folder build lama yang menumpuk.",
                text_color=("#059669", "#10B981"),
            )
            self.clean_btn.configure(state="disabled")

    def _do_clean_junk(self):
        SoundEngine.play(SoundType.CLEAN_COMPLETE)
        cnt, freed, msg = SystemTelemetry.clean_junk(self.project_root)
        self._scan_junk_status()
        if self.on_cleaned:
            self.on_cleaned(cnt, freed, msg)
