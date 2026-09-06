"""
MODULA - Smart Auto Failover v2.4
Detailed Activity & Failover Log History Modal with Search & Export.
"""
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional
import customtkinter as ctk

from core.models import LogEvent, LogLevel
from core.sound_engine import SoundEngine, SoundType


class LogDetailModal(ctk.CTkToplevel):
    """
    Detailed Fullscreen/Large Log Dialog with live search filter,
    log-level filter buttons, and file export options.
    """

    def __init__(self, master, log_history: List[LogEvent]):
        super().__init__(master)
        self.title("📋 Riwayat Lengkap Aktivitas & Failover Jaringan • MODULA")
        self.geometry("780x560")
        self.minsize(640, 420)

        self.transient(master)
        self.grab_set()

        self.all_logs: List[LogEvent] = list(log_history)
        self.active_level_filter: Optional[LogLevel] = None
        self.search_term: str = ""

        self._build_ui()
        self._refresh_log_view()

    def _build_ui(self):
        self.configure(fg_color=("#F8FAFC", "#12141C"))
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header Row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        left_hdr = ctk.CTkFrame(header, fg_color="transparent")
        left_hdr.pack(side="left")

        ctk.CTkLabel(
            left_hdr,
            text="📋 Riwayat Lengkap Aktivitas & Failover",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_hdr,
            text="Catatan seluruh pergantian rute metrik, status soket, dan kestabilan koneksi.",
            font=("Segoe UI", 11),
            text_color=("#64748B", "#94A3B8"),
        ).pack(anchor="w")

        # 2. Filter & Search Toolbar
        toolbar = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#181A24"),
            corner_radius=8,
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
        )
        toolbar.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")

        # Search box
        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="🔍 Cari kata kunci log...",
            font=("Segoe UI", 11),
            width=220,
            height=28,
        )
        self.search_entry.pack(side="left", padx=8, pady=6)
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search_changed())

        # Level filters
        levels_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        levels_box.pack(side="left", padx=8)

        self.filter_buttons = {}
        filters = [
            ("Semua", None, ("#E2E8F0", "#282C3D")),
            ("🚨 Failover", LogLevel.FAILOVER, ("#FEE2E2", "#7F1D1D")),
            ("⚠️ Warning", LogLevel.WARNING, ("#FEF3C7", "#78350F")),
            ("ℹ️ Info", LogLevel.INFO, ("#E0F2FE", "#0C4A6E")),
        ]

        for label, lvl, col in filters:
            btn = ctk.CTkButton(
                levels_box,
                text=label,
                command=lambda l=lvl: self._set_level_filter(l),
                font=("Segoe UI", 10, "bold"),
                fg_color=col,
                hover_color=("#CBD5E1", "#374151"),
                text_color=("#0F172A", "#F8FAFC"),
                width=80,
                height=26,
                corner_radius=6,
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[lvl] = btn

        # Right Action Buttons
        right_btns = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_btns.pack(side="right", padx=8)

        ctk.CTkButton(
            right_btns,
            text="💾 Ekspor File...",
            command=self._export_logs,
            font=("Segoe UI", 10, "bold"),
            fg_color=("#10B981", "#059669"),
            hover_color=("#059669", "#047857"),
            text_color="#FFFFFF",
            width=95,
            height=26,
            corner_radius=6,
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            right_btns,
            text="Tutup",
            command=self.destroy,
            font=("Segoe UI", 10),
            fg_color=("#E2E8F0", "#282C3D"),
            hover_color=("#CBD5E1", "#374151"),
            text_color=("#0F172A", "#F8FAFC"),
            width=65,
            height=26,
            corner_radius=6,
        ).pack(side="left", padx=3)

        # 3. Log Console Textbox
        self.textbox = ctk.CTkTextbox(
            self,
            corner_radius=10,
            fg_color=("#FFFFFF", "#0F1118"),
            text_color=("#0F172A", "#CBD5E1"),
            font=("Consolas", 10),
            wrap="word",
            border_width=1,
            border_color=("#CBD5E1", "#242938"),
        )
        self.textbox.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="nsew")

        # Color Tags
        self.textbox.tag_config("FAILOVER", foreground="#EF4444")
        self.textbox.tag_config("RECOVERY", foreground="#10B981")
        self.textbox.tag_config("WARNING", foreground="#F59E0B")
        self.textbox.tag_config("ERROR", foreground="#F87171")
        self.textbox.tag_config("INFO", foreground="#94A3B8")
        self.textbox.tag_config("SUCCESS", foreground="#34D399")
        self.textbox.tag_config("TIMESTAMP", foreground="#64748B")

    def _set_level_filter(self, lvl: Optional[LogLevel]):
        SoundEngine.play(SoundType.ACTION)
        self.active_level_filter = lvl
        self._refresh_log_view()

    def _on_search_changed(self):
        self.search_term = self.search_entry.get().strip().lower()
        self._refresh_log_view()

    def _refresh_log_view(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", tk.END)

        filtered = []
        for ev in self.all_logs:
            if self.active_level_filter and ev.level != self.active_level_filter:
                continue
            if self.search_term and self.search_term not in ev.message.lower() and self.search_term not in ev.level.value.lower():
                continue
            filtered.append(ev)

        if not filtered:
            self.textbox.insert(tk.END, "Tidak ada catatan log yang cocok dengan filter.\n", "INFO")
        else:
            for ev in filtered:
                self.textbox.insert(tk.END, f"[{ev.timestamp}] ", "TIMESTAMP")
                self.textbox.insert(tk.END, f"[{ev.level.value}] ", ev.level.value)
                self.textbox.insert(tk.END, f"{ev.message}\n")

        self.textbox.see(tk.END)
        self.textbox.configure(state="disabled")

    def _export_logs(self):
        SoundEngine.play(SoundType.ACTION)
        filename = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"MODULA_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if not filename:
            return

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("MODULA - Smart Auto Failover v2.4 Activity Log\n")
                f.write(f"Ekspor Pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 70 + "\n\n")
                for ev in self.all_logs:
                    f.write(f"[{ev.timestamp}] [{ev.level.value}] {ev.message}\n")

            SoundEngine.play(SoundType.SUCCESS)
            messagebox.showinfo("Ekspor Berhasil", f"Log berhasil disimpan ke:\n{filename}", parent=self)
        except Exception as e:
            messagebox.showerror("Gagal Ekspor", f"Terjadi kesalahan saat menyimpan file:\n{e}", parent=self)
