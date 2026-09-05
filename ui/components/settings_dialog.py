from typing import Callable, Optional
import customtkinter as ctk

from core.models import FailoverConfig


class SettingsDialog(ctk.CTkToplevel):
    """
    Configuration modal dialog for tuning ping targets, intervals, metrics, and thresholds.
    """

    def __init__(self, master, config: FailoverConfig, on_save: Optional[Callable[[FailoverConfig], None]] = None):
        super().__init__(master)
        self.title("Settings • Smart Auto-Failover")
        self.geometry("460x520")
        self.resizable(False, False)
        self.config = config
        self.on_save = on_save

        # Make modal
        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color="#181A20")
        self.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="⚙️ Failover & Probe Configuration",
            font=("Segoe UI", 16, "bold"),
            text_color="#F8FAFC",
        )
        title.pack(padx=20, pady=(18, 12), anchor="w")

        # Container Frame
        form = ctk.CTkFrame(self, fg_color="#20232B", corner_radius=10)
        form.pack(padx=20, pady=5, fill="both", expand=True)
        form.grid_columnconfigure(1, weight=1)

        # 1. Ping Target DNS
        ctk.CTkLabel(form, text="Ping Target DNS:", font=("Segoe UI", 12)).grid(
            row=0, column=0, padx=14, pady=(12, 6), sticky="w"
        )
        self.target_entry = ctk.CTkEntry(form, height=28)
        self.target_entry.insert(0, self.config.ping_target_primary)
        self.target_entry.grid(row=0, column=1, padx=14, pady=(12, 6), sticky="ew")

        # 2. Ping Timeout (ms)
        ctk.CTkLabel(form, text="Ping Timeout (ms):", font=("Segoe UI", 12)).grid(
            row=1, column=0, padx=14, pady=6, sticky="w"
        )
        self.timeout_entry = ctk.CTkEntry(form, height=28)
        self.timeout_entry.insert(0, str(self.config.ping_timeout_ms))
        self.timeout_entry.grid(row=1, column=1, padx=14, pady=6, sticky="ew")

        # 3. Ping Interval (ms)
        ctk.CTkLabel(form, text="Ping Interval (ms):", font=("Segoe UI", 12)).grid(
            row=2, column=0, padx=14, pady=6, sticky="w"
        )
        self.interval_entry = ctk.CTkEntry(form, height=28)
        self.interval_entry.insert(0, str(int(self.config.ping_interval_sec * 1000)))
        self.interval_entry.grid(row=2, column=1, padx=14, pady=6, sticky="ew")

        # 4. Failover Threshold (Consecutive RTOs)
        ctk.CTkLabel(form, text="Failover RTO Count:", font=("Segoe UI", 12)).grid(
            row=3, column=0, padx=14, pady=6, sticky="w"
        )
        self.rto_entry = ctk.CTkEntry(form, height=28)
        self.rto_entry.insert(0, str(self.config.failover_rto_threshold))
        self.rto_entry.grid(row=3, column=1, padx=14, pady=6, sticky="ew")

        # 5. Recovery Threshold (Consecutive Successes)
        ctk.CTkLabel(form, text="Recovery OK Count:", font=("Segoe UI", 12)).grid(
            row=4, column=0, padx=14, pady=6, sticky="w"
        )
        self.rec_entry = ctk.CTkEntry(form, height=28)
        self.rec_entry.insert(0, str(self.config.recovery_success_threshold))
        self.rec_entry.grid(row=4, column=1, padx=14, pady=6, sticky="ew")

        # Separator header for metrics
        sep_lbl = ctk.CTkLabel(
            form, text="Route Metrics (Lower = Higher Priority)", font=("Segoe UI", 11, "bold"), text_color="#94A3B8"
        )
        sep_lbl.grid(row=5, column=0, columnspan=2, padx=14, pady=(12, 4), sticky="w")

        # Metrics row
        metrics_frame = ctk.CTkFrame(form, fg_color="transparent")
        metrics_frame.grid(row=6, column=0, columnspan=2, padx=14, pady=4, sticky="ew")
        for i in range(4):
            metrics_frame.grid_columnconfigure(i, weight=1)

        # P1 Normal
        ctk.CTkLabel(metrics_frame, text="P1 Normal:", font=("Segoe UI", 10)).grid(row=0, column=0)
        self.p1_met_entry = ctk.CTkEntry(metrics_frame, width=50, height=26)
        self.p1_met_entry.insert(0, str(self.config.metric_p1_normal))
        self.p1_met_entry.grid(row=1, column=0, padx=2)

        # P2 Normal
        ctk.CTkLabel(metrics_frame, text="P2 Normal:", font=("Segoe UI", 10)).grid(row=0, column=1)
        self.p2_met_entry = ctk.CTkEntry(metrics_frame, width=50, height=26)
        self.p2_met_entry.insert(0, str(self.config.metric_p2_normal))
        self.p2_met_entry.grid(row=1, column=1, padx=2)

        # P3 Normal
        ctk.CTkLabel(metrics_frame, text="P3 Normal:", font=("Segoe UI", 10)).grid(row=0, column=2)
        self.p3_met_entry = ctk.CTkEntry(metrics_frame, width=50, height=26)
        self.p3_met_entry.insert(0, str(self.config.metric_p3_normal))
        self.p3_met_entry.grid(row=1, column=2, padx=2)

        # Demoted
        ctk.CTkLabel(metrics_frame, text="Demoted:", font=("Segoe UI", 10)).grid(row=0, column=3)
        self.demote_met_entry = ctk.CTkEntry(metrics_frame, width=50, height=26)
        self.demote_met_entry.insert(0, str(self.config.metric_demoted))
        self.demote_met_entry.grid(row=1, column=3, padx=2)

        # Bottom Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=20, pady=16, fill="x")
        btn_frame.grid_columnconfigure(0, weight=1)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="#2D3139",
            hover_color="#374151",
            width=90,
            height=32,
        )
        cancel_btn.grid(row=0, column=1, padx=6)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save Settings",
            command=self._save,
            fg_color="#10B981",
            hover_color="#059669",
            width=110,
            height=32,
        )
        save_btn.grid(row=0, column=2, padx=6)

    def _save(self):
        try:
            self.config.ping_target_primary = self.target_entry.get().strip() or "1.1.1.1"
            self.config.ping_timeout_ms = int(self.timeout_entry.get().strip())
            self.config.ping_interval_sec = max(0.5, int(self.interval_entry.get().strip()) / 1000.0)
            self.config.failover_rto_threshold = max(1, int(self.rto_entry.get().strip()))
            self.config.recovery_success_threshold = max(1, int(self.rec_entry.get().strip()))
            self.config.metric_p1_normal = int(self.p1_met_entry.get().strip())
            self.config.metric_p2_normal = int(self.p2_met_entry.get().strip())
            self.config.metric_p3_normal = int(self.p3_met_entry.get().strip())
            self.config.metric_demoted = int(self.demote_met_entry.get().strip())

            if self.on_save:
                self.on_save(self.config)

            self.destroy()
        except ValueError as e:
            # Simple error alert
            pass

