from typing import Callable, List, Optional
import customtkinter as ctk

from core.models import InterfaceStatus, MonitoredInterfaceState, PriorityLevel
from .latency_sparkline import LatencySparkline


class InterfaceCard(ctk.CTkFrame):
    """
    Modern card representing a prioritized network interface
    with real-time metrics, connection bubbles, manual on/off toggle, and latency sparkline.
    Supports Dual Mode (Dark & Light).
    """

    def __init__(
        self,
        master,
        priority: PriorityLevel,
        on_adapter_selected: Optional[Callable[[PriorityLevel, str], None]] = None,
        on_toggle_adapter: Optional[Callable[[str, bool], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=12,
            border_width=1,
            border_color=("#CBD5E1", "#2D3139"),
            fg_color=("#FFFFFF", "#1E212B"),
            **kwargs,
        )
        self.priority = priority
        self.on_adapter_selected = on_adapter_selected
        self.on_toggle_adapter = on_toggle_adapter
        self.current_alias: str = ""

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # 1. Header with Priority Badge and Metric
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        p_colors = {
            PriorityLevel.P1: (("#FEF3C7", "#78350F"), ("#92400E", "#FDE68A"), "PRIORITY 1 • PRIMARY"),
            PriorityLevel.P2: (("#FFE4E6", "#881337"), ("#BE123C", "#FDA4AF"), "PRIORITY 2 • BACKUP"),
            PriorityLevel.P3: (("#CFFAFE", "#164E63"), ("#0E7490", "#67E8F9"), "PRIORITY 3 • FALLBACK"),
        }
        bg_col, text_col, tag_text = p_colors.get(
            self.priority, (("#F1F5F9", "#1F2937"), ("#334155", "#9CA3AF"), "INTERFACE")
        )

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
            fg_color=("#E2E8F0", "#2A2F3D"),
            text_color=("#0F172A", "#E2E8F0"),
            corner_radius=6,
            padx=8,
            pady=2,
        )
        self.metric_badge.grid(row=0, column=1, sticky="e")

        # 2. Adapter Selection Dropdown & Manual Toggle Switch
        select_frame = ctk.CTkFrame(self, fg_color="transparent")
        select_frame.grid(row=1, column=0, padx=14, pady=(2, 6), sticky="ew")
        select_frame.grid_columnconfigure(0, weight=1)

        self.adapter_dropdown = ctk.CTkOptionMenu(
            select_frame,
            values=["Select Adapter..."],
            command=self._on_dropdown_change,
            font=("Segoe UI", 12),
            fg_color=("#E2E8F0", "#242938"),
            button_color=("#D97706", "#F59E0B"),
            button_hover_color=("#B45309", "#D97706"),
            text_color=("#0F172A", "#F8FAFC"),
            dropdown_font=("Segoe UI", 11),
            height=30,
        )
        self.adapter_dropdown.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        # Manual Connect/Disconnect switch
        self.toggle_var = ctk.BooleanVar(value=True)
        self.toggle_switch = ctk.CTkSwitch(
            select_frame,
            text="Port",
            variable=self.toggle_var,
            command=self._on_toggle_clicked,
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
            switch_width=36,
            switch_height=18,
        )
        self.toggle_switch.grid(row=0, column=1, sticky="e")

        # 3. Status Bubbles Row (Terhubung & Aktif)
        bubbles_row = ctk.CTkFrame(self, fg_color="transparent")
        bubbles_row.grid(row=2, column=0, padx=14, pady=(0, 4), sticky="ew")
        bubbles_row.grid_columnconfigure(0, weight=1)

        self.conn_bubble = ctk.CTkLabel(
            bubbles_row,
            text="⚪ Terputus",
            font=("Segoe UI", 10, "bold"),
            fg_color=("#F1F5F9", "#242833"),
            text_color=("#64748B", "#94A3B8"),
            corner_radius=6,
            padx=6,
            pady=2,
        )
        self.conn_bubble.pack(side="left", padx=(0, 4))

        self.active_bubble = ctk.CTkLabel(
            bubbles_row,
            text="Standby",
            font=("Segoe UI", 10, "bold"),
            fg_color=("#F1F5F9", "#242833"),
            text_color=("#64748B", "#94A3B8"),
            corner_radius=6,
            padx=6,
            pady=2,
        )
        self.active_bubble.pack(side="left")

        # 4. Latency Display & Sparkline
        latency_frame = ctk.CTkFrame(
            self,
            fg_color=("#F1F5F9", "#171922"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#232833"),
        )
        latency_frame.grid(row=3, column=0, padx=14, pady=4, sticky="ew")
        latency_frame.grid_columnconfigure(0, weight=1)

        top_lat_row = ctk.CTkFrame(latency_frame, fg_color="transparent")
        top_lat_row.grid(row=0, column=0, padx=10, pady=(6, 2), sticky="ew")
        top_lat_row.grid_columnconfigure(0, weight=1)

        lat_title = ctk.CTkLabel(
            top_lat_row,
            text="ICMP Latency (Ping)",
            font=("Segoe UI", 10),
            text_color=("#64748B", "#94A3B8"),
        )
        lat_title.grid(row=0, column=0, sticky="w")

        self.latency_val_label = ctk.CTkLabel(
            top_lat_row,
            text="-- ms",
            font=("Segoe UI", 15, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        self.latency_val_label.grid(row=0, column=1, sticky="e")

        self.sparkline = LatencySparkline(latency_frame, width=220, height=36)
        self.sparkline.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="ew")

        # 5. Network Details Grid
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.grid(row=4, column=0, padx=14, pady=(2, 10), sticky="ew")
        details_frame.grid_columnconfigure(1, weight=1)

        # IPv4
        ctk.CTkLabel(details_frame, text="IPv4:", font=("Segoe UI", 11), text_color=("#64748B", "#64748B")).grid(
            row=0, column=0, sticky="w", pady=1
        )
        self.ip_label = ctk.CTkLabel(
            details_frame, text="--", font=("Segoe UI", 11, "bold"), text_color=("#0F172A", "#E2E8F0")
        )
        self.ip_label.grid(row=0, column=1, sticky="e", pady=1)

        # Gateway
        ctk.CTkLabel(details_frame, text="Gateway:", font=("Segoe UI", 11), text_color=("#64748B", "#64748B")).grid(
            row=1, column=0, sticky="w", pady=1
        )
        self.gw_label = ctk.CTkLabel(
            details_frame, text="--", font=("Segoe UI", 11), text_color=("#334155", "#CBD5E1")
        )
        self.gw_label.grid(row=1, column=1, sticky="e", pady=1)

        # Consecutive OK / RTO
        ctk.CTkLabel(details_frame, text="Status RTO:", font=("Segoe UI", 11), text_color=("#64748B", "#64748B")).grid(
            row=2, column=0, sticky="w", pady=1
        )
        self.streak_label = ctk.CTkLabel(
            details_frame, text="0 OK • 0 RTO", font=("Segoe UI", 11), text_color=("#334155", "#CBD5E1")
        )
        self.streak_label.grid(row=2, column=1, sticky="e", pady=1)

    def set_adapter_options(self, options: List[str], selected: Optional[str] = None):
        vals = ["(Not Monitored)"] + options
        self.adapter_dropdown.configure(values=vals)
        if selected and selected in vals:
            self.adapter_dropdown.set(selected)
            self.current_alias = selected
        elif not selected and vals:
            self.adapter_dropdown.set(vals[0])
            self.current_alias = ""

    def _on_dropdown_change(self, value: str):
        chosen = "" if value == "(Not Monitored)" else value
        self.current_alias = chosen
        if self.on_adapter_selected:
            self.on_adapter_selected(self.priority, chosen)

    def _on_toggle_clicked(self):
        target_state = self.toggle_var.get()
        if self.on_toggle_adapter and self.current_alias:
            self.on_toggle_adapter(self.current_alias, target_state)

    def update_state(self, state: MonitoredInterfaceState):
        self.current_alias = state.alias
        self.ip_label.configure(text=state.ip if state.ip else "--")
        self.gw_label.configure(text=state.gateway if state.gateway else "--")

        metric_val = state.current_metric if state.current_metric > 0 else state.assigned_metric
        self.metric_badge.configure(
            text=f"Metric: {metric_val}" if metric_val > 0 else "Metric: --"
        )

        streak_text = f"{state.consecutive_success} OK • {state.consecutive_rto} RTO"
        if state.total_pings > 0:
            streak_text += f" ({state.packet_loss_pct:.0f}% loss)"
        self.streak_label.configure(text=streak_text)

        is_rto = (state.consecutive_rto > 0 or not state.is_connected)
        if not state.is_connected or not state.ip:
            self.latency_val_label.configure(text="TERPUTUS", text_color=("#94A3B8", "#64748B"))
        elif is_rto:
            self.latency_val_label.configure(text="RTO TIMEOUT", text_color="#EF4444")
        else:
            lat = state.last_latency_ms
            col = "#10B981" if lat < 50 else ("#3B82F6" if lat < 120 else "#F59E0B")
            self.latency_val_label.configure(text=f"{lat:.0f} ms", text_color=col)

        self.sparkline.update_history(state.latency_history, state.last_latency_ms, is_rto)

        # Update Bubbles
        if state.is_connected and state.ip:
            self.conn_bubble.configure(
                text="🟢 Terhubung",
                fg_color=("#D1FAE5", "#064E3B"),
                text_color=("#065F46", "#34D399"),
            )
            self.toggle_var.set(True)
        else:
            self.conn_bubble.configure(
                text="⚪ Terputus",
                fg_color=("#F1F5F9", "#242833"),
                text_color=("#64748B", "#94A3B8"),
            )

        if state.is_active_route:
            self.configure(border_color="#10B981", border_width=2)
            self.active_bubble.configure(
                text="★ Aktif (Zoom Route)",
                fg_color=("#D1FAE5", "#064E3B"),
                text_color=("#065F46", "#34D399"),
            )
            self.metric_badge.configure(fg_color=("#10B981", "#047857"), text_color="#FFFFFF")
        elif state.status == InterfaceStatus.RTO_FAILING:
            self.configure(border_color="#EF4444", border_width=2)
            self.active_bubble.configure(
                text="⚡ RTO Failing",
                fg_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#991B1B", "#FCA5A5"),
            )
            self.metric_badge.configure(fg_color=("#FEE2E2", "#7F1D1D"), text_color=("#991B1B", "#FECACA"))
        else:
            self.configure(border_color=("#CBD5E1", "#2D3139"), border_width=1)
            self.active_bubble.configure(
                text="Standby",
                fg_color=("#F1F5F9", "#242833"),
                text_color=("#64748B", "#94A3B8"),
            )
            self.metric_badge.configure(fg_color=("#E2E8F0", "#2A2F3D"), text_color=("#0F172A", "#E2E8F0"))
