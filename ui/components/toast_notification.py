import queue
import time
import customtkinter as ctk


class ToastNotificationManager:
    """
    Manages floating toast bubble notifications inside the main application window.
    Supports animated slide-in, automatic timeout, and queuing.
    """

    def __init__(self, master):
        self.master = master
        self.toast_frame = None
        self.queue = queue.Queue()
        self.is_showing = False
        self.dismiss_job = None

    def show(self, title: str, message: str, icon: str = "⚡", level: str = "info", duration_ms: int = 2800):
        """Queue and display a toast bubble."""
        self.queue.put((title, message, icon, level, duration_ms))
        if not self.is_showing:
            self._display_next()

    def success(self, message: str, title: str = "Sukses", duration_ms: int = 2800):
        self.show(title=title, message=message, icon="✅", level="success", duration_ms=duration_ms)

    def error(self, message: str, title: str = "Peringatan", duration_ms: int = 3500):
        self.show(title=title, message=message, icon="🚨", level="warning", duration_ms=duration_ms)

    def warning(self, message: str, title: str = "Perhatian", duration_ms: int = 3000):
        self.show(title=title, message=message, icon="⚠️", level="warning", duration_ms=duration_ms)

    def info(self, message: str, title: str = "Informasi", duration_ms: int = 2800):
        self.show(title=title, message=message, icon="ℹ️", level="info", duration_ms=duration_ms)

    def _display_next(self):
        if self.queue.empty():
            self.is_showing = False
            return

        self.is_showing = True
        title, message, icon, level, duration_ms = self.queue.get()

        # Clean previous toast if exists
        if self.toast_frame and self.toast_frame.winfo_exists():
            try:
                self.toast_frame.destroy()
            except Exception:
                pass

        # Color mapping based on level
        is_dark = (ctk.get_appearance_mode() == "Dark")
        level_colors = {
            "info": ("#D97706", "#F59E0B"),       # Barong Gold
            "success": ("#059669", "#10B981"),    # Emerald
            "warning": ("#DC2626", "#E11D48"),    # Crimson
            "failover": ("#DC2626", "#EF4444"),   # Urgent Red
            "qos": ("#4F46E5", "#6366F1"),        # Indigo
            "cyan": ("#0891B2", "#06B6D4"),       # Cyan
        }
        accent = level_colors.get(level, level_colors["info"])
        bg_col = "#1E222D" if is_dark else "#FFFFFF"
        border_col = accent[1] if is_dark else accent[0]

        # Toast Bubble Container Frame
        self.toast_frame = ctk.CTkFrame(
            self.master,
            corner_radius=12,
            border_width=2,
            border_color=border_col,
            fg_color=bg_col,
            width=360,
            height=58,
        )
        self.toast_frame.place(relx=0.98, rely=0.08, anchor="ne")
        self.toast_frame.lift()

        # Grid inside toast
        self.toast_frame.grid_columnconfigure(1, weight=1)

        # Left Icon Badge
        icon_lbl = ctk.CTkLabel(
            self.toast_frame,
            text=icon,
            font=("Segoe UI", 18),
            width=36,
        )
        icon_lbl.grid(row=0, column=0, rowspan=2, padx=(10, 4), pady=6, sticky="nsew")

        # Title Label
        title_lbl = ctk.CTkLabel(
            self.toast_frame,
            text=title,
            font=("Segoe UI", 11, "bold"),
            text_color=border_col,
            anchor="w",
        )
        title_lbl.grid(row=0, column=1, padx=4, pady=(6, 0), sticky="w")

        # Message Label
        msg_lbl = ctk.CTkLabel(
            self.toast_frame,
            text=message,
            font=("Segoe UI", 9),
            text_color=("#64748B", "#94A3B8"),
            anchor="w",
        )
        msg_lbl.grid(row=1, column=1, padx=4, pady=(0, 6), sticky="w")

        # Close button (small x)
        close_btn = ctk.CTkButton(
            self.toast_frame,
            text="×",
            command=self._dismiss,
            width=20,
            height=20,
            font=("Segoe UI", 12, "bold"),
            fg_color="transparent",
            hover_color=("#E2E8F0", "#2D3345"),
            text_color=("#94A3B8", "#64748B"),
        )
        close_btn.grid(row=0, column=2, padx=(0, 6), pady=(4, 0), sticky="ne")

        # Auto-dismiss after duration
        self.dismiss_job = self.master.after(duration_ms, self._dismiss)

    def _dismiss(self):
        if self.dismiss_job:
            try:
                self.master.after_cancel(self.dismiss_job)
            except Exception:
                pass
            self.dismiss_job = None

        if self.toast_frame and self.toast_frame.winfo_exists():
            try:
                self.toast_frame.destroy()
            except Exception:
                pass

        # Check for next queued toast
        self.master.after(100, self._display_next)
