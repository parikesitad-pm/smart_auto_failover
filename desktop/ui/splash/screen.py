"""
AutoFailover 3.0 Enterprise Splash / Initialization Gate
Author: parikesitad-pm
© 2026
"""

import os
import time
import threading
from typing import Callable, Optional, Dict, Any

try:
    import customtkinter as ctk
    from PIL import Image
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from ..theme import COCKPIT_THEME


class SplashScreen:
    """
    Enterprise Splash / Initialization Gate for AutoFailover 3.0.
    Executes real discovery/health pipeline in parallel while respecting
    a minimum presentation duration (default 3000ms).
    """

    STAGES = [
        (0.10, "Starting Core..."),
        (0.20, "Reading System Information..."),
        (0.40, "Discovering Network Interfaces..."),
        (0.55, "Reading IP Configuration..."),
        (0.70, "Validating Interface State..."),
        (0.85, "Initializing Network Probes (RFC 3550)..."),
        (0.95, "Evaluating Network Health..."),
        (1.00, "APP READY"),
    ]

    def __init__(
        self,
        parent: Any,
        logo_path: str,
        on_complete: Callable[[], None],
        min_duration_ms: int = 3000,
    ):
        self.parent = parent
        self.logo_path = logo_path
        self.on_complete = on_complete
        self.min_duration_ms = min_duration_ms
        self.start_time = time.time()
        self.is_destroyed = False

        if not HAS_CTK:
            # Headless or missing CTK fallback
            self.parent.after(min_duration_ms, self._finish)
            return

        self.frame = ctk.CTkFrame(self.parent, fg_color=COCKPIT_THEME["bg_dark"])
        self.frame.pack(fill="both", expand=True)

        # Container
        self.content_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Modula Logo
        if os.path.exists(self.logo_path):
            try:
                pil_img = Image.open(self.logo_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 120))
                self.logo_label = ctk.CTkLabel(self.content_frame, image=ctk_img, text="")
                self.logo_label.pack(pady=(0, 20))
            except Exception:
                self.logo_label = ctk.CTkLabel(
                    self.content_frame,
                    text="MODULA",
                    font=("Segoe UI", 28, "bold"),
                    text_color=COCKPIT_THEME["emerald"],
                )
                self.logo_label.pack(pady=(0, 20))
        else:
            self.logo_label = ctk.CTkLabel(
                self.content_frame,
                text="MODULA",
                font=("Segoe UI", 28, "bold"),
                text_color=COCKPIT_THEME["emerald"],
            )
            self.logo_label.pack(pady=(0, 20))

        # Title & Subtitle
        self.title_label = ctk.CTkLabel(
            self.content_frame,
            text="AUTO FAILOVER 3.0",
            font=("Segoe UI", 20, "bold"),
            text_color=COCKPIT_THEME["text_primary"],
        )
        self.title_label.pack(pady=(0, 4))

        self.sub_label = ctk.CTkLabel(
            self.content_frame,
            text="light seamless and usefull",
            font=("Segoe UI", 12),
            text_color=COCKPIT_THEME["text_muted"],
        )
        self.sub_label.pack(pady=(0, 28))

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            self.content_frame,
            width=360,
            height=6,
            progress_color=COCKPIT_THEME["emerald"],
            fg_color=COCKPIT_THEME["border"],
        )
        self.progress_bar.set(0.0)
        self.progress_bar.pack(pady=(0, 10))

        # Stage Status Label
        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="Starting Core...",
            font=("Segoe UI", 11, "bold"),
            text_color=COCKPIT_THEME["cyan"],
        )
        self.status_label.pack(pady=(0, 15))

        # Technical Disclosure Panel
        self.info_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color=COCKPIT_THEME["bg_card"],
            corner_radius=8,
            border_width=1,
            border_color=COCKPIT_THEME["border"],
            width=420,
            height=90,
        )
        self.info_frame.pack(pady=(10, 0))
        self.info_frame.pack_propagate(False)

        self.sys_info_label = ctk.CTkLabel(
            self.info_frame,
            text="Initializing native hardware abstraction layer...",
            font=("Consolas", 10),
            text_color=COCKPIT_THEME["text_secondary"],
            justify="left",
            wraplength=400,
        )
        self.sys_info_label.pack(padx=12, pady=10, anchor="w")

        # Animate stages
        self._current_stage_idx = 0
        self._schedule_next_stage()

    def update_technical_info(self, text: str):
        if HAS_CTK and not self.is_destroyed and hasattr(self, "sys_info_label"):
            self.sys_info_label.configure(text=text)

    def _schedule_next_stage(self):
        if self.is_destroyed:
            return

        if self._current_stage_idx < len(self.STAGES):
            prog, label = self.STAGES[self._current_stage_idx]
            self.progress_bar.set(prog)
            self.status_label.configure(text=label)
            self._current_stage_idx += 1

            step_delay = int(self.min_duration_ms / len(self.STAGES))
            self.parent.after(step_delay, self._schedule_next_stage)
        else:
            # Check elapsed time
            elapsed = (time.time() - self.start_time) * 1000
            remaining = max(0, self.min_duration_ms - elapsed)
            self.parent.after(int(remaining + 350), self._finish)

    def _finish(self):
        if self.is_destroyed:
            return
        self.is_destroyed = True
        if HAS_CTK and hasattr(self, "frame"):
            self.frame.destroy()
        self.on_complete()
