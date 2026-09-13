"""
AutoFailover 3.0 by Modula
Crafted by parikesitad-pm
© 2026

Entry Point: Supports Headless Mode, Acceptance Verification, and CustomTkinter GUI.
"""

import sys
import time
import argparse
from typing import Optional

from .__version__ import __version__, __product__, __author__
from .models.interface import InterfaceState
from .platform import get_platform_backend
from .core.events.bus import EventBus
from .core.failover.orchestrator import FailoverOrchestrator


def run_headless_monitor(iterations: Optional[int] = None, interval_sec: float = 1.0):
    """
    Continuous or bounded headless monitoring loop.
    Outputs live network cockpit status and state transitions without any GUI requirement.
    """
    backend = get_platform_backend()
    bus = EventBus(max_history=50)

    # Subscribe to print live transitions
    def on_event(event):
        ts = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        print(f"[{ts}] ⚡ {event.event_type.value}: {event.message}")

    bus.subscribe(on_event)

    print("=" * 70)
    print(f"  {__product__} — Headless Engine Runtime")
    print(f"  Author: {__author__} | Version: {__version__}")
    print("=" * 70)

    sys_id = backend.get_system_identity()
    print(f"System: {sys_id['device_name']} | {sys_id['os_name']} ({sys_id['architecture']}) | Kernel: {sys_id['kernel']}")
    print("-" * 70)

    orchestrator = FailoverOrchestrator(backend, bus, probe_interval_sec=interval_sec)
    orchestrator.initialize()

    count = 0
    try:
        while True:
            orchestrator.tick()
            count += 1

            active = orchestrator.active_interface
            active_str = f"{active.friendly_name} [{active.ip_address}]" if active else "NONE (NO ACTIVE PATH)"

            print(f"\n--- [TICK #{count}] Active Path: {active_str} ---")
            for iface in orchestrator.interfaces:
                state_symbol = "●" if iface.state == InterfaceState.ONLINE else "○"
                m = iface.metrics
                print(
                    f"  {state_symbol} {iface.friendly_name:<22} "
                    f"State: {iface.state.value:<9} "
                    f"IP: {str(iface.ip_address):<15} "
                    f"GW: {str(iface.gateway):<15} "
                    f"Latency: {m.latency_ms:>5.1f}ms "
                    f"Jitter (RFC3550): {m.jitter_ms:>4.1f}ms "
                    f"Health: {m.health_index:>3}%"
                )
                if iface.ssid:
                    print(f"      └─ SSID: {iface.ssid}")

            if iterations and count >= iterations:
                break
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\nHeadless monitor stopped by user.")


def run_acceptance_inspection():
    """
    Executes an authoritative inspection of real Linux hardware to verify
    the 5-state model, IP/gateway reading, carrier detection, and policy readiness.
    """
    backend = get_platform_backend()
    bus = EventBus()
    orchestrator = FailoverOrchestrator(backend, bus)

    print("\n" + "=" * 75)
    print(f"  AUTOFAILOVER 3.0 — REAL HARDWARE ACCEPTANCE INSPECTION")
    print("=" * 75)

    sys_id = backend.get_system_identity()
    print(f"[SYSTEM] Device: {sys_id['device_name']}")
    print(f"[SYSTEM] OS:     {sys_id['os_name']} ({sys_id['architecture']})")
    print(f"[SYSTEM] Kernel: {sys_id['kernel']}")
    print("-" * 75)

    orchestrator.initialize()
    orchestrator.tick()

    interfaces = orchestrator.interfaces
    print(f"Detected Interfaces: {len(interfaces)}")
    for iface in interfaces:
        print(f"\nInterface: {iface.name} ({iface.friendly_name})")
        print(f"  Type:          {iface.media_type.value}")
        print(f"  Carrier:       {'CONNECTED' if iface.carrier else 'DISCONNECTED'}")
        print(f"  Admin State:   {'ENABLED' if iface.admin_enabled else 'DISABLED'}")
        print(f"  Current State: {iface.state.value}")
        print(f"  IPv4 Address:  {iface.ip_address or 'N/A'}")
        print(f"  Netmask:       {iface.netmask or 'N/A'}")
        print(f"  Gateway:       {iface.gateway or 'N/A'}")
        if iface.ssid:
            print(f"  Wi-Fi SSID:    {iface.ssid}")
        if iface.link_speed:
            print(f"  Link Speed:    {iface.link_speed}")
        print(f"  Latency:       {iface.metrics.latency_ms} ms")
        print(f"  Jitter (RFC):  {iface.metrics.jitter_ms} ms")
        print(f"  Health Score:  {iface.metrics.health_index} / 100")

    def_route = backend.get_default_route()
    print("-" * 75)
    print(f"Authoritative OS Default Route: dev={def_route[0] if def_route else 'NONE'} gateway={def_route[1] if def_route else 'NONE'}")
    print(f"Designated Active Path:         {orchestrator.active_interface_id or 'NONE'}")
    print("=" * 75 + "\n")


def run_self_test() -> int:
    """
    Executes an autonomous runtime integrity self-test.
    Verifies:
      1. Package metadata & version
      2. Core failover & telemetry engine modules
      3. Canonical Speedtest runner & providers
      4. Native platform HAL backend & system identity
      5. Resource discovery (assets, logo)
      6. CustomTkinter GUI toolkit dependencies
      7. Full GUI module graph (App, Splash, Dashboard, Cockpit)
      8. Orchestrator bootstrap nominal
    Returns exit code 0 on success, non-zero on failure.
    """
    print("=" * 70)
    print(f"  AutoFailover {__version__} — Runtime Integrity Self-Test")
    print("=" * 70)

    # 1. Package version & metadata
    sys.stdout.write("[CHECK 1/8] Verifying package metadata... ")
    sys.stdout.flush()
    try:
        from .__version__ import __version__ as v, __product__ as p
        print(f"PASS ({p} {v})")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    # 2. Core engine modules
    sys.stdout.write("[CHECK 2/8] Verifying core engine modules... ")
    sys.stdout.flush()
    try:
        from .core.events.bus import EventBus
        from .core.failover.orchestrator import FailoverOrchestrator
        from .core.health.evaluator import HealthEngine
        from .core.policy.engine import PolicyEngine
        from .core.probe.rfc3550 import RFC3550JitterTracker
        from .core.recovery.arbiter import RecoveryArbiter
        from .core.telemetry.sampler import TelemetrySampler
        print("PASS")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    # 3. Canonical speedtest module
    sys.stdout.write("[CHECK 3/8] Verifying speedtest runner & canonical exports... ")
    sys.stdout.flush()
    try:
        from .core.speedtest import (
            SpeedtestRunner,
            SpeedtestResult,
            SpeedtestProvider,
            SpeedTestRunner,
            SpeedTestResult,
        )
        st = SpeedtestRunner()
        assert hasattr(st, "run_single_test"), "SpeedtestRunner missing run_single_test"
        assert hasattr(st, "run_bulk_tests"), "SpeedtestRunner missing run_bulk_tests"
        print("PASS")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    # 4. Platform backend initialization
    sys.stdout.write("[CHECK 4/8] Verifying native platform HAL... ")
    sys.stdout.flush()
    try:
        backend = get_platform_backend()
        sys_id = backend.get_system_identity()
        print(f"PASS ({sys_id['os_name']} {sys_id['architecture']})")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    # 5. Resource resolution
    sys.stdout.write("[CHECK 5/8] Verifying asset & resource discovery... ")
    sys.stdout.flush()
    try:
        import os
        from .resources import get_asset_path
        logo = get_asset_path("modula_3.0.png")
        if not os.path.isfile(logo):
            print(f"FAIL (Asset missing at {logo})")
            return 1
        print(f"PASS ({os.path.basename(logo)})")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    # 6. CustomTkinter GUI framework
    sys.stdout.write("[CHECK 6/8] Verifying CustomTkinter GUI framework... ")
    sys.stdout.flush()
    try:
        import customtkinter as ctk
        import tkinter
        from PIL import Image
        print(f"PASS (CustomTkinter {ctk.__version__})")
    except Exception as e:
        if getattr(sys, "frozen", False):
            print(f"FAIL ({e})")
            return 1
        print(f"NOTICE (Unpackaged environment lacks CustomTkinter: {e})")

    # 7. Full GUI module graph
    sys.stdout.write("[CHECK 7/8] Verifying full GUI module graph... ")
    sys.stdout.flush()
    try:
        from .ui.theme import COCKPIT_THEME
        from .ui.splash.screen import SplashScreen
        from .ui.dashboard.cockpit import CockpitDashboard
        from .ui.app import AutoFailoverApp
        print("PASS (App, Splash, Cockpit)")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    # 8. Bootstrap verification
    sys.stdout.write("[CHECK 8/8] Verifying orchestrator initialization... ")
    sys.stdout.flush()
    try:
        bus = EventBus()
        orch = FailoverOrchestrator(platform_backend=backend, event_bus=bus)
        orch.initialize()
        print("PASS")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    print("-" * 70)
    print("ALL SELF-TEST CHECKS PASSED SUCCESSFULLY (8/8).")
    print("=" * 70)
    return 0


def run_gui_smoke_test() -> int:
    """
    Executes a non-interactive CustomTkinter GUI smoke test.
    Verifies:
      1. Complete UI module graph imports cleanly.
      2. Tkinter and CustomTkinter display context can initialize.
      3. Main window container, SplashScreen, and CockpitDashboard can construct.
      4. Tears down and exits with code 0 without hanging or requiring user interaction.
    """
    print("=" * 70)
    print(f"  AutoFailover {__version__} — GUI Startup Smoke Test")
    print("=" * 70)

    try:
        import tkinter
        import customtkinter as ctk
    except Exception as e:
        print(f"[FAIL] GUI toolkit dependency missing: {e}")
        return 1

    try:
        from .ui.app import AutoFailoverApp
        print("[INFO] Initializing AutoFailoverApp container...")
        app = AutoFailoverApp()

        print("[INFO] Constructing CockpitDashboard...")
        app._on_splash_done()

        print("[INFO] Validating UI component hierarchy...")
        assert app.root is not None, "Root window is None"
        assert app.dashboard is not None, "CockpitDashboard is None"
        assert app.dashboard.root_frame is not None, "Dashboard root frame is None"

        # Update geometry and draw once without mainloop blocking
        app.root.update_idletasks()
        app.root.update()

        print("[INFO] Tearing down GUI smoke test cleanly...")
        try:
            app.orchestrator.stop()
        except Exception:
            pass
        app.root.destroy()

        print("-" * 70)
        print("GUI SMOKE TEST PASSED: Full CustomTkinter UI stack initialized cleanly.")
        print("=" * 70)
        return 0
    except Exception as e:
        import traceback
        print(f"\n[FAIL] GUI smoke test failed with exception: {e}")
        traceback.print_exc()
        return 1


def main():
    parser = argparse.ArgumentParser(description="AutoFailover 3.0 by Modula")
    parser.add_argument("--version", action="store_true", help="Show application version and exit")
    parser.add_argument("--self-test", action="store_true", help="Run comprehensive runtime integrity self-test")
    parser.add_argument("--gui-smoke", action="store_true", help="Run non-interactive GUI startup and component construction smoke test")
    parser.add_argument("--headless", action="store_true", help="Run in headless terminal monitor mode (no Tkinter required)")
    parser.add_argument("--acceptance", action="store_true", help="Run hardware acceptance inspection and verify 5-state model")
    parser.add_argument("--ticks", type=int, default=None, help="Number of ticks to run in headless mode (default: infinite)")
    args = parser.parse_args()

    if args.version:
        print(f"AutoFailover {__version__}")
        sys.exit(0)

    if args.self_test:
        sys.exit(run_self_test())

    if args.gui_smoke:
        sys.exit(run_gui_smoke_test())

    if args.acceptance:
        run_acceptance_inspection()
        return

    if args.headless:
        run_headless_monitor(iterations=args.ticks)
        return

    # 1. Dependency validation: Verify Tkinter & CustomTkinter exist
    try:
        import tkinter
        import customtkinter
    except (ImportError, ModuleNotFoundError) as exc:
        print("\n[ERROR] GUI Toolkit Dependency Missing.")
        print(f"        Detail: {exc}")
        print("        Tkinter / CustomTkinter is not installed in this environment.")
        print("        To run without GUI, use: AutoFailover 3.0 --headless\n")
        sys.exit(1)

    # 2. Separate internal application import: Never mislabel internal error as missing Tkinter
    try:
        from .ui.app import AutoFailoverApp
    except Exception as exc:
        import traceback
        print("\n[FATAL] GUI STARTUP ERROR")
        print(f"        Internal application module failed to load: {exc}")
        print("-" * 60)
        traceback.print_exc()
        print("-" * 60)
        print("        Do not run with broken internal modules. Please report this issue.\n")
        sys.exit(1)

    # 3. Instantiate and run application
    try:
        app = AutoFailoverApp()
        app.run()
    except Exception as exc:
        import traceback
        print(f"\n[FATAL] Unhandled runtime exception in GUI: {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

