"""
MODULA - Smart Auto Failover v2.4
Sports Car Supercar Instrument Cluster & Dual-Channel Backbone Spectrum Gauge.
Features:
- Sports car tachometer gauge with 60 FPS needle sweep & redline gradient
- Dual-channel ICMP Backbone Spectrum: 2 bars per backbone (3 targets = 6 bars, 4 targets = 8 bars)
- Digital gear/throttle HUD readout with real-time throughput & RFC 3550 Jitter
"""
import math
import random
import time
import tkinter as tk
from typing import Dict, List, Optional
import customtkinter as ctk

from core.models import TrafficStats


class SportsCarGaugeWidget(ctk.CTkFrame):
    """
    Supercar Instrument Cluster with Live Tachometer & Dual-Channel Backbone Spectrum Bars.
    """

    def __init__(self, master, targets: Optional[List[str]] = None, height: int = 140, **kwargs):
        super().__init__(
            master,
            corner_radius=12,
            border_width=1,
            border_color=("#CBD5E1", "#2A2E3D"),
            fg_color=("#FFFFFF", "#0D0E15"),
            height=height,
            **kwargs,
        )
        self.targets = targets or ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        self.canvas_height = height

        # Live values
        self.target_dl_kbps = 0.0
        self.target_up_kbps = 0.0
        self.target_jitter = 0.0
        self.active_alias = "P1"

        # Smooth interpolated display values (60 FPS lerp)
        self.display_dl_kbps = 0.0
        self.display_up_kbps = 0.0
        self.display_jitter = 0.0
        self.needle_angle = -140.0  # -140 deg (0) to +50 deg (max RPM)

        # Backbone channels (2 bars per target: Bar 1 = Latency RTT, Bar 2 = Stability/Jitter)
        # Stored as: target -> (rtt_ms, jitter_ms, bar1_height_lerp, bar2_height_lerp, peak1, peak2)
        self.channel_data: Dict[str, List[float]] = {}
        self._init_channel_data()

        self.anim_tick_phase = 0.0
        self._build_ui()
        self._anim_loop()

    def _init_channel_data(self):
        for t in self.targets:
            if t not in self.channel_data:
                # [rtt_ms, jitter_ms, bar1_pct, bar2_pct, peak1, peak2]
                self.channel_data[t] = [18.0, 1.2, 20.0, 85.0, 25.0, 90.0]

    def set_targets(self, targets: List[str]):
        """Dynamically update target backbones (e.g. expanding from 3 to 4 targets)."""
        clean = [t.strip() for t in targets if t and t.strip()]
        if not clean:
            clean = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        self.targets = clean
        self._init_channel_data()
        self._redraw()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(
            self,
            height=self.canvas_height,
            background="#0D0E15",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=4)
        self.canvas.bind("<Configure>", lambda e: self._redraw())

    def update_telemetry(self, stats: TrafficStats, jitter: float = 0.0, active_route_alias: str = "P1", latencies: Optional[Dict[str, float]] = None):
        """Update live telemetry from main polling cycle."""
        self.target_dl_kbps = max(0.0, stats.download_kbps)
        self.target_up_kbps = max(0.0, stats.upload_kbps)
        self.target_jitter = max(0.0, jitter)
        self.active_alias = active_route_alias or "P1"

        if latencies:
            for t in self.targets:
                if t in latencies:
                    self.channel_data[t][0] = max(1.0, latencies[t])
                    self.channel_data[t][1] = max(0.2, jitter)

    def update_gauge(self, speed_mbps: float, latency_ms: float = 15.0, jitter_ms: float = 1.0, targets: Optional[List[str]] = None):
        """Convenience method to update gauge speed, latency, jitter, and target channels."""
        if targets:
            self.set_targets(targets)
        self.speed_val = speed_mbps
        self.target_dl_kbps = max(0.0, speed_mbps * 1024.0 * 0.8)
        self.target_up_kbps = max(0.0, speed_mbps * 1024.0 * 0.2)
        self.target_jitter = max(0.0, jitter_ms)
        for t in self.targets:
            if t in self.channel_data:
                self.channel_data[t][0] = max(1.0, latency_ms)
                self.channel_data[t][1] = max(0.1, jitter_ms)


    def _anim_loop(self):
        """Smooth 60 FPS animation loop (~16ms ticks)."""
        self.anim_tick_phase += 0.06

        # Exponential lerp for tachometer needle
        self.display_dl_kbps += (self.target_dl_kbps - self.display_dl_kbps) * 0.12
        self.display_up_kbps += (self.target_up_kbps - self.display_up_kbps) * 0.12
        self.display_jitter += (self.target_jitter - self.display_jitter) * 0.12

        # Convert dl_kbps to sports tachometer angle (-140 to +50 degrees)
        # Scale: 0 Kbps -> -140 deg, 100 Mbps (100,000 Kbps) -> +50 deg (log scale for realistic throttle feel)
        val = max(0.0, self.display_dl_kbps)
        if val <= 1.0:
            target_ang = -140.0
        else:
            # log-based progress so low speeds still give visible tachometer revs
            norm = min(1.0, math.log10(val + 10.0) / 5.2)
            target_ang = -140.0 + (norm * 190.0)

        self.needle_angle += (target_ang - self.needle_angle) * 0.14

        # Update backbone channels lerp & peak hold
        for t in self.targets:
            if t not in self.channel_data:
                continue
            rtt, jit, b1, b2, p1, p2 = self.channel_data[t]
            # Bar 1: RTT latency (0-150ms -> 0-100%)
            t_b1 = min(100.0, max(8.0, (rtt / 120.0) * 100.0 + math.sin(self.anim_tick_phase + hash(t)) * 4.0))
            # Bar 2: Stability ratio (higher jitter = lower stability, 0-100%)
            t_b2 = min(100.0, max(15.0, 100.0 - (jit * 10.0) + math.cos(self.anim_tick_phase * 1.2) * 5.0))

            b1 += (t_b1 - b1) * 0.15
            b2 += (t_b2 - b2) * 0.15

            # Gravity peak hold
            p1 = max(b1, p1 - 0.7)
            p2 = max(b2, p2 - 0.7)

            self.channel_data[t][2] = b1
            self.channel_data[t][3] = b2
            self.channel_data[t][4] = p1
            self.channel_data[t][5] = p2

        self._redraw()
        self.after(16, self._anim_loop)

    def _redraw(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 50:
            return

        self.canvas.delete("all")

        # 1. Background Grid & Carbon Lines
        bg_col = "#0D0E15"
        self.canvas.create_rectangle(0, 0, w, h, fill=bg_col, outline="")

        # Sports car divider line between Tachometer (left) and Backbone Spectrum (right)
        tach_w = min(int(w * 0.46), 340)
        self.canvas.create_line(tach_w, 10, tach_w, h - 10, fill="#212534", width=1, dash=(3, 3))

        # 2. DRAW SPORTS CAR TACHOMETER (LEFT SECTION)
        cx = tach_w // 2
        cy = h // 2 + 18
        radius = min(h - 28, 92)

        # Outer Tachometer Track Arc (-145 to +55 deg)
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=-55, extent=200, style="arc", outline="#1F2332", width=9
        )

        # Yellow/Redline Zone Arc (-10 to +55 deg)
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=-55, extent=65, style="arc", outline="#7F1D1D", width=9
        )

        # Active Throttle Glow Arc based on needle position
        sweep = max(1.0, min(190.0, self.needle_angle - (-140.0)))
        arc_col = "#EF4444" if sweep > 140.0 else ("#F59E0B" if sweep > 70.0 else "#10B981")
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=140 - sweep, extent=sweep, style="arc", outline=arc_col, width=7
        )

        # Tachometer Tick Marks & Labels (0, 10, 25, 50, 100M)
        tick_vals = [("0", -140), ("10M", -95), ("25M", -50), ("50M", -5), ("100M", +40)]
        for lbl, ang_deg in tick_vals:
            rad = math.radians(ang_deg)
            x1 = cx + (radius - 12) * math.cos(rad)
            y1 = cy - (radius - 12) * math.sin(rad)
            x2 = cx + (radius - 4) * math.cos(rad)
            y2 = cy - (radius - 4) * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill="#475569", width=1.5)

        # Tachometer Needle
        n_rad = math.radians(self.needle_angle)
        nx = cx + (radius - 14) * math.cos(n_rad)
        ny = cy - (radius - 14) * math.sin(n_rad)

        # Needle shadow & core
        self.canvas.create_line(cx, cy, nx, ny, fill=arc_col, width=2.5)
        self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill="#F8FAFC", outline=arc_col, width=2)

        # Digital Center Speed & HUD Readout
        dl_mbps = self.display_dl_kbps / 1000.0
        up_mbps = self.display_up_kbps / 1000.0

        if dl_mbps >= 1.0:
            speed_txt = f"{dl_mbps:.1f}"
            unit_txt = "Mbps"
        else:
            speed_txt = f"{self.display_dl_kbps:.0f}"
            unit_txt = "Kbps"

        # Supercar Gear Badge
        gear_txt = f"🏎️ {self.active_alias.upper()} ACTIVE"
        self.canvas.create_text(cx, cy - 42, text=gear_txt, font=("Segoe UI", 8, "bold"), fill="#F59E0B")

        self.canvas.create_text(cx, cy - 20, text=f"{speed_txt} {unit_txt}", font=("Segoe UI", 13, "bold"), fill="#F8FAFC")
        self.canvas.create_text(
            cx, cy + 22,
            text=f"↑ {up_mbps:.1f} Mbps  •  Jitter {self.display_jitter:.1f}ms",
            font=("Consolas", 8),
            fill="#94A3B8"
        )

        # 3. DRAW DUAL-CHANNEL BACKBONE SPECTRUM (RIGHT SECTION)
        spec_x_start = tach_w + 14
        spec_w = w - spec_x_start - 10
        total_targets = len(self.targets)
        num_bars = total_targets * 2

        # Header for Backbone Spectrum
        self.canvas.create_text(
            spec_x_start, 12,
            text=f"🌐 ICMP DUAL-CHANNEL BACKBONE SPECTRUM  [{num_bars} BARS ACTIVE]",
            font=("Segoe UI", 9, "bold"),
            fill="#F59E0B",
            anchor="w"
        )

        legend_txt = "■ Bar 1: RTT Latency  |  ■ Bar 2: Link Stability (RFC 3550)"
        self.canvas.create_text(
            w - 12, 12,
            text=legend_txt,
            font=("Segoe UI", 8),
            fill="#64748B",
            anchor="e"
        )

        # Calculate slot width per target
        if total_targets == 0:
            return

        slot_w = spec_w / float(total_targets)
        bar_w = min(14.0, (slot_w - 16) / 2.0)
        chart_bottom = h - 22
        max_bar_h = h - 54

        for idx, target in enumerate(self.targets):
            slot_cx = spec_x_start + (idx * slot_w) + (slot_w / 2.0)

            # Retrieve channel metrics
            chan = self.channel_data.get(target, [20.0, 1.0, 30.0, 80.0, 35.0, 85.0])
            rtt_val, jit_val, b1_pct, b2_pct, p1_pct, p2_pct = chan

            # Coordinates for Bar 1 (Latency) and Bar 2 (Stability)
            b1_x = slot_cx - bar_w - 2
            b2_x = slot_cx + 2

            h1 = max(4.0, (b1_pct / 100.0) * max_bar_h)
            h2 = max(4.0, (b2_pct / 100.0) * max_bar_h)

            peak1_y = chart_bottom - ((p1_pct / 100.0) * max_bar_h)
            peak2_y = chart_bottom - ((p2_pct / 100.0) * max_bar_h)

            # Draw background slot tracks
            self.canvas.create_rectangle(b1_x, chart_bottom - max_bar_h, b1_x + bar_w, chart_bottom, fill="#161822", outline="")
            self.canvas.create_rectangle(b2_x, chart_bottom - max_bar_h, b2_x + bar_w, chart_bottom, fill="#161822", outline="")

            # Color gradient: Bar 1 (Amber/Redline for high latency)
            col1 = "#EF4444" if rtt_val > 80.0 else ("#F59E0B" if rtt_val > 40.0 else "#10B981")
            # Color gradient: Bar 2 (Cyan/Indigo for high stability)
            col2 = "#06B6D4" if b2_pct > 60.0 else "#3B82F6"

            # Draw Bar 1 (Latency RTT)
            self.canvas.create_rectangle(b1_x, chart_bottom - h1, b1_x + bar_w, chart_bottom, fill=col1, outline="")
            # Peak hold dot 1
            self.canvas.create_line(b1_x, peak1_y, b1_x + bar_w, peak1_y, fill="#FFFFFF", width=2)

            # Draw Bar 2 (Stability Index)
            self.canvas.create_rectangle(b2_x, chart_bottom - h2, b2_x + bar_w, chart_bottom, fill=col2, outline="")
            # Peak hold dot 2
            self.canvas.create_line(b2_x, peak2_y, b2_x + bar_w, peak2_y, fill="#38BDF8", width=2)

            # Target Label Below (e.g. 1.1.1.1, 8.8.8.8)
            label_col = "#F8FAFC" if idx == 0 else "#94A3B8"
            self.canvas.create_text(
                slot_cx, chart_bottom + 11,
                text=f"{target} ({rtt_val:.0f}ms)",
                font=("Consolas", 8, "bold"),
                fill=label_col,
                anchor="center"
            )
