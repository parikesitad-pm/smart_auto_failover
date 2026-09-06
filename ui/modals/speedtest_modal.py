import threading
from typing import Dict, List, Optional, Tuple
import customtkinter as ctk

from core.models import AdapterInfo, SpeedtestProvider, SpeedtestResult
from core.speedtest_engine import SpeedtestManager


class SpeedtestModal(ctk.CTkToplevel):
    """
    Speedtest Suite dialog supporting Cloudflare, nPerf, and Ookla engines
    with Individual Interface selection and Bulk Comparison testing.
    Supports Dual Mode (Dark & Light).
    """

    def __init__(self, master, adapters: List[AdapterInfo]):
        super().__init__(master)
        self.title("⚡ Speedtest Suite • Cloudflare, nPerf & Ookla")
        self.geometry("720x620")
        self.minsize(600, 500)

        self.adapters = [a for a in adapters if a.is_connected and a.ipv4 and not a.ipv4.startswith("169.254.")]
        self.is_testing = False

        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#181A20"))
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text="⚡ Multi-Interface Speedtest Suite",
            font=("Segoe UI", 16, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Uji kecepatan independen yang di-bind ke Source IP adapter masing-masing",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # 2. Control Panel Frame
        ctrl_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#2D3139"),
            fg_color=("#FFFFFF", "#1E212B"),
        )
        ctrl_frame.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        ctrl_frame.grid_columnconfigure(1, weight=1)

        # Provider selection
        ctk.CTkLabel(ctrl_frame, text="Engine / Provider:", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, padx=14, pady=10, sticky="w"
        )
        self.provider_menu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=[
                SpeedtestProvider.CLOUDFLARE.value,
                SpeedtestProvider.NPERF.value,
                SpeedtestProvider.OOKLA.value,
            ],
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#2D3139"),
            button_color=("#3B82F6", "#2563EB"),
            text_color=("#0F172A", "#F8FAFC"),
            width=200,
            height=28,
        )
        self.provider_menu.grid(row=0, column=1, padx=14, pady=10, sticky="w")

        # Interface selection
        ctk.CTkLabel(ctrl_frame, text="Pilih Interface:", font=("Segoe UI", 11, "bold")).grid(
            row=1, column=0, padx=14, pady=(0, 10), sticky="w"
        )

        adapter_options = ["🔍 Bulk Test (Semua Adapter Aktif)"] + [
            f"{a.alias} ({a.ipv4})" for a in self.adapters
        ]
        self.adapter_menu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=adapter_options,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#2D3139"),
            button_color=("#3B82F6", "#2563EB"),
            text_color=("#0F172A", "#F8FAFC"),
            width=260,
            height=28,
        )
        self.adapter_menu.grid(row=1, column=1, padx=14, pady=(0, 10), sticky="w")

        # Start button
        self.start_btn = ctk.CTkButton(
            ctrl_frame,
            text="▶ Mulai Speedtest",
            command=self._start_speedtest,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#10B981", "#059669"),
            hover_color=("#059669", "#047857"),
            width=140,
            height=32,
            corner_radius=6,
        )
        self.start_btn.grid(row=0, column=2, rowspan=2, padx=14, pady=10, sticky="e")

        # Progress bar & Status
        self.prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.prog_frame.grid(row=2, column=0, padx=20, pady=4, sticky="ew")
        self.prog_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.prog_frame,
            text="Siap untuk pengujian. Pilih engine dan klik 'Mulai Speedtest'.",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        )
        self.status_label.grid(row=0, column=0, sticky="w", pady=(2, 4))

        self.prog_bar = ctk.CTkProgressBar(self.prog_frame, height=8)
        self.prog_bar.set(0.0)
        self.prog_bar.grid(row=1, column=0, sticky="ew")

        # 3. Results Container (Scrollable Frame)
        self.results_box = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#2D3139"),
            fg_color=("#FFFFFF", "#1E212B"),
        )
        self.results_box.grid(row=3, column=0, padx=20, pady=8, sticky="nsew")
        self.grid_rowconfigure(3, weight=1)
        self.results_box.grid_columnconfigure(0, weight=1)

        # Empty state prompt
        self.empty_label = ctk.CTkLabel(
            self.results_box,
            text="Hasil pengujian kecepatan akan tampil di sini.",
            font=("Segoe UI", 11),
            text_color=("#94A3B8", "#64748B"),
        )
        self.empty_label.pack(pady=40)

        # 4. Bottom close button
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=4, column=0, padx=20, pady=10, sticky="e")

        close_btn = ctk.CTkButton(
            bottom_frame,
            text="Tutup",
            command=self.destroy,
            width=90,
            height=30,
            fg_color=("#64748B", "#374151"),
            hover_color=("#475569", "#4B5563"),
        )
        close_btn.pack()

    def _start_speedtest(self):
        if self.is_testing:
            return

        selected_provider_str = self.provider_menu.get()
        provider = SpeedtestProvider.CLOUDFLARE
        for p in SpeedtestProvider:
            if p.value == selected_provider_str:
                provider = p
                break

        selected_adapter_str = self.adapter_menu.get()

        self.is_testing = True
        self.start_btn.configure(state="disabled", text="⏳ Menguji...")
        self.prog_bar.set(0.0)

        # Clear previous results
        for child in self.results_box.winfo_children():
            child.destroy()

        t = threading.Thread(
            target=self._run_test_worker,
            args=(provider, selected_adapter_str),
            daemon=True,
        )
        t.start()

    def _run_test_worker(self, provider: SpeedtestProvider, selected_opt: str):
        if "Bulk Test" in selected_opt or not self.adapters:
            # Bulk test across all active adapters
            target_list = [(a.alias, a.ipv4) for a in self.adapters]
            total = len(target_list)

            for idx, (alias, ip) in enumerate(target_list):
                self._update_progress(f"[{idx+1}/{total}] Menguji '{alias}'...", 0.1)

                def prog(phase, pct, cur_mbps):
                    overall_pct = (idx + (pct / 100.0)) / total
                    self._update_progress(f"[{alias}] {phase}", overall_pct)

                res = SpeedtestManager.run_single(alias, ip, provider, on_progress=prog)
                self.after(0, self._render_result_card, res)
        else:
            # Individual adapter test
            matched = None
            for a in self.adapters:
                if a.alias in selected_opt:
                    matched = a
                    break

            if matched:
                def prog(phase, pct, cur_mbps):
                    self._update_progress(f"[{matched.alias}] {phase}", pct / 100.0)

                res = SpeedtestManager.run_single(matched.alias, matched.ipv4, provider, on_progress=prog)
                self.after(0, self._render_result_card, res)

        self.after(0, self._test_finished)

    def _update_progress(self, status: str, pct: float):
        self.after(0, lambda: self._apply_progress(status, pct))

    def _apply_progress(self, status: str, pct: float):
        self.status_label.configure(text=status)
        self.prog_bar.set(min(1.0, max(0.0, pct)))

    def _render_result_card(self, res: SpeedtestResult):
        card = ctk.CTkFrame(
            self.results_box,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#2D3139"),
            fg_color=("#F8FAFC", "#171922"),
        )
        card.pack(fill="x", pady=4, padx=2)
        card.grid_columnconfigure(1, weight=1)

        # Header: Alias + Server
        hdr_row = ctk.CTkFrame(card, fg_color="transparent")
        hdr_row.pack(fill="x", padx=12, pady=(8, 4))
        hdr_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr_row,
            text=f"🌐 {res.alias} ({res.ip})",
            font=("Segoe UI", 12, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            hdr_row,
            text=f"{res.provider.value} • {res.server_location}",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        ).grid(row=0, column=1, sticky="e")

        # Stats grid
        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 8))
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)

        # Download
        ctk.CTkLabel(grid, text="Download", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8")).grid(row=0, column=0)
        ctk.CTkLabel(
            grid,
            text=f"{res.download_mbps:.1f} Mbps",
            font=("Segoe UI", 14, "bold"),
            text_color=("#059669", "#34D399"),
        ).grid(row=1, column=0)

        # Upload
        ctk.CTkLabel(grid, text="Upload", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8")).grid(row=0, column=1)
        ctk.CTkLabel(
            grid,
            text=f"{res.upload_mbps:.1f} Mbps",
            font=("Segoe UI", 14, "bold"),
            text_color=("#2563EB", "#60A5FA"),
        ).grid(row=1, column=1)

        # Ping
        ctk.CTkLabel(grid, text="Ping (Latency)", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8")).grid(row=0, column=2)
        ctk.CTkLabel(
            grid,
            text=f"{res.ping_ms:.0f} ms",
            font=("Segoe UI", 14, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).grid(row=1, column=2)

        # Jitter
        ctk.CTkLabel(grid, text="Jitter", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8")).grid(row=0, column=3)
        ctk.CTkLabel(
            grid,
            text=f"{res.jitter_ms:.1f} ms",
            font=("Segoe UI", 14, "bold"),
            text_color=("#D97706", "#FBBF24") if res.jitter_ms > 10 else ("#059669", "#34D399"),
        ).grid(row=1, column=3)

    def _test_finished(self):
        self.is_testing = False
        self.start_btn.configure(state="normal", text="▶ Mulai Speedtest")
        self.status_label.configure(text="Pengujian selesai!")
        self.prog_bar.set(1.0)
