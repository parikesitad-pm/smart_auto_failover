"""
AutoFailover 3.0 Desktop Main Application Window
Author: parikesitad-pm
© 2026
"""

import os
import sys
from typing import Optional

try:
    import customtkinter as ctk
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

from .theme import COCKPIT_THEME
from .splash.screen import SplashScreen
from .dashboard.cockpit import CockpitDashboard
from ..core.failover.orchestrator import FailoverOrchestrator
from ..platform import get_platform_backend


class AutoFailoverApp:
    """
    Main desktop GUI application orchestrator for AutoFailover 3.0.
    """

    def __init__(self, logo_path: Optional[str] = None):
        if not HAS_CTK:
            raise RuntimeError(
                "CustomTkinter is not available. Please run with --headless or ensure customtkinter and tkinter are installed."
            )

        self.root = ctk.CTk()
        self.root.title("Auto Failover 3.0.0 by Modula")
        self.root.geometry("1120x720")
        self.root.minsize(980, 640)
        self.root.configure(fg_color=COCKPIT_THEME["bg_dark"])

        # Determine logo path
        if not logo_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logo_path = os.path.join(base_dir, "assets", "modula_3.0.png")
        self.logo_path = logo_path

        # Instantiate Platform HAL and Failover Orchestrator
        self.backend = get_platform_backend()
        self.orchestrator = FailoverOrchestrator(platform_backend=self.backend)

        # Start orchestrator background engine thread
        self.orchestrator.start()

        # Launch Splash Screen
        self.splash = SplashScreen(
            parent=self.root,
            logo_path=self.logo_path,
            on_complete=self._on_splash_done,
            min_duration_ms=3000,
        )

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_splash_done(self):
        # Transition to Cockpit Dashboard
        self.dashboard = CockpitDashboard(
            parent=self.root,
            orchestrator=self.orchestrator,
            logo_path=self.logo_path,
        )

    def _on_close(self):
        # Stop background failover orchestrator cleanly
        try:
            self.orchestrator.stop()
        except Exception:
            pass
        self.root.destroy()
        sys.exit(0)

    def run(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.root.mainloop()
