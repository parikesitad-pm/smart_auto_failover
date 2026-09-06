import os
import tkinter as tk
from typing import Optional
import customtkinter as ctk

from core.sound_engine import SoundEngine, SoundType
from core.system_telemetry import HardwareSpecs, SystemTelemetry


class SystemDiagnosticsModal(ctk.CTkToplevel):
    """
    MODULA System Diagnostics & Fastfetch-Style Hardware Telemetry Hub.
    Displays Linux Fastfetch-style PC hardware specifications, live CPU/RAM gauges,
    rolling resource history graph, and active high-load process telemetry.
    """

    def __init__(self, master, project_root: Optional[str] = None):
        super().__init__(master)
        self.title("💻 MODULA • System Telemetry & Fastfetch Hardware Hub")
        self.geometry("740x680")
        self.minsize(680, 580)

        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.specs: HardwareSpecs = SystemTelemetry.get_hardware_specs()

        self.transient(master)
        self.grab_set()

        self._build_ui()
        self._is_alive = True
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(1000, self._tick_metrics)

    def _on_close(self):
        self._is_alive = False
        self.destroy()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text="💻 MODULA Hardware Telemetry & Fastfetch Hub",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Informasi Sistem ala Fastfetch • Live Resource Monitor • Active Process Telemetry",
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

        # 2c. Real-Time Rolling Resource Graph
        graph_card = ctk.CTkFrame(
            scroll_box,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#242938"),
            fg_color=("#F8FAFC", "#1E222D"),
        )
        graph_card.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(
            graph_card,
            text="📈 LIVE CPU & RAM UTILIZATION GRAPH (Rolling 60s)",
            font=("Segoe UI", 11, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        is_dark = (ctk.get_appearance_mode() == "Dark")
        self.canvas_bg = "#12141A" if is_dark else "#FFFFFF"
        self.res_canvas = tk.Canvas(
            graph_card,
            height=90,
            bg=self.canvas_bg,
            highlightthickness=0,
        )
        self.res_canvas.pack(fill="x", padx=14, pady=(2, 10))

        # 2d. Active Top Processes by Resource
        proc_card = ctk.CTkFrame(
            scroll_box,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#242938"),
            fg_color=("#F8FAFC", "#1E222D"),
        )
        proc_card.pack(fill="x", padx=4, pady=6)

        ctk.CTkLabel(
            proc_card,
            text="⚡ ACTIVE HIGH-LOAD PROCESS TELEMETRY (Top Apps)",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0284C7", "#38BDF8"),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.proc_container = ctk.CTkFrame(proc_card, fg_color="transparent")
        self.proc_container.pack(fill="x", padx=14, pady=(2, 10))
        self._refresh_process_list()

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

    def _refresh_process_list(self):
        for w in self.proc_container.winfo_children():
            w.destroy()

        procs = SystemTelemetry.get_top_processes(limit=5)
        if not procs:
            ctk.CTkLabel(
                self.proc_container,
                text="Memindai proses aktif...",
                font=("Segoe UI", 10),
                text_color=("#64748B", "#94A3B8"),
            ).pack(anchor="w")
            return

        for p in procs:
            row = ctk.CTkFrame(self.proc_container, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                row,
                text=f"• {p['name']}",
                font=("Segoe UI", 10, "bold"),
                text_color=("#0F172A", "#F8FAFC"),
                width=180,
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=f"CPU: {p['cpu']}%",
                font=("Segoe UI", 10),
                text_color=("#D97706", "#F59E0B"),
                width=90,
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=f"RAM: {p['ram']}%",
                font=("Segoe UI", 10),
                text_color=("#DC2626", "#F43F5E"),
                width=90,
                anchor="w",
            ).pack(side="left")

    def _tick_metrics(self):
        if not getattr(self, "_is_alive", True):
            return

        try:
            cpu, ram, ram_txt = SystemTelemetry.get_live_cpu_ram()
            self.cpu_lbl.configure(text=f"CPU USAGE: {cpu:.1f}%")
            self.cpu_bar.set(cpu / 100.0)
            self.ram_lbl.configure(text=f"RAM USAGE: {ram:.1f}% ({ram_txt})")
            self.ram_bar.set(ram / 100.0)

            # Record sample
            SystemTelemetry.record_history_sample(cpu, ram)

            # Redraw rolling history graph
            self._draw_rolling_graph()
            self._refresh_process_list()
        except Exception:
            pass

        self.after(1000, self._tick_metrics)

    def _draw_rolling_graph(self):
        self.res_canvas.delete("all")
        w = self.res_canvas.winfo_width() or 660
        h = self.res_canvas.winfo_height() or 90

        cpu_hist, ram_hist = SystemTelemetry.get_history()
        if len(cpu_hist) < 2:
            return

        # Draw grid lines
        for y_pct in [0.25, 0.5, 0.75]:
            gy = h * y_pct
            self.res_canvas.create_line(0, gy, w, gy, fill="#2D3345", width=1, dash=(2, 4))

        # Plot CPU (Amber)
        step = w / max(1, len(cpu_hist) - 1)
        cpu_points = []
        for idx, val in enumerate(cpu_hist):
            x = idx * step
            y = h - (val / 100.0 * (h - 8)) - 4
            cpu_points.extend([x, y])

        if len(cpu_points) >= 4:
            self.res_canvas.create_line(cpu_points, fill="#F59E0B", width=2, smooth=True)

        # Plot RAM (Red / Rose)
        ram_points = []
        for idx, val in enumerate(ram_hist):
            x = idx * step
            y = h - (val / 100.0 * (h - 8)) - 4
            ram_points.extend([x, y])

        if len(ram_points) >= 4:
            self.res_canvas.create_line(ram_points, fill="#F43F5E", width=2, smooth=True)

        # Legend
        self.res_canvas.create_text(50, 12, text="― CPU", fill="#F59E0B", font=("Segoe UI", 9, "bold"))
        self.res_canvas.create_text(110, 12, text="― RAM", fill="#F43F5E", font=("Segoe UI", 9, "bold"))
