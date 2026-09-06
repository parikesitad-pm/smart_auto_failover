from typing import List, Optional
import customtkinter as ctk

from core.models import AdapterInfo, AdapterPortSummary


class AdapterSummaryBar(ctk.CTkFrame):
    """
    Summary bar displaying total Ethernet and Wireless adapters
    with live status bubbles ('Terhubung' and 'Aktif').
    Supports dual-mode (Dark / Light).
    """

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            border_color=("#CBD5E1", "#2D3139"),
            fg_color=("#F8FAFC", "#1E212B"),
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # Left Info: Port Counts
        self.port_info_label = ctk.CTkLabel(
            self,
            text="🌐 Port Jaringan: Memuat...",
            font=("Segoe UI", 12, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        self.port_info_label.grid(row=0, column=0, padx=14, pady=8, sticky="w")

        # Right Container for Bubbles
        self.bubbles_container = ctk.CTkFrame(self, fg_color="transparent")
        self.bubbles_container.grid(row=0, column=1, padx=14, pady=6, sticky="e")

        # Bubble 1: Terhubung
        self.connected_bubble = ctk.CTkLabel(
            self.bubbles_container,
            text=" 0 Terhubung ",
            font=("Segoe UI", 11, "bold"),
            fg_color=("#D1FAE5", "#064E3B"),
            text_color=("#065F46", "#34D399"),
            corner_radius=6,
            padx=8,
            pady=3,
        )
        self.connected_bubble.pack(side="left", padx=4)

        # Bubble 2: Aktif Default Route
        self.active_bubble = ctk.CTkLabel(
            self.bubbles_container,
            text=" Belum Ada Rute Aktif ",
            font=("Segoe UI", 11, "bold"),
            fg_color=("#E0E7FF", "#1E1B4B"),
            text_color=("#3730A3", "#818CF8"),
            corner_radius=6,
            padx=8,
            pady=3,
        )
        self.active_bubble.pack(side="left", padx=4)

    def update_summary(self, summary: AdapterPortSummary):
        self.port_info_label.configure(
            text=f"🌐 Port Jaringan: {summary.total_ethernet} Ethernet, {summary.total_wireless} Wireless"
        )
        self.connected_bubble.configure(
            text=f" 🟢 {summary.connected_count} Terhubung " if summary.connected_count > 0 else " ⚪ 0 Terhubung "
        )
        if summary.active_route_alias:
            self.active_bubble.configure(
                text=f" ★ Aktif: {summary.active_route_alias} ",
                fg_color=("#D1FAE5", "#064E3B"),
                text_color=("#065F46", "#34D399"),
            )
        else:
            self.active_bubble.configure(
                text=" ⚪ Rute Standby ",
                fg_color=("#F1F5F9", "#242833"),
                text_color=("#64748B", "#94A3B8"),
            )
