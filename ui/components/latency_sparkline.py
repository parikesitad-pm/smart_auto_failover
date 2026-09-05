import tkinter as tk
from typing import List
import customtkinter as ctk


class LatencySparkline(ctk.CTkFrame):
    """
    Mini canvas-based sparkline chart and latency bar showing recent ping history.
    """

    def __init__(self, master, width: int = 240, height: int = 40, max_points: int = 30, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.width = width
        self.height = height
        self.max_points = max_points
        self.history: List[float] = []

        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg="#1A1C23",
            highlightthickness=1,
            highlightbackground="#2D3139",
        )
        self.canvas.pack(fill="both", expand=True)

    def update_history(self, history: List[float], last_latency: float, is_rto: bool):
        self.history = history[-self.max_points :] if history else []
        self._redraw(last_latency, is_rto)

    def _redraw(self, last_latency: float, is_rto: bool):
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or self.width
        h = self.canvas.winfo_height() or self.height

        if not self.history:
            self.canvas.create_text(
                w / 2, h / 2, text="No Ping Data", fill="#6C727F", font=("Segoe UI", 9)
            )
            return

        # Draw background horizontal guide lines (e.g. 50ms, 150ms)
        max_scale_ms = 250.0
        y_50 = h - int((50.0 / max_scale_ms) * (h - 8))
        self.canvas.create_line(0, y_50, w, y_50, fill="#232833", dash=(2, 2))

        # Calculate points
        n = len(self.history)
        if n < 2:
            return

        step_x = w / (self.max_points - 1)
        start_x = w - (n - 1) * step_x

        points = []
        for i, lat in enumerate(self.history):
            x = start_x + (i * step_x)
            if lat <= 0:  # RTO
                y = h - 2  # Bottom or top marker
            else:
                ratio = min(1.0, lat / max_scale_ms)
                y = (h - 4) - int(ratio * (h - 10))
            points.append((x, y))

        # Color based on latest status
        if is_rto:
            line_color = "#EF4444"  # Red
        elif last_latency < 50:
            line_color = "#10B981"  # Emerald Green
        elif last_latency < 120:
            line_color = "#3B82F6"  # Blue
        elif last_latency < 250:
            line_color = "#F59E0B"  # Amber
        else:
            line_color = "#EF4444"  # Red

        # Draw sparkline segments
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            lat_next = self.history[i + 1]
            seg_color = "#EF4444" if lat_next <= 0 else line_color
            self.canvas.create_line(x1, y1, x2, y2, fill=seg_color, width=2, smooth=True)

        # Draw latest point pulsing dot
        if points:
            last_x, last_y = points[-1]
            dot_color = "#EF4444" if is_rto else line_color
            r = 3
            self.canvas.create_oval(
                last_x - r, last_y - r, last_x + r, last_y + r, fill=dot_color, outline="#FFFFFF", width=1
            )

