import argparse
import sys
import customtkinter as ctk

from core.network_manager import NetworkManager
from splash_screen import SplashScreen
from ui.app_window import AppWindow


def main():
    parser = argparse.ArgumentParser(description="Smart Auto-Failover Network Monitor for Windows")
    parser.add_argument("--simulate", action="store_true", help="Force simulation mode (do not alter system metrics)")
    parser.add_argument("--require-admin", action="store_true", help="Automatically prompt for UAC elevation if not admin")
    parser.add_argument("--no-splash", action="store_true", help="Skip splash screen and launch main window directly")
    args = parser.parse_args()

    # If --require-admin requested and not admin, prompt UAC elevation immediately
    if args.require_admin and not NetworkManager.is_admin():
        if NetworkManager.request_elevation():
            sys.exit(0)

    # Set CustomTkinter theme
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    # Launch GUI with Enterprise Splash Screen
    app = AppWindow()
    if args.simulate:
        app.engine.set_dry_run(True)

    if args.no_splash:
        app.deiconify()
    else:
        app.withdraw()

        def on_splash_finish():
            app.deiconify()
            app.lift()
            app.focus_force()

        SplashScreen(master=app, on_finish=on_splash_finish, duration=3.0)

    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nShutdown requested by user. Restoring automatic metrics...")
        app.engine.stop(restore_metrics=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
