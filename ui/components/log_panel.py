from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from core.models import LogEvent, LogLevel


class LogPanel(ctk.CTkFrame):
    """
    Color-coded activity and failover history log console.
    """

    def __init__(self, master, max_lines: int = 500, **kwargs):
        super().__init__(
            master,
            corner_radius=12,
            border_width=1,
            border_color="#2D3139",
            fg_color="#1A1C23",
            **kwargs,
        )
        self.max_lines = max_lines
        self.auto_scroll_var = ctk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="ew")
        top_bar.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            top_bar,
            text="📋 Activity & Failover Log",
            font=("Segoe UI", 12, "bold"),
            text_color="#E2E8F0",
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Auto-scroll toggle
        auto_chk = ctk.CTkCheckBox(
            top_bar,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            font=("Segoe UI", 11),
            text_color="#94A3B8",
            checkbox_width=16,
            checkbox_height=16,
        )
        auto_chk.grid(row=0, column=1, padx=8, sticky="e")

        # Clear button
        clear_btn = ctk.CTkButton(
            top_bar,
            text="Clear",
            command=self.clear_logs,
            font=("Segoe UI", 11),
            fg_color="#2D3139",
            hover_color="#374151",
            text_color="#E2E8F0",
            width=55,
            height=24,
            corner_radius=6,
        )
        clear_btn.grid(row=0, column=2, padx=4, sticky="e")

        # Export button
        export_btn = ctk.CTkButton(
            top_bar,
            text="Export...",
            command=self.export_logs,
            font=("Segoe UI", 11),
            fg_color="#2D3139",
            hover_color="#374151",
            text_color="#E2E8F0",
            width=65,
            height=24,
            corner_radius=6,
        )
        export_btn.grid(row=0, column=3, padx=(4, 0), sticky="e")

        # Text Box
        self.textbox = ctk.CTkTextbox(
            self,
            corner_radius=8,
            fg_color="#12131A",
            text_color="#CBD5E1",
            font=("Consolas", 10),
            wrap="word",
            border_width=0,
        )
        self.textbox.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="nsew")

        # Setup Tk Text tags for syntax highlighting
        # Access underlying Tkinter Text widget
        tk_text: tk.Text = self.textbox._textbox
        tk_text.tag_config("TIME", foreground="#64748B")
        tk_text.tag_config("FAILOVER", foreground="#F87171", font=("Consolas", 10, "bold"))
        tk_text.tag_config("RECOVERY", foreground="#34D399", font=("Consolas", 10, "bold"))
        tk_text.tag_config("SUCCESS", foreground="#10B981")
        tk_text.tag_config("WARN", foreground="#FBBF24")
        tk_text.tag_config("ERROR", foreground="#EF4444", font=("Consolas", 10, "bold"))
        tk_text.tag_config("INFO", foreground="#94A3B8")

    def append_log(self, event: LogEvent):
        tk_text: tk.Text = self.textbox._textbox
        tk_text.configure(state="normal")

        # Format: [HH:MM:SS] [LEVEL] Message
        tk_text.insert("end", f"[{event.timestamp}] ", "TIME")
        tk_text.insert("end", f"[{event.level.value}] ", event.level.name)
        tk_text.insert("end", f"{event.message}\n", event.level.name if event.level in (LogLevel.FAILOVER, LogLevel.RECOVERY) else "INFO")

        # Enforce max lines
        lines = int(tk_text.index("end-1c").split(".")[0])
        if lines > self.max_lines:
            tk_text.delete("1.0", f"{lines - self.max_lines}.0")

        if self.auto_scroll_var.get():
            tk_text.see("end")

        tk_text.configure(state="disabled")

    def clear_logs(self):
        tk_text: tk.Text = self.textbox._textbox
        tk_text.configure(state="normal")
        tk_text.delete("1.0", "end")
        tk_text.configure(state="disabled")

    def export_logs(self):
        content = self.textbox.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showinfo("Export Log", "The log is currently empty.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"failover_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("Export Log", f"Log successfully exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save log: {e}")

