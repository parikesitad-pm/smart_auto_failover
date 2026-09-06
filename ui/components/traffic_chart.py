import tkinter as tk
from typing import List, Tuple
import customtkinter as ctk

from core.models import TrafficStats


class TrafficChartWidget(ctk.CTkFrame):
    """
    Real-time Bandwidth (Download/Upload throughput) and Jitter visualizer widget.
    Supports Dual Mode (Dark & Light).
    """

    def __init__(self, master, width: int = 340, height: int = 60, **kwargs):
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
        self.max_points = 30

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header metrics row
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, padx=12, pady=(8, 2), sticky="ew")
        top_row.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            top_row,
            text="📊 Live Throughput & Jitter",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        title_label.grid(row=0, column=0, sticky="w")

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

        # Canvas for Throughput Curves
        self.canvas = tk.Canvas(
            self,
            width=self.chart_width,
            height=self.chart_height,
            bg="#12131A" if ctk.get_appearance_mode() == "Dark" else "#F1F5F9",
            highlightthickness=0,
        )
        self.canvas.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")

    def update_traffic(self, stats: TrafficStats, dl_history: List[float], up_history: List[float]):
        self.dl_history = dl_history[-self.max_points :] if dl_history else []
        self.up_history = up_history[-self.max_points :] if up_history else []

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
        bg_col = "#12131A" if is_dark else "#F1F5F9"
        self.canvas.configure(bg=bg_col)
        self.canvas.delete("all")

        w = self.canvas.winfo_width() or self.chart_width
        h = self.canvas.winfo_height() or self.chart_height

        if not self.dl_history and not self.up_history:
            self.canvas.create_text(
                w / 2, h / 2, text="Monitoring Network Traffic...", fill="#64748B", font=("Segoe UI", 9)
            )
            return

        # Max scale
        max_val = max(max(self.dl_history or [10.0]), max(self.up_history or [10.0]), 50.0)
        grid_col = "#1E212B" if is_dark else "#E2E8F0"
        self.canvas.create_line(0, h / 2, w, h / 2, fill=grid_col, dash=(2, 2))

        def draw_curve(data: List[float], color: str):
            if len(data) < 2:
                return
            step_x = w / (self.max_points - 1)
            start_x = w - (len(data) - 1) * step_x
            points = []
            for i, val in enumerate(data):
                x = start_x + (i * step_x)
                ratio = min(1.0, val / max_val)
                y = (h - 4) - (ratio * (h - 8))
                points.append((x, y))

            for i in range(len(points) - 1):
                self.canvas.create_line(
                    points[i][0], points[i][1], points[i + 1][0], points[i + 1][1],
                    fill=color, width=2, smooth=True
                )

        # Draw Download (Green) and Upload (Blue)
        draw_curve(self.dl_history, "#10B981")
        draw_curve(self.up_history, "#3B82F6")
