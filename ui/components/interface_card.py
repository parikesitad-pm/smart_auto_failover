from typing import Callable, List, Optional
import customtkinter as ctk

from core.models import InterfaceStatus, MonitoredInterfaceState, PriorityLevel
from .latency_sparkline import LatencySparkline


class InterfaceCard(ctk.CTkFrame):
    """
    Modern card representing a single prioritized network interface
    with real-time metrics, status badges, and latency visualization.
    """

    def __init__(
        self,
        master,
        priority: PriorityLevel,
        on_adapter_selected: Optional[Callable[[PriorityLevel, str], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=12,
            border_width=1,
            border_color="#2D3139",
            fg_color="#1E212B",
            **kwargs,
        )
        self.priority = priority
        self.on_adapter_selected = on_adapter_selected

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # 1. Header with Priority Badge and Role
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=14, pady=(12, 6), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        # Priority tag
        p_colors = {
            PriorityLevel.P1: ("#064E3B", "#34D399", "PRIORITY 1 • PRIMARY"),
            PriorityLevel.P2: ("#1E3A8A", "#60A5FA", "PRIORITY 2 • BACKUP"),
            PriorityLevel.P3: ("#581C87", "#C084FC", "PRIORITY 3 • FALLBACK"),
        }
        bg_col, text_col, tag_text = p_colors.get(self.priority, ("#1F2937", "#9CA3AF", "INTERFACE"))

        self.tag_label = ctk.CTkLabel(
            header_frame,
            text=f" {tag_text} ",
            font=("Segoe UI", 11, "bold"),
            fg_color=bg_col,
            text_color=text_col,
            corner_radius=6,
        )
        self.tag_label.grid(row=0, column=0, sticky="w")

        # Metric Badge
        self.metric_badge = ctk.CTkLabel(
            header_frame,
            text="Metric: --",
            font=("Segoe UI", 12, "bold"),
            fg_color="#2A2F3D",
            text_color="#E2E8F0",
            corner_radius=6,
            padx=8,
            pady=2,
        )
        self.metric_badge.grid(row=0, column=1, sticky="e")

        # 2. Adapter Selection Dropdown
        select_frame = ctk.CTkFrame(self, fg_color="transparent")
        select_frame.grid(row=1, column=0, padx=14, pady=(2, 6), sticky="ew")
        select_frame.grid_columnconfigure(0, weight=1)

        self.adapter_dropdown = ctk.CTkOptionMenu(
            select_frame,
            values=["Select Adapter..."],
            command=self._on_dropdown_change,
            font=("Segoe UI", 12),
            fg_color="#2D3139",
            button_color="#3B82F6",
            button_hover_color="#2563EB",
            dropdown_font=("Segoe UI", 11),
            height=30,
        )
        self.adapter_dropdown.grid(row=0, column=0, sticky="ew")

        # 3. Status Banner
        self.status_banner = ctk.CTkLabel(
            self,
            text="⚪ DISCONNECTED",
            font=("Segoe UI", 11, "bold"),
            fg_color="#242833",
            text_color="#94A3B8",
            corner_radius=6,
            height=26,
        )
        self.status_banner.grid(row=2, column=0, padx=14, pady=4, sticky="ew")

        # 4. Latency Display & Sparkline
        latency_frame = ctk.CTkFrame(self, fg_color="#171922", corner_radius=8)
        latency_frame.grid(row=3, column=0, padx=14, pady=6, sticky="ew")
        latency_frame.grid_columnconfigure(0, weight=1)

        top_lat_row = ctk.CTkFrame(latency_frame, fg_color="transparent")
        top_lat_row.grid(row=0, column=0, padx=10, pady=(8, 2), sticky="ew")
        top_lat_row.grid_columnconfigure(0, weight=1)

        lat_title = ctk.CTkLabel(
            top_lat_row,
            text="ICMP Health (Ping)",
            font=("Segoe UI", 10),
            text_color="#94A3B8",
        )
        lat_title.grid(row=0, column=0, sticky="w")

        self.latency_val_label = ctk.CTkLabel(
            top_lat_row,
            text="-- ms",
            font=("Segoe UI", 16, "bold"),
            text_color="#F8FAFC",
        )
        self.latency_val_label.grid(row=0, column=1, sticky="e")

        # Sparkline canvas
        self.sparkline = LatencySparkline(latency_frame, width=220, height=36)
        self.sparkline.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="ew")

        # 5. Network Details Grid
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.grid(row=4, column=0, padx=14, pady=(4, 12), sticky="ew")
        details_frame.grid_columnconfigure(1, weight=1)

        # IP Address
        ctk.CTkLabel(details_frame, text="IPv4:", font=("Segoe UI", 11), text_color="#64748B").grid(
            row=0, column=0, sticky="w", pady=1
        )
        self.ip_label = ctk.CTkLabel(
            details_frame, text="--", font=("Segoe UI", 11, "bold"), text_color="#E2E8F0"
        )
        self.ip_label.grid(row=0, column=1, sticky="e", pady=1)

        # Gateway
        ctk.CTkLabel(details_frame, text="Gateway:", font=("Segoe UI", 11), text_color="#64748B").grid(
            row=1, column=0, sticky="w", pady=1
        )
        self.gw_label = ctk.CTkLabel(
            details_frame, text="--", font=("Segoe UI", 11), text_color="#CBD5E1"
        )
        self.gw_label.grid(row=1, column=1, sticky="e", pady=1)

        # Consecutive / Loss
        ctk.CTkLabel(details_frame, text="RTO / Streak:", font=("Segoe UI", 11), text_color="#64748B").grid(
            row=2, column=0, sticky="w", pady=1
        )
        self.streak_label = ctk.CTkLabel(
            details_frame, text="0 OK • 0 RTO", font=("Segoe UI", 11), text_color="#CBD5E1"
        )
        self.streak_label.grid(row=2, column=1, sticky="e", pady=1)

    def set_adapter_options(self, options: List[str], selected: Optional[str] = None):
        vals = ["(Not Monitored)"] + options
        self.adapter_dropdown.configure(values=vals)
        if selected and selected in vals:
            self.adapter_dropdown.set(selected)
        elif not selected and vals:
            self.adapter_dropdown.set(vals[0])

    def _on_dropdown_change(self, value: str):
        chosen = "" if value == "(Not Monitored)" else value
        if self.on_adapter_selected:
            self.on_adapter_selected(self.priority, chosen)

    def update_state(self, state: MonitoredInterfaceState):
        # Update IP and Gateway
        self.ip_label.configure(text=state.ip if state.ip else "--")
        self.gw_label.configure(text=state.gateway if state.gateway else "--")

        # Update Metric Badge
        metric_val = state.current_metric if state.current_metric > 0 else state.assigned_metric
        self.metric_badge.configure(
            text=f"Metric: {metric_val}" if metric_val > 0 else "Metric: --"
        )

        # Update Streaks & Loss
        streak_text = f"{state.consecutive_success} OK • {state.consecutive_rto} RTO"
        if state.total_pings > 0:
            streak_text += f" ({state.packet_loss_pct:.0f}% loss)"
        self.streak_label.configure(text=streak_text)

        # Latency text & Sparkline
        is_rto = (state.consecutive_rto > 0 or not state.is_connected)
        if not state.is_connected or not state.ip:
            self.latency_val_label.configure(text="DISCONNECTED", text_color="#64748B")
        elif is_rto:
            self.latency_val_label.configure(text="TIMEOUT (RTO)", text_color="#EF4444")
        else:
            lat = state.last_latency_ms
            col = "#10B981" if lat < 50 else ("#3B82F6" if lat < 120 else "#F59E0B")
            self.latency_val_label.configure(text=f"{lat:.0f} ms", text_color=col)

        self.sparkline.update_history(state.latency_history, state.last_latency_ms, is_rto)

        # Status Banner & Card Border
        if state.is_active_route:
            self.configure(border_color="#10B981", border_width=2)
            self.status_banner.configure(
                text="★ ACTIVE DEFAULT ROUTE (ZOOM)",
                fg_color="#064E3B",
                text_color="#6EE7B7",
            )
            self.metric_badge.configure(fg_color="#047857", text_color="#FFFFFF")
        elif state.status == InterfaceStatus.RTO_FAILING:
            self.configure(border_color="#EF4444", border_width=2)
            self.status_banner.configure(
                text="⚡ RTO PACKET LOSS / FAILING",
                fg_color="#7F1D1D",
                text_color="#FCA5A5",
            )
            self.metric_badge.configure(fg_color="#7F1D1D", text_color="#FECACA")
        elif state.is_connected:
            self.configure(border_color="#2D3139", border_width=1)
            self.status_banner.configure(
                text="✓ STANDBY (HEALTHY)",
                fg_color="#1E293B",
                text_color="#94A3B8",
            )
            self.metric_badge.configure(fg_color="#2A2F3D", text_color="#E2E8F0")
        else:
            self.configure(border_color="#2D3139", border_width=1)
            self.status_banner.configure(
                text="⚪ DISCONNECTED / NO CABLE",
                fg_color="#242833",
                text_color="#64748B",
            )
            self.metric_badge.configure(fg_color="#2A2F3D", text_color="#64748B")

