import math
import random
import tkinter as tk
from typing import List, Tuple
import customtkinter as ctk

from core.models import TrafficStats


class TrafficChartWidget(ctk.CTkFrame):
    """
    Real-time Bandwidth (Download/Upload throughput) and Jitter visualizer widget.
    Supports Dual Mode (Dark & Light) and Dual Visualization:
    - Smooth Curve Area
    - Aesthetic Equalizer Spectrum Bars (Barong Gold / Crimson / Cyan gradient)
    """

    def __init__(self, master, width: int = 340, height: int = 68, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#2D3139"),
            fg_color=("#F8FAFC", "#171922"),
            **kwargs,
        )
        self.chart_width = width
        self.chart_height = height
        self.dl_history: List[float] = []
        self.up_history: List[float] = []
        self.max_points = 32
        self.view_mode = "Spectrum Bars"  # "Spectrum Bars" or "Smooth Curve"

        # Peak hold values for spectrum bars
        self.bar_peaks = [0.0] * 28
        self.current_jitter = 0.0

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header metrics row
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, padx=12, pady=(6, 2), sticky="ew")
        top_row.grid_columnconfigure(0, weight=1)

        # Title & Mode Switcher
        left_box = ctk.CTkFrame(top_row, fg_color="transparent")
        left_box.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            left_box,
            text="📊 Live Bandwidth & Jitter",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        title_label.pack(side="left", padx=(0, 10))

        self.mode_toggle = ctk.CTkSegmentedButton(
            left_box,
            values=["Spectrum Bars", "Smooth Curve"],
            command=self._on_mode_change,
            font=("Segoe UI", 9, "bold"),
            height=20,
            width=170,
            selected_color=("#D97706", "#F59E0B"),
            selected_hover_color=("#B45309", "#D97706"),
        )
        self.mode_toggle.set(self.view_mode)
        self.mode_toggle.pack(side="left")

        # Live Badges
        metrics_box = ctk.CTkFrame(top_row, fg_color="transparent")
        metrics_box.grid(row=0, column=1, sticky="e")

        self.dl_label = ctk.CTkLabel(
            metrics_box,
            text="⬇ 0 kbps",
            font=("Segoe UI", 10, "bold"),
            text_color=("#059669", "#34D399"),
        )
        self.dl_label.pack(side="left", padx=4)

        self.up_label = ctk.CTkLabel(
            metrics_box,
            text="⬆ 0 kbps",
            font=("Segoe UI", 10, "bold"),
            text_color=("#2563EB", "#60A5FA"),
        )
        self.up_label.pack(side="left", padx=4)

        self.jitter_label = ctk.CTkLabel(
            metrics_box,
            text="Jitter: 0.0 ms",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        )
        self.jitter_label.pack(side="left", padx=(4, 0))

        # Canvas for Throughput Curves / Equalizer
        self.canvas = tk.Canvas(
            self,
            width=self.chart_width,
            height=self.chart_height,
            bg="#12131A" if ctk.get_appearance_mode() == "Dark" else "#F1F5F9",
            highlightthickness=0,
        )
        self.canvas.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

    def _on_mode_change(self, mode: str):
        self.view_mode = mode
        self._redraw_chart()

    def update_traffic(self, stats: TrafficStats, dl_history: List[float], up_history: List[float]):
        self.dl_history = dl_history[-self.max_points :] if dl_history else []
        self.up_history = up_history[-self.max_points :] if up_history else []
        self.current_jitter = stats.jitter_ms

        # Update text badges
        dl_text = f"⬇ {stats.download_kbps / 1000.0:.1f} Mbps" if stats.download_kbps >= 1000 else f"⬇ {stats.download_kbps:.0f} kbps"
        up_text = f"⬆ {stats.upload_kbps / 1000.0:.1f} Mbps" if stats.upload_kbps >= 1000 else f"⬆ {stats.upload_kbps:.0f} kbps"
        self.dl_label.configure(text=dl_text)
        self.up_label.configure(text=up_text)

        # Jitter color
        j = stats.jitter_ms
        j_col = ("#059669", "#34D399") if j < 5 else (("#D97706", "#FBBF24") if j < 15 else ("#DC2626", "#F87171"))
        self.jitter_label.configure(text=f"Jitter: {j:.1f} ms", text_color=j_col)

        self._redraw_chart()

    def _redraw_chart(self):
        is_dark = (ctk.get_appearance_mode() == "Dark")
        bg_col = "#12141C" if is_dark else "#F1F5F9"
        self.canvas.configure(bg=bg_col)
        self.canvas.delete("all")

        w = self.canvas.winfo_width() or self.chart_width
        h = self.canvas.winfo_height() or self.chart_height

        if not self.dl_history and not self.up_history:
            self.canvas.create_text(
                w / 2, h / 2, text="Monitoring Network Traffic • Standby", fill="#64748B", font=("Segoe UI", 9)
            )
            return

        if self.view_mode == "Spectrum Bars":
            self._draw_spectrum_bars(w, h, is_dark)
        else:
            self._draw_smooth_curve(w, h, is_dark)

    def _draw_spectrum_bars(self, w: int, h: int, is_dark: bool):
        num_bars = 28
        bar_gap = 3
        total_gaps = (num_bars - 1) * bar_gap
        bar_w = max(4, int((w - 20 - total_gaps) / num_bars))
        start_x = int((w - (num_bars * bar_w + total_gaps)) / 2)

        # Reference max value
        max_val = max(max(self.dl_history or [10.0]), max(self.up_history or [10.0]), 80.0)
        latest_dl = self.dl_history[-1] if self.dl_history else 0.0
        latest_up = self.up_history[-1] if self.up_history else 0.0

        for i in range(num_bars):
            # Equalizer frequency simulation shaped by traffic & jitter
            center_dist = abs(i - (num_bars / 2)) / (num_bars / 2)
            bell = math.cos(center_dist * math.pi * 0.45)
            # Mix DL, UP, and subtle jitter harmonics
            noise = (math.sin(i * 1.3 + time.time() * 3.0) * 0.15) + 0.85
            ratio = ((latest_dl * 0.6 + latest_up * 0.4) / max_val) * bell * noise
            # Add jitter ripple
            ratio += (min(15.0, self.current_jitter) / 100.0) * (math.sin(i * 0.9) * 0.2)
            ratio = max(0.04, min(0.96, ratio))

            bar_h = int(ratio * (h - 10))
            x1 = start_x + i * (bar_w + bar_gap)
            x2 = x1 + bar_w
            y2 = h - 4
            y1 = y2 - bar_h

            # Dynamic Barong Color Palette based on height:
            # Low: Cyan (#06B6D4) -> Mid: Gold (#F59E0B) -> High: Crimson (#DC2626)
            if ratio < 0.35:
                bar_color = "#06B6D4" if is_dark else "#0891B2"
            elif ratio < 0.70:
                bar_color = "#F59E0B" if is_dark else "#D97706"
            else:
                bar_color = "#DC2626" if is_dark else "#E11D48"

            # Draw bar
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=bar_color, outline="")

            # Peak hold cap (floating dot)
            if bar_h > self.bar_peaks[i]:
                self.bar_peaks[i] = float(bar_h)
            else:
                self.bar_peaks[i] = max(0.0, self.bar_peaks[i] - 1.8)

            peak_y = int(y2 - self.bar_peaks[i] - 2)
            if peak_y < y1:
                cap_color = "#FDE68A" if is_dark else "#92400E"
                self.canvas.create_line(x1, peak_y, x2, peak_y, fill=cap_color, width=2)

    def _draw_smooth_curve(self, w: int, h: int, is_dark: bool):
        max_val = max(max(self.dl_history or [10.0]), max(self.up_history or [10.0]), 50.0)
        grid_col = "#1E212B" if is_dark else "#E2E8F0"
        self.canvas.create_line(0, h / 2, w, h / 2, fill=grid_col, dash=(2, 2))

        def draw_curve(data: List[float], color: str):
            if len(data) < 2:
                return
            step_x = (w - 24) / (self.max_points - 1)
            start_x = 12 + (w - 24) - (len(data) - 1) * step_x
            points = []
            for i, val in enumerate(data):
                x = start_x + (i * step_x)
                ratio = min(1.0, val / max_val)
                y = (h - 6) - (ratio * (h - 12))
                points.append((x, y))

            for i in range(len(points) - 1):
                self.canvas.create_line(
                    points[i][0], points[i][1], points[i + 1][0], points[i + 1][1],
                    fill=color, width=2, smooth=True
                )

        # Draw Download (Green/Gold) and Upload (Blue/Crimson)
        draw_curve(self.dl_history, "#10B981" if not is_dark else "#34D399")
        draw_curve(self.up_history, "#3B82F6" if not is_dark else "#60A5FA")
