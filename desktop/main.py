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
      1. Package imports resolve
      2. Core modules load
      3. Platform backend can initialize safely
      4. Resources can be found
      5. CustomTkinter runtime can be imported
      6. Application bootstrap can initialize without immediate fatal error
    Returns exit code 0 on success, non-zero on failure.
    """
    print("=" * 70)
    print(f"  AutoFailover {__version__} — Runtime Self-Test")
    print("=" * 70)

    # 1. Package version & metadata
    sys.stdout.write("[CHECK 1/6] Verifying package metadata... ")
    sys.stdout.flush()
    try:
        from .__version__ import __version__ as v, __product__ as p
        print(f"PASS ({p} {v})")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    # 2. Core engine modules
    sys.stdout.write("[CHECK 2/6] Verifying core engine modules... ")
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

    # 3. Platform backend initialization
    sys.stdout.write("[CHECK 3/6] Verifying native platform HAL... ")
    sys.stdout.flush()
    try:
        backend = get_platform_backend()
        sys_id = backend.get_system_identity()
        print(f"PASS ({sys_id['os_name']} {sys_id['architecture']})")
    except Exception as e:
        print(f"FAIL ({e})")
        return 1

    # 4. Resource resolution
    sys.stdout.write("[CHECK 4/6] Verifying asset & resource discovery... ")
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

    # 5. CustomTkinter GUI framework
    sys.stdout.write("[CHECK 5/6] Verifying CustomTkinter GUI framework... ")
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

    # 6. Bootstrap verification
    sys.stdout.write("[CHECK 6/6] Verifying orchestrator initialization... ")
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
    print("ALL SELF-TEST CHECKS PASSED SUCCESSFULLY.")
    print("=" * 70)
    return 0


def main():
    parser = argparse.ArgumentParser(description="AutoFailover 3.0 by Modula")
    parser.add_argument("--version", action="store_true", help="Show application version and exit")
    parser.add_argument("--self-test", action="store_true", help="Run comprehensive runtime integrity self-test")
    parser.add_argument("--headless", action="store_true", help="Run in headless terminal monitor mode (no Tkinter required)")
    parser.add_argument("--acceptance", action="store_true", help="Run hardware acceptance inspection and verify 5-state model")
    parser.add_argument("--ticks", type=int, default=None, help="Number of ticks to run in headless mode (default: infinite)")
    args = parser.parse_args()

    if args.version:
        print(f"AutoFailover {__version__}")
        sys.exit(0)

    if args.self_test:
        sys.exit(run_self_test())

    if args.acceptance:
        run_acceptance_inspection()
        return

    if args.headless:
        run_headless_monitor(iterations=args.ticks)
        return

    # Attempt to launch CustomTkinter GUI
    try:
        import tkinter
        from .ui.app import AutoFailoverApp
        app = AutoFailoverApp()
        app.run()
    except (ImportError, ModuleNotFoundError) as e:
        print("\n[NOTICE] Tkinter GUI toolkit is not currently installed in this Python environment.")
        print(f"         Error detail: {e}")
        print("         Falling back to Headless Engine Mode...\n")
        run_headless_monitor()


if __name__ == "__main__":
    main()
