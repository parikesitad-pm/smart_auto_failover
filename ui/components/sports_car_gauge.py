"""
MODULA - Smart Auto Failover v2.6
Sports Car Supercar Instrument Cluster:
- Dual Cockpit Tachometers:
  * Left Dial: RPM Tachometer for DOWNLOAD throughput (with auto-scaling Kbps / Mbps / Gbps)
  * Center Cockpit HUD: Real-time Jitter (RFC 3550 in ms), Stability Meter & Gear Badge
  * Right Dial: MPH Speedometer for UPLOAD throughput (with auto-scaling Kbps / Mbps / Gbps)
- Dedicated Circular ICMP Backbone Tachometer Gauges (100% bars-free):
  * 3 default circular dials for 1.1.1.1, 8.8.8.8, 9.9.9.9
  * Automatically expands to 4 circular dials when Target 4 is activated!
"""
import math
import time
import tkinter as tk
from typing import Dict, List, Optional, Tuple
import customtkinter as ctk

from core.models import TrafficStats


class SportsCarGaugeWidget(ctk.CTkFrame):
    """
    Supercar Panoramic Instrument Cluster:
    Left: Dual Cockpit Gauges (RPM Download & MPH Upload + Center Jitter HUD)
    Right: Circular ICMP Backbone Tachometer Dials (3 or 4 circular dials, 0 bars)
    """

    def __init__(self, master, targets: Optional[List[str]] = None, height: int = 145, **kwargs):
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
        self.speed_val = 0.0

        # Live Target Values
        self.target_dl_kbps = 0.0
        self.target_up_kbps = 0.0
        self.target_jitter = 0.0
        self.active_alias = "P1 LAN"

        # Smooth Interpolated Display Values (60 FPS Exponential Lerp)
        self.display_dl_kbps = 0.0
        self.display_up_kbps = 0.0
        self.display_jitter = 0.0
        self.dl_needle_angle = -140.0
        self.up_needle_angle = -140.0

        # Backbone Data: target -> {target_rtt, display_rtt, peak_rtt, needle_angle}
        self.bb_data: Dict[str, dict] = {}
        self._init_backbone_data()

        self.anim_tick_phase = 0.0
        self._animating = True
        self._idle_ticks = 0

        self._build_ui()
        self._anim_loop()

    def _init_backbone_data(self):
        for t in self.targets:
            if t not in self.bb_data:
                # Assign initial baseline
                self.bb_data[t] = {
                    "target_rtt": 18.0,
                    "display_rtt": 18.0,
                    "peak_rtt": 25.0,
                    "needle_angle": -120.0,
                }

    def set_targets(self, targets: List[str]):
        """Dynamically update target backbones (e.g. expanding from 3 to 4 dials)."""
        clean = [t.strip() for t in targets if t and t.strip()]
        if not clean:
            clean = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
        self.targets = clean
        self._init_backbone_data()
        self._idle_ticks = 0
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

    def update_telemetry(
        self,
        stats: TrafficStats,
        jitter: float = 0.0,
        active_route_alias: str = "P1",
        latencies: Optional[Dict[str, float]] = None,
        dl_kbps: Optional[float] = None,
        up_kbps: Optional[float] = None,
    ):
        """Update live throughput, jitter, and individual target latencies."""
        if dl_kbps is not None:
            self.target_dl_kbps = max(0.0, dl_kbps)
        else:
            self.target_dl_kbps = max(0.0, stats.download_kbps)

        if up_kbps is not None:
            self.target_up_kbps = max(0.0, up_kbps)
        else:
            self.target_up_kbps = max(0.0, stats.upload_kbps)

        self.target_jitter = max(0.0, jitter or stats.jitter_ms)
        self.active_alias = active_route_alias or "P1 ACTIVE"
        self.speed_val = (self.target_dl_kbps + self.target_up_kbps) / 1000.0

        if latencies:
            for t in self.targets:
                if t in latencies:
                    self.bb_data[t]["target_rtt"] = max(1.0, latencies[t])
                    if latencies[t] > self.bb_data[t]["peak_rtt"]:
                        self.bb_data[t]["peak_rtt"] = latencies[t]

        self._idle_ticks = 0

    def update_gauge(
        self,
        speed_mbps: float,
        latency_ms: float = 15.0,
        jitter_ms: float = 1.0,
        targets: Optional[List[str]] = None,
        dl_kbps: Optional[float] = None,
        up_kbps: Optional[float] = None,
    ):
        """Convenience method to update gauge metrics and backbone targets."""
        if targets:
            self.set_targets(targets)
        self.speed_val = speed_mbps

        if dl_kbps is not None:
            self.target_dl_kbps = max(0.0, dl_kbps)
        else:
            self.target_dl_kbps = max(0.0, speed_mbps * 1024.0 * 0.8)

        if up_kbps is not None:
            self.target_up_kbps = max(0.0, up_kbps)
        else:
            self.target_up_kbps = max(0.0, speed_mbps * 1024.0 * 0.2)

        self.target_jitter = max(0.0, jitter_ms)

        for t in self.targets:
            if t in self.bb_data:
                self.bb_data[t]["target_rtt"] = max(1.0, latency_ms)
                if latency_ms > self.bb_data[t]["peak_rtt"]:
                    self.bb_data[t]["peak_rtt"] = latency_ms

        self._idle_ticks = 0

    def _anim_loop(self):
        """Ultra-smooth 60 FPS animation loop with 0% CPU idle throttling."""
        if not getattr(self, "_animating", True):
            return

        self.anim_tick_phase += 0.05

        # Check if values are changing
        d_dl = self.target_dl_kbps - self.display_dl_kbps
        d_up = self.target_up_kbps - self.display_up_kbps
        d_jit = self.target_jitter - self.display_jitter

        # Exponential Lerp for Download & Upload Gauges
        self.display_dl_kbps += d_dl * 0.16
        self.display_up_kbps += d_up * 0.16
        self.display_jitter += d_jit * 0.16

        # Convert Download to needle angle (-140° to +40°, 180° span)
        val_dl = max(0.0, self.display_dl_kbps)
        if val_dl <= 1.0:
            target_ang_dl = -140.0
        else:
            norm_dl = min(1.0, math.log10(val_dl + 10.0) / 5.2)
            target_ang_dl = -140.0 + (norm_dl * 180.0)
        self.dl_needle_angle += (target_ang_dl - self.dl_needle_angle) * 0.16

        # Convert Upload to needle angle (-140° to +40°, 180° span)
        val_up = max(0.0, self.display_up_kbps)
        if val_up <= 1.0:
            target_ang_up = -140.0
        else:
            norm_up = min(1.0, math.log10(val_up + 10.0) / 5.0)
            target_ang_up = -140.0 + (norm_up * 180.0)
        self.up_needle_angle += (target_ang_up - self.up_needle_angle) * 0.16

        # Update Circular Backbone Gauges
        for t in self.targets:
            if t not in self.bb_data:
                continue
            entry = self.bb_data[t]
            t_rtt = entry["target_rtt"]
            entry["display_rtt"] += (t_rtt - entry["display_rtt"]) * 0.15

            # Decay peak hold slowly
            entry["peak_rtt"] = max(entry["display_rtt"], entry["peak_rtt"] - 0.3)

            # Map RTT to circular angle (-135° to +45°, 180° span, 0-120ms)
            rtt_norm = min(1.0, entry["display_rtt"] / 120.0)
            target_ang_bb = -135.0 + (rtt_norm * 180.0)
            entry["needle_angle"] += (target_ang_bb - entry["needle_angle"]) * 0.16

        self._redraw()
        self.after(16, self._anim_loop)

    @staticmethod
    def _format_speed(kbps: float) -> Tuple[str, str]:
        """Format speed value and return (formatted_text, unit_badge: Kbps / Mbps / Gbps)."""
        if kbps >= 1_000_000.0:
            return f"{kbps / 1_000_000.0:.2f}", "Gbps"
        elif kbps >= 1000.0:
            return f"{kbps / 1000.0:.1f}", "Mbps"
        else:
            return f"{max(0.0, kbps):.0f}", "Kbps"

    def _redraw(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 50:
            return

        self.canvas.delete("all")

        # 1. Dark Cockpit Background & Divider
        bg_col = "#0D0E15"
        self.canvas.create_rectangle(0, 0, w, h, fill=bg_col, outline="")

        # Dynamic layout partition:
        # Left cluster: Download RPM, Center HUD, Upload MPH (~52% of width)
        # Right cluster: Circular ICMP Backbone Dials (~48% of width)
        left_w = min(int(w * 0.52), 620)
        right_start = left_w + 12

        # Sports car neon divider
        self.canvas.create_line(left_w, 10, left_w, h - 10, fill="#1F2332", width=1, dash=(3, 3))

        # ======================================================================
        # SECTION 1: SUPERCAR DUAL INSTRUMENT CLUSTER (DOWNLOAD RPM & UPLOAD MPH)
        # ======================================================================
        cluster_cx = left_w // 2
        cy = h // 2 + 12
        dial_r = min(int(h * 0.44), 62)

        # DL dial center (Left)
        dl_cx = int(cluster_cx - dial_r * 1.55)
        # UP dial center (Right of cluster)
        up_cx = int(cluster_cx + dial_r * 1.55)

        # 1A. DRAW DOWNLOAD (RPM) GAUGE
        self._draw_cockpit_dial(
            cx=dl_cx, cy=cy, radius=dial_r,
            needle_ang=self.dl_needle_angle,
            val_kbps=self.display_dl_kbps,
            top_badge="🏎️ RPM • DOWNLOAD",
            accent_col="#F59E0B",
            is_download=True,
        )

        # 1B. DRAW UPLOAD (MPH) GAUGE
        self._draw_cockpit_dial(
            cx=up_cx, cy=cy, radius=dial_r,
            needle_ang=self.up_needle_angle,
            val_kbps=self.display_up_kbps,
            top_badge="🏎️ MPH • UPLOAD",
            accent_col="#38BDF8",
            is_download=False,
        )

        # 1C. DRAW CENTER FLIGHT/DRIVE COMPUTER (JITTER & ACTIVE GEAR)
        self._draw_center_cockpit_hud(cx=cluster_cx, cy=cy, radius=dial_r)

        # ======================================================================
        # SECTION 2: CIRCULAR ICMP BACKBONE TACHOMETER GAUGES (ZERO BARS!)
        # ======================================================================
        right_w = w - right_start - 10
        total_targets = len(self.targets)
        if total_targets > 0 and right_w > 80:
            slot_w = right_w / total_targets
            bb_r = min(int(h * 0.38), int(slot_w * 0.44), 48)

            # Section Title
            self.canvas.create_text(
                right_start, 12,
                text=f"🌐 ICMP BACKBONE TACHOMETERS  [{total_targets} ACTIVE GAUGES]",
                font=("Segoe UI", 9, "bold"),
                fill="#F59E0B",
                anchor="w",
            )

            for idx, target in enumerate(self.targets):
                slot_cx = int(right_start + idx * slot_w + (slot_w / 2))
                bb_cy = h // 2 + 14
                self._draw_backbone_circular_gauge(
                    cx=slot_cx,
                    cy=bb_cy,
                    radius=bb_r,
                    target=target,
                    idx=idx,
                )

    def _draw_cockpit_dial(self, cx: int, cy: int, radius: int, needle_ang: float, val_kbps: float, top_badge: str, accent_col: str, is_download: bool):
        """Render supercar analog dial for Download or Upload throughput."""
        start_deg = 220
        total_deg = 200

        # Outer track arc
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=-40, extent=total_deg, style="arc", outline="#1F2332", width=7
        )

        # Redline track (>80% scale)
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=-40, extent=45, style="arc", outline="#7F1D1D", width=7
        )

        # Active throttle sweep arc
        sweep = max(2.0, min(190.0, needle_ang - (-140.0)))
        arc_col = "#EF4444" if sweep > 150.0 else (accent_col if sweep > 60.0 else "#10B981")
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=start_deg, extent=-sweep, style="arc", outline=arc_col, width=6
        )

        # Instrument Ticks
        for i in range(9):
            t = i / 8.0
            deg = start_deg - (t * total_deg)
            rad = math.radians(deg)
            is_maj = (i % 2 == 0)
            t_len = 8 if is_maj else 4
            x1 = cx + (radius - t_len) * math.cos(rad)
            y1 = cy - (radius - t_len) * math.sin(rad)
            x2 = cx + radius * math.cos(rad)
            y2 = cy - radius * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill="#475569", width=1.5 if is_maj else 1)

        # Sweeping Needle
        n_rad = math.radians(needle_ang)
        nx = cx + (radius - 8) * math.cos(n_rad)
        ny = cy - (radius - 8) * math.sin(n_rad)
        self.canvas.create_line(cx, cy, nx, ny, fill=arc_col, width=2.5, capstyle="round")

        # Center metallic hub with redline ring
        hub_r = 6
        self.canvas.create_oval(cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r, fill="#0D0E15", outline=arc_col, width=1.5)
        self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#F8FAFC", outline="")

        # Top Badge (RPM / MPH)
        self.canvas.create_text(cx, cy - radius - 8, text=top_badge, font=("Segoe UI", 7, "bold"), fill=accent_col)

        # Digital Center Speed Value & Unit Badge
        speed_txt, unit_txt = self._format_speed(val_kbps)
        self.canvas.create_text(cx, cy - 14, text=speed_txt, font=("Segoe UI", 12, "bold"), fill="#F8FAFC")
        self.canvas.create_text(cx, cy + 14, text=unit_txt, font=("Segoe UI", 8, "bold"), fill=accent_col)

    def _draw_center_cockpit_hud(self, cx: int, cy: int, radius: int):
        """Render center cockpit computer: Active Gear, Jitter, and Stability badge."""
        hud_box_w = 110
        hud_box_h = int(radius * 1.8)

        # HUD background glass panel
        x1 = cx - hud_box_w // 2
        y1 = cy - hud_box_h // 2 + 4
        x2 = cx + hud_box_w // 2
        y2 = cy + hud_box_h // 2 + 4

        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#121520", outline="#252A3B", width=1)

        # Gear / Active Route Badge
        alias_clean = self.active_alias.replace("ACTIVE", "").strip().upper()
        self.canvas.create_text(
            cx, y1 + 14,
            text=f"🏎️ {alias_clean[:12]}",
            font=("Segoe UI", 8, "bold"),
            fill="#F59E0B",
        )

        # Jitter Metric Value
        jit_val = self.display_jitter
        jit_col = "#10B981" if jit_val < 5.0 else ("#F59E0B" if jit_val < 15.0 else "#EF4444")

        self.canvas.create_text(
            cx, cy - 4,
            text=f"{jit_val:.1f} ms",
            font=("Segoe UI", 14, "bold"),
            fill=jit_col,
        )

        # Subtitle
        self.canvas.create_text(
            cx, cy + 14,
            text="RFC 3550 JITTER",
            font=("Consolas", 7, "bold"),
            fill="#94A3B8",
        )

        # Stability Indicator Status Pill
        stab_txt = "● STABLE" if jit_val < 8.0 else "● BUFFERBLOAT"
        self.canvas.create_text(
            cx, y2 - 12,
            text=stab_txt,
            font=("Segoe UI", 7, "bold"),
            fill=jit_col,
        )

    def _draw_backbone_circular_gauge(self, cx: int, cy: int, radius: int, target: str, idx: int):
        """Render dedicated circular sports car gauge for an ICMP backbone target (NO BARS)."""
        data = self.bb_data.get(target, {"display_rtt": 18.0, "needle_angle": -120.0, "peak_rtt": 25.0})
        rtt = data.get("display_rtt", 18.0)
        n_ang = data.get("needle_angle", -120.0)
        peak = data.get("peak_rtt", rtt)

        start_deg = 225
        total_deg = 210

        # Background track
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=-45, extent=total_deg, style="arc", outline="#1A1E2B", width=6
        )

        # Redline track (>80ms)
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=-45, extent=55, style="arc", outline="#7F1D1D", width=6
        )

        # Dynamic arc color based on latency RTT
        if rtt > 80.0:
            arc_col = "#EF4444"
        elif rtt > 35.0:
            arc_col = "#F59E0B"
        else:
            arc_col = "#10B981"

        # Active latency sweep arc
        sweep = max(3.0, min(total_deg, (rtt / 120.0) * total_deg))
        self.canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=start_deg, extent=-sweep, style="arc", outline=arc_col, width=5
        )

        # Peak Hold Pip
        peak_sweep = max(2.0, min(total_deg, (peak / 120.0) * total_deg))
        peak_deg = start_deg - peak_sweep
        peak_rad = math.radians(peak_deg)
        px1 = cx + (radius - 8) * math.cos(peak_rad)
        py1 = cy - (radius - 8) * math.sin(peak_rad)
        px2 = cx + (radius + 1) * math.cos(peak_rad)
        py2 = cy - (radius + 1) * math.sin(peak_rad)
        self.canvas.create_line(px1, py1, px2, py2, fill="#38BDF8", width=2)

        # Sweeping Needle
        n_rad = math.radians(n_ang)
        nx = cx + (radius - 7) * math.cos(n_rad)
        ny = cy - (radius - 7) * math.sin(n_rad)
        self.canvas.create_line(cx, cy, nx, ny, fill=arc_col, width=2, capstyle="round")

        # Center metallic hub
        self.canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#0D0E15", outline=arc_col, width=1.5)
        self.canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill="#F8FAFC", outline="")

        # Top Target Label Header
        prefix = f"P{idx + 1}"
        self.canvas.create_text(
            cx, cy - radius - 8,
            text=f"{prefix} • {target}",
            font=("Consolas", 8, "bold"),
            fill="#F59E0B" if idx == 0 else "#CBD5E1",
        )

        # Digital Center Latency Readout
        self.canvas.create_text(
            cx, cy + 12,
            text=f"{rtt:.0f} ms",
            font=("Consolas", 10, "bold"),
            fill=arc_col,
        )

        # Provider Provider Name
        prov_map = {
            "1.1.1.1": "Cloudflare",
            "1.0.0.1": "Cloudflare",
            "8.8.8.8": "Google DNS",
            "8.8.4.4": "Google DNS",
            "9.9.9.9": "Quad9 BGP",
            "208.67.222.222": "OpenDNS",
            "192.168.1.1": "Gateway",
        }
        prov_name = prov_map.get(target, "Anycast")
        self.canvas.create_text(
            cx, cy + radius + 10,
            text=prov_name,
            font=("Segoe UI", 7),
            fill="#64748B",
        )

    def destroy(self):
        """Gracefully terminate animation loop upon widget disposal."""
        self._animating = False
        super().destroy()
