import math
import os
import time
import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk
from PIL import Image

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "modula_logo.png")


class SkeletonLoader(ctk.CTkFrame):
    """
    GitHub-style animated skeleton preloader overlay.
    Displays glowing MODULA Barong branding, animated shimmering placeholder cards,
    and a progress status indicator before smoothly transitioning to the main dashboard.
    """

    def __init__(self, master, on_finish: Optional[Callable[[], None]] = None, min_duration: float = 1.3):
        super().__init__(
            master,
            corner_radius=0,
            fg_color=("#F8FAFC", "#12141C"),
        )
        self.master = master
        self.on_finish = on_finish
        self.min_duration = min_duration
        self.start_time = time.time()
        self.shimmer_offset = 0
        self.is_active = True

        self._build_ui()
        self._animate_shimmer()

    def _build_ui(self):
        self.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)
        self.lift()

        is_dark = (ctk.get_appearance_mode() == "Dark")
        bg_col = "#12141C" if is_dark else "#F8FAFC"
        base_skel = "#1E222D" if is_dark else "#E2E8F0"
        text_sub = "#94A3B8" if is_dark else "#64748B"

        # Center Container
        center_box = ctk.CTkFrame(self, fg_color="transparent")
        center_box.place(relx=0.5, rely=0.46, anchor="center", relwidth=0.88)

        # 1. Logo & Branding Header
        logo_box = ctk.CTkFrame(center_box, fg_color="transparent")
        logo_box.pack(pady=(0, 20))

        if os.path.exists(LOGO_PATH):
            try:
                pil_img = Image.open(LOGO_PATH)
                # Resize keeping aspect ratio
                aspect = pil_img.width / pil_img.height
                img_h = 72
                img_w = int(img_h * aspect)
                self.logo_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(img_w, img_h))
                self.logo_label = ctk.CTkLabel(logo_box, image=self.logo_ctk, text="")
                self.logo_label.pack(pady=(0, 6))
            except Exception:
                pass

        self.title_lbl = ctk.CTkLabel(
            logo_box,
            text="MODULA  •  SMART AUTO FAILOVER",
            font=("Segoe UI", 16, "bold"),
            text_color=("#D97706", "#F59E0B"),
        )
        self.title_lbl.pack()

        self.sub_lbl = ctk.CTkLabel(
            logo_box,
            text="Initialising Network Topology • Calibrating Zero-Drop UDP Routes",
            font=("Segoe UI", 11),
            text_color=text_sub,
        )
        self.sub_lbl.pack(pady=(2, 0))

        # 2. Canvas for Animated Skeleton Wireframe
        self.skel_canvas = tk.Canvas(
            center_box,
            height=280,
            bg=bg_col,
            highlightthickness=0,
        )
        self.skel_canvas.pack(fill="x", pady=10)

        # 3. Status Progress Indicator
        status_box = ctk.CTkFrame(center_box, fg_color="transparent")
        status_box.pack(fill="x", pady=(10, 0))

        self.status_lbl = ctk.CTkLabel(
            status_box,
            text="⚡ Scanning hardware interfaces (PCIe / USB GbE Docking / Wi-Fi)...",
            font=("Segoe UI", 11, "bold"),
            text_color=("#0F172A", "#F8FAFC"),
        )
        self.status_lbl.pack()

        self.progress_bar = ctk.CTkProgressBar(
            status_box,
            height=5,
            corner_radius=3,
            progress_color=("#D97706", "#F59E0B"),
        )
        self.progress_bar.set(0.2)
        self.progress_bar.pack(fill="x", padx=60, pady=8)

    def update_status(self, text: str, progress: float):
        if not self.is_active:
            return
        self.status_lbl.configure(text=text)
        self.progress_bar.set(progress)

    def _animate_shimmer(self):
        if not self.is_active:
            return

        elapsed = time.time() - self.start_time
        self.shimmer_offset = (self.shimmer_offset + 18) % 800

        # Draw wireframe skeletons on canvas
        self._draw_skeleton_rects()

        # Update progress simulation
        if elapsed < self.min_duration * 0.4:
            self.progress_bar.set(0.15 + (elapsed / self.min_duration) * 0.4)
            self.status_lbl.configure(text="🔍 Detecting physical Ethernet ports & active gateways...")
        elif elapsed < self.min_duration * 0.8:
            self.progress_bar.set(0.55 + (elapsed / self.min_duration) * 0.35)
            self.status_lbl.configure(text="🛡️ Calibrating interface route metrics & failover triggers...")
        else:
            self.progress_bar.set(0.95)
            self.status_lbl.configure(text="✨ Ready! Launching Modula Dashboard...")

        if elapsed >= self.min_duration:
            self.finish()
            return

        self.after(35, self._animate_shimmer)

    def _draw_skeleton_rects(self):
        self.skel_canvas.delete("all")
        w = self.skel_canvas.winfo_width() or 760
        h = self.skel_canvas.winfo_height() or 280

        is_dark = (ctk.get_appearance_mode() == "Dark")
        base_col = "#1B1E28" if is_dark else "#E5E9F0"
        card_bg = "#161822" if is_dark else "#F1F5F9"
        border_col = "#242836" if is_dark else "#CBD5E1"

        # Skeleton Summary Bar
        self.skel_canvas.create_rectangle(10, 8, w - 10, 42, fill=card_bg, outline=border_col, width=1)
        self._draw_shimmer_bar(24, 18, 120, 28, base_col)
        self._draw_shimmer_bar(160, 18, 280, 28, base_col)
        self._draw_shimmer_bar(w - 180, 18, w - 24, 28, base_col)

        # Skeleton 3 Interface Cards (P1, P2, P3)
        col_w = (w - 36) / 3
        for i in range(3):
            x1 = 10 + i * (col_w + 8)
            x2 = x1 + col_w
            # Card body
            self.skel_canvas.create_rectangle(x1, 52, x2, 200, fill=card_bg, outline=border_col, width=1)
            # Card header line
            self._draw_shimmer_bar(x1 + 14, 66, x1 + col_w * 0.6, 78, base_col)
            # Status badge
            self._draw_shimmer_bar(x2 - 50, 66, x2 - 14, 78, base_col)
            # Line 1 (IP)
            self._draw_shimmer_bar(x1 + 14, 94, x1 + col_w * 0.75, 106, base_col)
            # Line 2 (Gateway)
            self._draw_shimmer_bar(x1 + 14, 116, x1 + col_w * 0.65, 128, base_col)
            # Line 3 (Metric badge)
            self._draw_shimmer_bar(x1 + 14, 138, x1 + col_w * 0.45, 150, base_col)
            # Sparkline placeholder
            self._draw_shimmer_bar(x1 + 14, 162, x2 - 14, 186, base_col)

        # Skeleton Traffic Chart Bar
        self.skel_canvas.create_rectangle(10, 212, w - 10, 268, fill=card_bg, outline=border_col, width=1)
        self._draw_shimmer_bar(24, 226, 200, 238, base_col)
        self._draw_shimmer_bar(24, 246, w - 24, 258, base_col)

    def _draw_shimmer_bar(self, x1, y1, x2, y2, base_col):
        # Draw base bar
        self.skel_canvas.create_rectangle(x1, y1, x2, y2, fill=base_col, outline="")

        # Compute shimmer highlight intersection
        shim_x1 = self.shimmer_offset - 120
        shim_x2 = self.shimmer_offset + 120
        if shim_x2 > x1 and shim_x1 < x2:
            ix1 = max(x1, shim_x1)
            ix2 = min(x2, shim_x2)
            is_dark = (ctk.get_appearance_mode() == "Dark")
            glow_col = "#2B3245" if is_dark else "#FFFFFF"
            self.skel_canvas.create_rectangle(ix1, y1, ix2, y2, fill=glow_col, outline="")

    def finish(self):
        if not self.is_active:
            return
        self.is_active = False
        try:
            self.destroy()
        except Exception:
            pass
        if self.on_finish:
            self.on_finish()
