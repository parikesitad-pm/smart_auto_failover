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
from ..resources import get_asset_path
from ..core.events.bus import EventBus
from ..core.failover.orchestrator import FailoverOrchestrator
from ..platform import get_platform_backend


class AutoFailoverApp:
    """
    Main desktop window container orchestrating the Splash gate
    and the primary automotive-inspired Cockpit dashboard.
    """

    def __init__(self, logo_path: Optional[str] = None):
        if not HAS_CTK:
            raise RuntimeError(
                "CustomTkinter is not available. Please run with --headless or ensure customtkinter and tkinter are installed."
            )

        self.root = ctk.CTk()
        self.root.title("AutoFailover 3.0 by Modula")
        self.root.geometry("1120x720")
        self.root.minsize(980, 640)
        self.root.configure(fg_color=COCKPIT_THEME["bg_dark"])

        # Set cross-platform window icon (Linux iconphoto PNG, Windows iconbitmap ICO)
        self._icon_photo_ref = None
        try:
            if sys.platform.startswith("win"):
                ico_path = get_asset_path("modula_3.0.ico")
                if ico_path and os.path.isfile(ico_path):
                    try:
                        self.root.iconbitmap(ico_path)
                    except Exception:
                        pass
            png_path = get_asset_path("modula_3.0.png")
            if png_path and os.path.isfile(png_path):
                from PIL import Image, ImageTk
                img = Image.open(png_path)
                self._icon_photo_ref = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self._icon_photo_ref)
        except Exception:
            pass

        # Determine logo path via centralized resource resolver
        self.logo_path = logo_path or get_asset_path("modula_3.0.png")

        # Instantiate Platform HAL and Failover Orchestrator
        self.backend = get_platform_backend()
        self.bus = EventBus()
        self.orchestrator = FailoverOrchestrator(platform_backend=self.backend, event_bus=self.bus)

        # Initial hardware discovery & registration gate
        self.orchestrator.initialize()

        # Start orchestrator background engine thread
        self.orchestrator.start()

        # Launch Splash Screen
        self.splash = SplashScreen(
            parent=self.root,
            logo_path=self.logo_path,
            on_complete=self._on_splash_done,
            min_duration_ms=3000,
        )

        # Update initial technical disclosure on splash
        try:
            sys_id = self.backend.get_system_identity()
            ifaces = self.orchestrator.interfaces
            active = self.orchestrator.active_interface
            active_name = active.friendly_name if active else "None"
            summary_text = (
                f"System: {sys_id.get('os_name', 'OS')} ({sys_id.get('architecture', 'arch')})\n"
                f"Discovered: {len(ifaces)} interfaces | Designated Active Path: {active_name}"
            )
            self.splash.update_technical_info(summary_text)
        except Exception:
            pass

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
        """
        Executes an orderly, crash-free teardown:
        1. Halt dashboard polling ticker and cancel running speedtests
        2. Signal orchestrator background thread to stop cleanly
        3. Call platform backend cleanup (restoring Windows automatic metrics)
        4. Destroy Tkinter display context
        """
        # 1. Stop dashboard UI tickers & active benchmark threads
        if hasattr(self, "dashboard") and self.dashboard:
            try:
                self.dashboard.stop()
            except Exception:
                pass

        # 2. Stop background failover orchestrator cleanly
        try:
            self.orchestrator.stop()
        except Exception:
            pass

        # 3. Platform HAL cleanup (restore adapter metrics on Windows)
        if hasattr(self, "backend") and self.backend:
            try:
                self.backend.cleanup()
            except Exception:
                pass

        # 4. Destroy window and exit cleanly
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.root.mainloop()
