import math
import threading
import time
import tkinter as tk
from typing import Dict, List, Optional, Tuple
import customtkinter as ctk

from core.models import AdapterInfo, SpeedtestProvider, SpeedtestResult
from core.speedtest_engine import SpeedtestManager
from .speedtest_detail_modal import SpeedtestDetailModal


ALL_4_PROVIDERS = "⚡ 1-Click All 4 Providers (Ookla, Fast.com, nPerf, Cloudflare)"


class OoklaGauge(tk.Canvas):
    """
    Ookla-style animated circular speedometer gauge with sweep needle,
    tick marks, and live digital readout.
    """

    def __init__(self, master, width: int = 340, height: int = 180, **kwargs):
        super().__init__(
            master,
            width=width,
            height=height,
            highlightthickness=0,
            **kwargs,
        )
        self.w = width
        self.h = height
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.stage_text = "Ready"
        self.max_scale = 100.0  # Dynamic scale: 50, 100, 250, 500, 1000
        self._animating = True

        self.draw_gauge(0.0)
        self._anim_tick()

    def _anim_tick(self):
        """60 FPS continuous exponential lerp for buttery smooth speedometer animation."""
        if not getattr(self, "_animating", True):
            return

        diff = self.target_speed - self.current_speed
        if abs(diff) > 0.05:
            self.current_speed += diff * 0.16
            self.draw_gauge(self.current_speed)
        elif self.current_speed != self.target_speed:
            self.current_speed = self.target_speed
            self.draw_gauge(self.current_speed)

        try:
            self.after(16, self._anim_tick)
        except Exception:
            pass

    def destroy(self):
        self._animating = False
        super().destroy()

    def set_speed(self, speed_mbps: float, stage: str = ""):
        self.target_speed = max(0.0, speed_mbps)
        if stage:
            self.stage_text = stage
        if self.target_speed > self.max_scale * 0.88:
            if self.max_scale <= 100.0:
                self.max_scale = 250.0
            elif self.max_scale <= 250.0:
                self.max_scale = 500.0
            elif self.max_scale <= 500.0:
                self.max_scale = 1000.0

    def reset(self):
        self.current_speed = 0.0
        self.target_speed = 0.0
        self.stage_text = "Ready"
        self.max_scale = 100.0
        self.draw_gauge(0.0)

    def draw_gauge(self, speed: float):
        self.delete("all")
        is_dark = (ctk.get_appearance_mode() == "Dark")
        bg_col = "#181A24" if is_dark else "#FFFFFF"
        self.configure(bg=bg_col)

        cx = self.w / 2
        cy = self.h - 22
        radius = min(self.w / 2 - 28, self.h - 36)

        # Arc from 140 to 40 degrees (angles in standard math: 180 + 35 down to -35)
        # In Tkinter arc: start is degrees counter-clockwise from 3 o'clock, extent is counter-clockwise
        # We will draw ticks manually
        start_deg = 215
        end_deg = -35
        total_deg = start_deg - end_deg  # 250 degrees span

        # Draw background track arc
        track_col = "#242938" if is_dark else "#E2E8F0"
        self.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=end_deg, extent=total_deg,
            style="arc", outline=track_col, width=8
        )

        # Draw active gradient progress arc
        speed_ratio = min(1.0, speed / max(10.0, self.max_scale))
        if speed_ratio > 0.01:
            active_extent = total_deg * speed_ratio
            active_col = "#F59E0B" if speed_ratio < 0.6 else "#DC2626"
            self.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=start_deg, extent=-active_extent,
                style="arc", outline=active_col, width=8
            )

        # Tick marks & Labels
        tick_col = "#475569" if is_dark else "#94A3B8"
        text_col = "#64748B" if is_dark else "#64748B"
        ticks = [0, 0.25, 0.5, 0.75, 1.0]
        for t in ticks:
            deg = start_deg - (t * total_deg)
            rad = math.radians(deg)
            x1 = cx + (radius - 12) * math.cos(rad)
            y1 = cy - (radius - 12) * math.sin(rad)
            x2 = cx + radius * math.cos(rad)
            y2 = cy - radius * math.sin(rad)
            self.create_line(x1, y1, x2, y2, fill=tick_col, width=2)

            val_label = int(t * self.max_scale)
            lx = cx + (radius - 22) * math.cos(rad)
            ly = cy - (radius - 22) * math.sin(rad)
            self.create_text(lx, ly, text=str(val_label), fill=text_col, font=("Segoe UI", 7))

        # Needle
        needle_deg = start_deg - (speed_ratio * total_deg)
        needle_rad = math.radians(needle_deg)
        needle_len = radius - 8
        nx = cx + needle_len * math.cos(needle_rad)
        ny = cy - needle_len * math.sin(needle_rad)
        needle_col = "#F59E0B" if is_dark else "#D97706"
        self.create_line(cx, cy, nx, ny, fill=needle_col, width=3, capstyle="round")

        # Center Hub
        hub_col = "#E11D48" if is_dark else "#DC2626"
        self.create_oval(cx - 7, cy - 7, cx + 7, cy + 7, fill=hub_col, outline="")

        # Digital Readout
        speed_txt = f"{speed:.1f}" if speed < 100 else f"{speed:.0f}"
        readout_col = "#F8FAFC" if is_dark else "#0F172A"
        self.create_text(cx, cy - 38, text=speed_txt, fill=readout_col, font=("Segoe UI", 22, "bold"))
        self.create_text(cx, cy - 20, text="Mbps", fill="#06B6D4", font=("Segoe UI", 9, "bold"))

        # Stage status underneath
        self.create_text(cx, cy + 12, text=self.stage_text, fill=needle_col, font=("Segoe UI", 9, "bold"))


class SpeedtestModal(ctk.CTkToplevel):
    """
    MODULA Speedtest Suite dialog supporting:
    - 1-Click All 4 Providers (Ookla, Fast.com Netflix, nPerf, Cloudflare)
    - Individual Provider test
    - Ookla-style animated circular speedometer gauge
    - Cloudflare-style telemetry breakdown (Loaded Latency, Jitter, Loss, ISP)
    """

    def __init__(self, master, adapters: List[AdapterInfo]):
        super().__init__(master)
        self.title("⚡ MODULA Speedtest Suite • Ookla, Fast.com, nPerf & Cloudflare")
        self.geometry("820x720")
        self.minsize(740, 600)

        self.adapters = [a for a in adapters if a.is_connected and a.ipv4 and not a.ipv4.startswith("169.254.")]
        self.is_testing = False

        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(14, 6), sticky="ew")

        ctk.CTkLabel(
            header,
            text="⚡ MODULA Multi-Provider Speedtest Suite",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Multi-Engine Benchmark • Bound to Adapter Source-IP • Ookla, Fast.com (Netflix), nPerf & Cloudflare",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # 2. Control Panel
        ctrl_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        ctrl_frame.grid(row=1, column=0, padx=20, pady=6, sticky="ew")
        ctrl_frame.grid_columnconfigure(1, weight=1)

        # Provider selection
        ctk.CTkLabel(ctrl_frame, text="Engine / Mode:", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, padx=14, pady=10, sticky="w"
        )

        provider_choices = [
            ALL_4_PROVIDERS,
            SpeedtestProvider.CLOUDFLARE.value,
            SpeedtestProvider.FAST.value,
            SpeedtestProvider.NPERF.value,
            SpeedtestProvider.OOKLA.value,
        ]
        self.provider_menu = ctk.CTkOptionMenu(
            ctrl_frame,
            values=provider_choices,
            font=("Segoe UI", 11),
            fg_color=("#E2E8F0", "#242938"),
            button_color=("#D97706", "#F59E0B"),
            button_hover_color=("#B45309", "#D97706"),
            text_color=("#0F172A", "#F8FAFC"),
            width=280,
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
            fg_color=("#E2E8F0", "#242938"),
            button_color=("#D97706", "#F59E0B"),
            button_hover_color=("#B45309", "#D97706"),
            text_color=("#0F172A", "#F8FAFC"),
            width=280,
            height=28,
        )
        self.adapter_menu.grid(row=1, column=1, padx=14, pady=(0, 10), sticky="w")

        # Start button
        self.start_btn = ctk.CTkButton(
            ctrl_frame,
            text="▶ Start Test",
            command=self._start_speedtest,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#DC2626", "#E11D48"),
            hover_color=("#B91C1C", "#BE123C"),
            width=140,
            height=34,
            corner_radius=8,
        )
        self.start_btn.grid(row=0, column=2, rowspan=2, padx=14, pady=10, sticky="e")

        # 3. Middle Section: Ookla Gauge + Cloudflare Telemetry Cards
        middle_box = ctk.CTkFrame(self, fg_color="transparent")
        middle_box.grid(row=2, column=0, padx=20, pady=4, sticky="ew")
        middle_box.grid_columnconfigure(0, weight=1)
        middle_box.grid_columnconfigure(1, weight=1)

        # Left: Ookla Gauge
        gauge_container = ctk.CTkFrame(
            middle_box,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        gauge_container.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        ctk.CTkLabel(
            gauge_container,
            text="OOKLA-STYLE SPEEDOMETER",
            font=("Segoe UI", 10, "bold"),
            text_color=("#64748B", "#94A3B8"),
        ).pack(pady=(6, 0))

        self.gauge = OoklaGauge(gauge_container, width=320, height=170)
        self.gauge.pack(pady=4)

        # Right: Cloudflare-Style Telemetry Cards
        telemetry_container = ctk.CTkFrame(
            middle_box,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        telemetry_container.grid(row=0, column=1, padx=(6, 0), sticky="nsew")

        ctk.CTkLabel(
            telemetry_container,
            text="CLOUDFLARE TELEMETRY BREAKDOWN",
            font=("Segoe UI", 10, "bold"),
            text_color=("#64748B", "#94A3B8"),
        ).pack(pady=(6, 4))

        # 4 Telemetry Metric Cards Grid
        grid_cards = ctk.CTkFrame(telemetry_container, fg_color="transparent")
        grid_cards.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        grid_cards.grid_columnconfigure(0, weight=1)
        grid_cards.grid_columnconfigure(1, weight=1)

        # Card 1: Download
        self.card_dl = self._create_telemetry_tile(grid_cards, 0, 0, "⬇ DOWNLOAD", "0.0 Mbps", "#10B981")
        # Card 2: Upload
        self.card_up = self._create_telemetry_tile(grid_cards, 0, 1, "⬆ UPLOAD", "0.0 Mbps", "#3B82F6")
        # Card 3: Ping & Jitter
        self.card_lat = self._create_telemetry_tile(grid_cards, 1, 0, "⏱ IDLE LATENCY / JITTER", "0 ms / 0 ms", "#F59E0B")
        # Card 4: Loaded Latency & Server
        self.card_loaded = self._create_telemetry_tile(grid_cards, 1, 1, "📶 BUFFERBLOAT / LOC", "0 ms • Standby", "#06B6D4")

        # Progress bar under middle
        self.prog_bar = ctk.CTkProgressBar(
            self,
            height=4,
            corner_radius=2,
            progress_color=("#D97706", "#F59E0B"),
        )
        self.prog_bar.set(0.0)
        self.prog_bar.grid(row=3, column=0, padx=20, pady=(0, 4), sticky="ew")

        # 4. Results Container (Scrollable Table)
        self.results_box = ctk.CTkScrollableFrame(
            self,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#FFFFFF", "#181A24"),
        )
        self.results_box.grid(row=4, column=0, padx=20, pady=(2, 10), sticky="nsew")
        self.grid_rowconfigure(4, weight=1)
        self.results_box.grid_columnconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(
            self.results_box,
            text="Hasil benchmark multi-provider akan ditampilkan di sini.",
            font=("Segoe UI", 11),
            text_color=("#94A3B8", "#64748B"),
        )
        self.empty_label.pack(pady=30)

        # Close button
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="e")
        ctk.CTkButton(
            bottom,
            text="Tutup",
            command=self.destroy,
            width=90,
            height=28,
            fg_color=("#E2E8F0", "#242938"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(side="right")

    def _create_telemetry_tile(self, master, r, c, title, init_val, accent_col):
        is_dark = (ctk.get_appearance_mode() == "Dark")
        tile = ctk.CTkFrame(
            master,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#2D3345"),
            fg_color=("#F8FAFC", "#1E222E"),
        )
        tile.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

        lbl_t = ctk.CTkLabel(tile, text=title, font=("Segoe UI", 8, "bold"), text_color=("#64748B", "#94A3B8"))
        lbl_t.pack(anchor="w", padx=8, pady=(4, 0))

        lbl_v = ctk.CTkLabel(tile, text=init_val, font=("Segoe UI", 11, "bold"), text_color=accent_col)
        lbl_v.pack(anchor="w", padx=8, pady=(0, 4))
        return lbl_v

    def _start_speedtest(self):
        if self.is_testing:
            return

        if not self.adapters:
            self.card_loaded.configure(text="No active network adapters")
            return

        sel_adapter_str = self.adapter_menu.get()
        is_bulk = "Bulk Test" in sel_adapter_str
        chosen_provider_str = self.provider_menu.get()

        self.is_testing = True
        self.start_btn.configure(state="disabled", text="⏳ Testing...")
        self.prog_bar.set(0.05)
        self.gauge.reset()

        if self.empty_label.winfo_exists():
            self.empty_label.pack_forget()

        # Run benchmark on background worker thread
        threading.Thread(
            target=self._worker_speedtest,
            args=(sel_adapter_str, is_bulk, chosen_provider_str),
            daemon=True,
        ).start()

    def _worker_speedtest(self, sel_adapter_str: str, is_bulk: bool, provider_str: str):
        try:
            # 1. Resolve target adapters
            if is_bulk:
                targets = [(a.alias, a.ipv4) for a in self.adapters]
            else:
                alias = sel_adapter_str.split(" (")[0].strip()
                matched = next((a for a in self.adapters if a.alias == alias), self.adapters[0])
                targets = [(matched.alias, matched.ipv4)]

            # 2. Check mode: 1-Click 4 Providers or Single Provider
            if provider_str == ALL_4_PROVIDERS:
                for alias, ip in targets:
                    def on_prov_start(p, idx, total):
                        self.after(0, lambda: self.gauge.set_speed(0.0, f"{p.name} ({idx}/{total})"))

                    def on_prog(p, phase, pct, cur_mbps):
                        self.after(0, lambda: self._update_progress_ui(p.value, phase, pct, cur_mbps))

                    def on_done(res):
                        self.after(0, lambda: self._add_result_row(res))

                    SpeedtestManager.run_all_providers(
                        alias,
                        ip,
                        on_provider_start=on_prov_start,
                        on_progress=on_prog,
                        on_provider_done=on_done,
                    )
            else:
                # Single provider mode
                provider = next((p for p in SpeedtestProvider if p.value == provider_str), SpeedtestProvider.CLOUDFLARE)

                for alias, ip in targets:
                    def on_prog(phase, pct, cur_mbps):
                        self.after(0, lambda: self._update_progress_ui(provider.value, phase, pct, cur_mbps))

                    res = SpeedtestManager.run_single(alias, ip, provider, on_progress=on_prog)
                    self.after(0, lambda: self._add_result_row(res))

        except Exception as e:
            print(f"Speedtest error: {e}")
        finally:
            self.after(0, self._on_finish)

    def _update_progress_ui(self, provider_name: str, phase: str, pct: float, cur_mbps: float):
        self.prog_bar.set(pct / 100.0)
        self.gauge.set_speed(cur_mbps, phase[:24])

        if "DL" in phase or "Download" in phase:
            self.card_dl.configure(text=f"{cur_mbps:.1f} Mbps")
        elif "Upload" in phase or "UP" in phase:
            self.card_up.configure(text=f"{cur_mbps:.1f} Mbps")

    def _add_result_row(self, res: SpeedtestResult):
        # Update telemetry tiles
        self.card_dl.configure(text=f"{res.download_mbps:.1f} Mbps")
        self.card_up.configure(text=f"{res.upload_mbps:.1f} Mbps")
        self.card_lat.configure(text=f"{res.ping_ms:.1f} ms (Jitter: {res.jitter_ms:.1f} ms)")
        loc_str = res.server_location[:24] if res.server_location else "Anycast"
        self.card_loaded.configure(text=f"{res.loaded_latency_ms:.1f} ms • {loc_str}")

        # Add row to results list
        row = ctk.CTkFrame(
            self.results_box,
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#2D3345"),
            fg_color=("#F8FAFC", "#1E222E"),
        )
        row.pack(fill="x", pady=3, padx=2)
        row.grid_columnconfigure(1, weight=1)

        # Provider Pill
        ctk.CTkLabel(
            row,
            text=f" {res.provider.value} ",
            font=("Segoe UI", 9, "bold"),
            fg_color=("#FEF3C7", "#78350F"),
            text_color=("#92400E", "#FDE68A"),
            corner_radius=4,
        ).pack(side="left", padx=8, pady=6)

        # Interface Alias & IP
        ctk.CTkLabel(
            row,
            text=f"{res.alias} ({res.ip})",
            font=("Segoe UI", 10, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        ).pack(side="left", padx=6)

        # Right side telemetry badges & Detail Button
        right_box = ctk.CTkFrame(row, fg_color="transparent")
        right_box.pack(side="right", padx=8)

        ctk.CTkLabel(right_box, text=f"⬇ {res.download_mbps:.1f}M", font=("Segoe UI", 10, "bold"), text_color="#10B981").pack(side="left", padx=5)
        ctk.CTkLabel(right_box, text=f"⬆ {res.upload_mbps:.1f}M", font=("Segoe UI", 10, "bold"), text_color="#3B82F6").pack(side="left", padx=5)
        ctk.CTkLabel(right_box, text=f"⏱ {res.ping_ms:.0f}ms", font=("Segoe UI", 10), text_color=("#64748B", "#94A3B8")).pack(side="left", padx=5)
        ctk.CTkLabel(right_box, text=f"Buf: {res.loaded_latency_ms:.0f}ms", font=("Segoe UI", 9), text_color="#06B6D4").pack(side="left", padx=5)

        detail_btn = ctk.CTkButton(
            right_box,
            text="🔍 Detail",
            command=lambda r=res: SpeedtestDetailModal(self, r),
            font=("Segoe UI", 10, "bold"),
            fg_color=("#D97706", "#F59E0B"),
            hover_color=("#B45309", "#D97706"),
            text_color=("#FFFFFF", "#0F172A"),
            width=68,
            height=24,
            corner_radius=4,
        )
        detail_btn.pack(side="left", padx=(6, 2))

        # Also make row click open the detail modal
        row.bind("<Button-1>", lambda e, r=res: SpeedtestDetailModal(self, r))

    def _on_finish(self):
        self.is_testing = False
        self.start_btn.configure(state="normal", text="▶ Start Test")
        self.prog_bar.set(1.0)
        self.gauge.set_speed(0.0, "Benchmark Complete")
