import math
import random
import time
import tkinter as tk
from typing import List, Optional, Tuple
import customtkinter as ctk

from core.models import TrafficStats


class TrafficChartWidget(ctk.CTkFrame):
    """
    MODULA Iconic Real-Time Network Spectrum & Throughput Analyzer.
    Ultra-smooth 40 FPS rendering with exponential lerping and anti-aliased splines.

    Supports 3 Iconic Visualizer Modes:
    1. ⚡ Cyber Spectrum Bars (32-band Barong Equalizer with gravity peak-hold caps)
    2. 📡 RF Internet Wave (Dual-band Oscilloscope packet frequency waves)
    3. 🌊 Smooth Curve (Anti-aliased spline curves with soft gradient area fills)
    """

    def __init__(self, master, width: int = 340, height: int = 70, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
            fg_color=("#F8FAFC", "#161822"),
            **kwargs,
        )
        self.chart_width = width
        self.chart_height = height
        self.max_points = 36

        # Historical raw samples
        self.dl_history: List[float] = [0.0] * self.max_points
        self.up_history: List[float] = [0.0] * self.max_points

        # Smoothly interpolated display values (exponential lerp)
        self.display_dl_points: List[float] = [0.0] * self.max_points
        self.display_up_points: List[float] = [0.0] * self.max_points

        self.target_dl_kbps = 0.0
        self.target_up_kbps = 0.0
        self.target_jitter = 0.0

        self.display_dl_kbps = 0.0
        self.display_up_kbps = 0.0
        self.display_jitter = 0.0

        self.view_mode = "⚡ Cyber Spectrum"

        # 32 Spectrum Equalizer Bars & Peaks
        self.num_bars = 32
        self.bar_heights = [4.0] * self.num_bars
        self.bar_peaks = [6.0] * self.num_bars
        self.anim_phase = 0.0

        self._cached_bg: Optional[str] = None
        self._cached_w = self.chart_width
        self._cached_h = self.chart_height

        self._build_ui()

        # Start buttery smooth 40 FPS animation loop (25ms ticks)
        self._animation_loop()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header metrics row
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, padx=12, pady=(6, 2), sticky="ew")
        top_row.grid_columnconfigure(0, weight=1)

        # Left: Title, Mode Switcher, and Source Info Button
        left_box = ctk.CTkFrame(top_row, fg_color="transparent")
        left_box.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            left_box,
            text="📡 Live Spectrum",
            font=("Segoe UI", 11, "bold"),
            text_color=("#D97706", "#F59E0B"),
        )
        title_label.pack(side="left", padx=(0, 6))

        self.mode_toggle = ctk.CTkSegmentedButton(
            left_box,
            values=["⚡ Cyber Spectrum", "📡 RF Wave", "🌊 Smooth Curve"],
            command=self._on_mode_change,
            font=("Segoe UI", 9, "bold"),
            height=20,
            width=270,
            selected_color=("#D97706", "#F59E0B"),
            selected_hover_color=("#B45309", "#D97706"),
        )
        self.mode_toggle.set(self.view_mode)
        self.mode_toggle.pack(side="left", padx=(0, 6))

        # Direct clickable Source & Target Info button
        info_btn = ctk.CTkButton(
            left_box,
            text="ℹ️ Info Target & Jitter",
            command=self._open_sources_modal,
            font=("Segoe UI", 9),
            fg_color=("#E2E8F0", "#20232B"),
            hover_color=("#CBD5E1", "#2D3139"),
            text_color=("#0F172A", "#38BDF8"),
            height=20,
            width=120,
            corner_radius=4,
        )
        info_btn.pack(side="left")

        # Right: Live Badges
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

        # Canvas for Spectrum & Waves
        self.canvas = tk.Canvas(
            self,
            width=self.chart_width,
            height=self.chart_height,
            bg="#10121A" if ctk.get_appearance_mode() == "Dark" else "#F1F5F9",
            highlightthickness=0,
        )
        self.canvas.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")

    def _open_sources_modal(self):
        from ui.modals.telemetry_sources_modal import TelemetrySourcesModal
        TelemetrySourcesModal(self.winfo_toplevel())

    def _on_mode_change(self, mode: str):
        self.view_mode = mode
        self._redraw_frame()

    def update_traffic(self, stats: TrafficStats, dl_history: List[float], up_history: List[float]):
        """Receive 1-second discrete sample and set lerping targets."""
        self.target_dl_kbps = stats.download_kbps
        self.target_up_kbps = stats.upload_kbps
        self.target_jitter = stats.jitter_ms

        if dl_history:
            self.dl_history = dl_history[-self.max_points :]
            while len(self.dl_history) < self.max_points:
                self.dl_history.insert(0, 0.0)
        if up_history:
            self.up_history = up_history[-self.max_points :]
            while len(self.up_history) < self.max_points:
                self.up_history.insert(0, 0.0)

    def _animation_loop(self):
        """Buttery smooth ~40 FPS rendering loop with continuous lerping."""
        # 1. Advance phase
        self.anim_phase += 0.06

        # 2. Smoothly lerp metrics to target (exponential moving average eliminates discrete jerks)
        lerp_rate = 0.12
        self.display_dl_kbps += (self.target_dl_kbps - self.display_dl_kbps) * lerp_rate
        self.display_up_kbps += (self.target_up_kbps - self.display_up_kbps) * lerp_rate
        self.display_jitter += (self.target_jitter - self.display_jitter) * lerp_rate

        # 3. Smoothly lerp historical point buffers
        for i in range(min(len(self.display_dl_points), len(self.dl_history))):
            self.display_dl_points[i] += (self.dl_history[i] - self.display_dl_points[i]) * 0.15
        for i in range(min(len(self.display_up_points), len(self.up_history))):
            self.display_up_points[i] += (self.up_history[i] - self.display_up_points[i]) * 0.15

        # 4. Update digital labels smoothly
        dl_val = self.display_dl_kbps
        up_val = self.display_up_kbps
        dl_text = f"⬇ {dl_val / 1000.0:.1f} Mbps" if dl_val >= 1000 else f"⬇ {dl_val:.0f} kbps"
        up_text = f"⬆ {up_val / 1000.0:.1f} Mbps" if up_val >= 1000 else f"⬆ {up_val:.0f} kbps"
        self.dl_label.configure(text=dl_text)
        self.up_label.configure(text=up_text)

        j = self.display_jitter
        j_col = ("#059669", "#34D399") if j < 5 else (("#D97706", "#FBBF24") if j < 15 else ("#DC2626", "#F87171"))
        self.jitter_label.configure(text=f"Jitter: {j:.1f} ms", text_color=j_col)

        # 5. Redraw canvas
        self._redraw_frame()

        # 6. Schedule next frame at 25ms (40 FPS)
        self.after(25, self._animation_loop)

    def _redraw_frame(self):
        is_dark = (ctk.get_appearance_mode() == "Dark")
        bg_col = "#10121A" if is_dark else "#F1F5F9"

        # Cache bg to avoid reconfiguring every frame (major source of Tkinter stutters)
        if self._cached_bg != bg_col:
            self.canvas.configure(bg=bg_col)
            self._cached_bg = bg_col

        self.canvas.delete("all")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 50:
            self._cached_w = w
        if h > 20:
            self._cached_h = h
        w, h = self._cached_w, self._cached_h

        if self.view_mode == "⚡ Cyber Spectrum":
            self._draw_cyber_spectrum(w, h, is_dark)
        elif self.view_mode == "📡 RF Wave":
            self._draw_rf_wave(w, h, is_dark)
        else:
            self._draw_smooth_curve(w, h, is_dark)

    def _draw_cyber_spectrum(self, w: int, h: int, is_dark: bool):
        """32-Band Barong Equalizer Spectrum with smooth fluid transitions and peak hold gravity."""
        num_bars = self.num_bars
        bar_gap = 3
        total_gaps = (num_bars - 1) * bar_gap
        bar_w = max(4, int((w - 24 - total_gaps) / num_bars))
        start_x = int((w - (num_bars * bar_w + total_gaps)) / 2)

        total_traffic = self.display_dl_kbps + self.display_up_kbps
        load_ratio = min(1.0, total_traffic / 35000.0) if total_traffic > 10 else 0.0

        for i in range(num_bars):
            # Frequency harmonics with smooth center bell distribution
            center_dist = abs(i - (num_bars / 2)) / (num_bars / 2)
            bell = math.cos(center_dist * math.pi * 0.46)

            # Continuous ambient heartbeat (flowing undulating cyber wave)
            ambient = (math.sin(self.anim_phase * 2.2 + i * 0.35) * 0.12) + 0.20
            traffic_amp = load_ratio * (0.85 + 0.3 * math.sin(self.anim_phase * 3.8 + i * 0.6))
            jitter_amp = (min(20.0, self.display_jitter) / 100.0) * (math.sin(i * 1.2) * 0.25)

            target_ratio = min(0.96, max(0.08, bell * (ambient + traffic_amp + jitter_amp)))
            target_h = target_ratio * (h - 10)

            # Smooth exponential height transition (0.22 lerp)
            self.bar_heights[i] += (target_h - self.bar_heights[i]) * 0.22
            cur_h = int(self.bar_heights[i])

            x1 = start_x + i * (bar_w + bar_gap)
            x2 = x1 + bar_w
            y2 = h - 4
            y1 = y2 - cur_h

            # Dynamic Barong Color: Cyan (#06B6D4) -> Royal Gold (#F59E0B) -> Crimson (#DC2626)
            rel_h = cur_h / max(10, h - 10)
            if rel_h < 0.38:
                bar_color = "#06B6D4" if is_dark else "#0891B2"
            elif rel_h < 0.72:
                bar_color = "#F59E0B" if is_dark else "#D97706"
            else:
                bar_color = "#DC2626" if is_dark else "#E11D48"

            self.canvas.create_rectangle(x1, y1, x2, y2, fill=bar_color, outline="")

            # Peak hold cap with gentle gravity decay
            if cur_h > self.bar_peaks[i]:
                self.bar_peaks[i] = float(cur_h)
            else:
                self.bar_peaks[i] = max(float(cur_h), self.bar_peaks[i] - 0.75)

            peak_y = int(y2 - self.bar_peaks[i] - 2)
            cap_color = "#FDE68A" if is_dark else "#B45309"
            self.canvas.create_line(x1, peak_y, x2, peak_y, fill=cap_color, width=2)

    def _draw_rf_wave(self, w: int, h: int, is_dark: bool):
        """Dual-band RF Internet Wave Oscilloscope with anti-aliased smooth spline waves."""
        mid_y = h / 2
        grid_col = "#1C202E" if is_dark else "#E2E8F0"

        # Oscilloscope baseline grid lines
        self.canvas.create_line(10, mid_y, w - 10, mid_y, fill=grid_col, dash=(2, 4))
        self.canvas.create_line(10, mid_y - (h / 4), w - 10, mid_y - (h / 4), fill=grid_col, dash=(1, 5))
        self.canvas.create_line(10, mid_y + (h / 4), w - 10, mid_y + (h / 4), fill=grid_col, dash=(1, 5))

        # Channel 1: Download Wave (Cyan)
        dl_scale = min(1.0, self.display_dl_kbps / 20000.0) if self.display_dl_kbps > 10 else 0.12
        pts_dl: List[float] = []
        steps = 50
        dx = (w - 24) / steps
        for s in range(steps + 1):
            x = 12 + s * dx
            norm_x = s / steps
            wave = math.sin(self.anim_phase * 2.8 + norm_x * 8.0) * (h * 0.35 * dl_scale + 4.0)
            y = mid_y - wave
            pts_dl.extend([x, y])

        # Draw single connected smooth spline (buttery smooth rendering)
        if len(pts_dl) >= 4:
            self.canvas.create_line(*pts_dl, fill="#06B6D4", width=2, smooth=True, splinesteps=16)

        # Channel 2: Upload / Jitter Wave (Gold/Crimson)
        up_scale = min(1.0, self.display_up_kbps / 12000.0) if self.display_up_kbps > 10 else 0.12
        pts_up: List[float] = []
        for s in range(steps + 1):
            x = 12 + s * dx
            norm_x = s / steps
            wave = math.cos(self.anim_phase * 2.4 + norm_x * 10.0) * (h * 0.28 * up_scale + 3.0)
            y = mid_y + wave
            pts_up.extend([x, y])

        up_col = "#F59E0B" if self.display_jitter < 10 else "#DC2626"
        if len(pts_up) >= 4:
            self.canvas.create_line(*pts_up, fill=up_col, width=2, smooth=True, splinesteps=16)

        # Real-time packet sweep marker
        marker_x = 12 + ((self.anim_phase * 40) % (w - 24))
        self.canvas.create_line(marker_x, 4, marker_x, h - 4, fill="#E11D48", width=1, dash=(2, 2))

    def _draw_smooth_curve(self, w: int, h: int, is_dark: bool):
        """Classic throughput spline curves with area fill (Bloomberg / Apple-style)."""
        max_val = max(
            max(self.display_dl_points or [10.0]),
            max(self.display_up_points or [10.0]),
            80.0
        )
        grid_col = "#1E212B" if is_dark else "#E2E8F0"
        self.canvas.create_line(0, h / 2, w, h / 2, fill=grid_col, dash=(2, 2))

        def draw_spline_area(data: List[float], line_color: str, area_color: str):
            if len(data) < 2:
                return
            n = len(data)
            step_x = (w - 24) / (n - 1)
            line_coords: List[float] = []
            poly_coords: List[float] = [12, h - 4]

            for i, val in enumerate(data):
                x = 12 + i * step_x
                ratio = min(1.0, max(0.0, val / max_val))
                y = (h - 6) - (ratio * (h - 12))
                line_coords.extend([x, y])
                poly_coords.extend([x, y])

            poly_coords.extend([12 + (n - 1) * step_x, h - 4])

            # Draw translucent area fill underneath
            if len(poly_coords) >= 6:
                self.canvas.create_polygon(*poly_coords, fill=area_color, outline="", smooth=True, splinesteps=24)

            # Draw top spline line
            if len(line_coords) >= 4:
                self.canvas.create_line(*line_coords, fill=line_color, width=2, smooth=True, splinesteps=24)

        # Download curve (Cyan with subtle fill)
        dl_fill = "#0C2333" if is_dark else "#E0F2FE"
        draw_spline_area(self.display_dl_points, "#06B6D4" if is_dark else "#0284C7", dl_fill)

        # Upload curve (Gold with subtle fill)
        up_fill = "#2A1E11" if is_dark else "#FEF3C7"
        draw_spline_area(self.display_up_points, "#F59E0B" if is_dark else "#D97706", up_fill)
