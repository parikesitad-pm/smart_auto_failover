"""
AutoFailover 3.0 Core - Failover Engine & Runtime Orchestrator
Author: parikesitad-pm
© 2026
"""

import time
import threading
from typing import List, Dict, Optional, Callable
from ...models.interface import NetworkInterface, InterfaceState
from ...models.policy import PolicyConfig, WorkloadProfile, CandidateScore
from ...models.events import EventType, FailoverEvent
from ...platform.base import PlatformBackend
from ..probe.rfc3550 import RFC3550JitterTracker, probe_socket_rtt
from ..health.evaluator import HealthEngine
from ..policy.engine import PolicyEngine
from ..recovery.arbiter import RecoveryArbiter
from ..events.bus import EventBus
from ..workload.watcher import WorkloadWatcher
from ..telemetry.sampler import TelemetrySampler


class FailoverOrchestrator:
    """
    Main runtime engine driving interface monitoring, probe sampling,
    policy decisions, failover execution, and recovery stabilization.
    Completely decoupled from the UI layer.
    """

    def __init__(
        self,
        platform_backend: PlatformBackend,
        event_bus: EventBus,
        config: Optional[PolicyConfig] = None,
        probe_target_host: str = "1.1.1.1",
        probe_interval_sec: float = 0.5,
    ):
        self.backend = platform_backend
        self.bus = event_bus
        self.config = config or PolicyConfig()
        self.probe_target_host = probe_target_host
        self.probe_interval_sec = probe_interval_sec

        self.recovery = RecoveryArbiter(default_cooldown_sec=self.config.recovery_cooldown_seconds)
        self.workload_watcher = WorkloadWatcher()
        self.telemetry_sampler = TelemetrySampler()

        self._interfaces: Dict[str, NetworkInterface] = {}
        self._jitter_trackers: Dict[str, RFC3550JitterTracker] = {}
        self._active_interface_id: Optional[str] = None
        self._lock = threading.RLock()
        self._is_running = False
        self._loop_thread: Optional[threading.Thread] = None

    @property
    def interfaces(self) -> List[NetworkInterface]:
        with self._lock:
            return list(self._interfaces.values())

    @property
    def active_interface_id(self) -> Optional[str]:
        with self._lock:
            return self._active_interface_id

    @property
    def active_interface(self) -> Optional[NetworkInterface]:
        with self._lock:
            if self._active_interface_id:
                return self._interfaces.get(self._active_interface_id)
            return None

    def initialize(self) -> None:
        """Initial hardware discovery and registration gate."""
        with self._lock:
            discovered = self.backend.discover_interfaces()
            for iface in discovered:
                self._interfaces[iface.id] = iface
                self._jitter_trackers[iface.id] = RFC3550JitterTracker()
                self.bus.publish(
                    EventType.INTERFACE_DISCOVERED,
                    f"Discovered interface {iface.friendly_name} [{iface.state.value}]",
                    interface_id=iface.id,
                    interface_name=iface.name,
                )

            # Determine initial active path from default route
            default_route = self.backend.get_default_route()
            if default_route:
                dev, gw = default_route
                if dev in self._interfaces:
                    iface = self._interfaces[dev]
                    if iface.state == InterfaceState.READY:
                        iface.state = InterfaceState.ONLINE
                    self._active_interface_id = dev

    def tick(self) -> None:
        """
        Single evaluation tick (typically 2–10 Hz):
        1. Dynamic details & carrier query per interface
        2. Socket probe & RFC 3550 jitter calculation
        3. Health evaluation
        4. Policy arbitration
        5. Failover execution if triggered
        """
        with self._lock:
            # 1. Update dynamic interface states
            for iface_id, iface in list(self._interfaces.items()):
                details = self.backend.query_interface_details(iface.name)
                prev_carrier = iface.carrier
                prev_admin = iface.admin_enabled
                prev_state = iface.state

                iface.carrier = details["carrier"]
                iface.admin_enabled = details["admin_enabled"]
                iface.ip_address = details["ip_address"]
                iface.netmask = details["netmask"]
                iface.gateway = details["gateway"]
                iface.ssid = details["ssid"]
                iface.link_speed = details["link_speed"]

                # Carrier Transition Events
                if not prev_carrier and iface.carrier:
                    self.recovery.notify_carrier_restored(iface_id)
                    self.bus.publish(
                        EventType.CARRIER_CONNECTED,
                        f"Physical link carrier restored on {iface.friendly_name}",
                        interface_id=iface_id,
                        interface_name=iface.name,
                    )
                elif prev_carrier and not iface.carrier:
                    self.recovery.notify_carrier_lost(iface_id)
                    iface.clear_network_addressing()
                    self.bus.publish(
                        EventType.CARRIER_DISCONNECTED,
                        f"Physical link disconnected on {iface.friendly_name}",
                        interface_id=iface_id,
                        interface_name=iface.name,
                    )

                # Admin State Transition Events
                if prev_admin and not iface.admin_enabled:
                    iface.clear_network_addressing()
                    iface.state = InterfaceState.DISABLED
                    self.bus.publish(
                        EventType.ADMIN_DISABLED,
                        f"Interface {iface.friendly_name} administratively disabled at OS level",
                        interface_id=iface_id,
                        interface_name=iface.name,
                    )
                elif not prev_admin and iface.admin_enabled:
                    self.bus.publish(
                        EventType.ADMIN_ENABLED,
                        f"Interface {iface.friendly_name} administratively enabled",
                        interface_id=iface_id,
                        interface_name=iface.name,
                    )

                # 2. Probe if interface has carrier & IP
                if iface.admin_enabled and iface.carrier and iface.ip_address:
                    t_send = time.monotonic()
                    success, rtt_ms = probe_socket_rtt(
                        self.probe_target_host,
                        target_port=443,
                        timeout_sec=0.6,
                        source_ip=iface.ip_address,
                    )
                    t_recv = time.monotonic()

                    if success:
                        jitter = self._jitter_trackers[iface_id].update(t_send, t_recv)
                        iface.metrics.latency_ms = round(rtt_ms, 1)
                        iface.metrics.jitter_ms = round(jitter, 1)
                        iface.metrics.packet_loss_pct = 0.0
                        iface.metrics.samples_count += 1
                        iface.metrics.last_probe_timestamp = time.time()
                    else:
                        iface.metrics.packet_loss_pct = 100.0
                else:
                    iface.metrics.reset()

                # 3. Health State Evaluation
                iface.metrics.health_index = HealthEngine.calculate_health_index(iface.metrics)
                evaluated_state = HealthEngine.evaluate_state(
                    iface.state,
                    iface.metrics,
                    self.config,
                    iface.carrier,
                )

                # Enforce Recovery Cooldown rule:
                # If recovering, hold at READY (never hijack ONLINE prematurely)
                if not self.recovery.is_stabilized(iface_id, self.config.recovery_cooldown_seconds):
                    if evaluated_state in (InterfaceState.ONLINE, InterfaceState.READY):
                        evaluated_state = InterfaceState.READY

                if evaluated_state != iface.state:
                    old_st = iface.state
                    iface.state = evaluated_state
                    self.bus.publish(
                        EventType.STATE_TRANSITION,
                        f"{iface.friendly_name} transitioned {old_st.value} -> {evaluated_state.value}",
                        interface_id=iface_id,
                        interface_name=iface.name,
                    )

            # 4. Policy Arbitration
            workload, apps = self.workload_watcher.detect_active_profile()
            switch_decision = PolicyEngine.evaluate_failover(
                list(self._interfaces.values()),
                self._active_interface_id,
                self.config,
                workload,
            )

            if switch_decision is not None:
                target_id, reason = switch_decision
                self._execute_failover(target_id, reason)

            # Check for Zero-Connection state
            usable_paths = [i for i in self._interfaces.values() if i.state.is_usable()]
            if not usable_paths and self._active_interface_id is not None:
                self._active_interface_id = None
                self.bus.publish(
                    EventType.ZERO_CONNECTION,
                    "CRITICAL: Zero usable network connections available. Pipeline is OFFLINE.",
                )

    def _execute_failover(self, target_id: str, reason: str) -> bool:
        """
        Executes Layer-3 route switch and verifies post-flight state.
        """
        target_iface = self._interfaces.get(target_id)
        if not target_iface or not target_iface.gateway:
            return False

        old_active_id = self._active_interface_id
        old_active_iface = self._interfaces.get(old_active_id) if old_active_id else None

        self.bus.publish(
            EventType.FAILOVER_TRIGGERED,
            f"Initiating failover: {reason}",
            interface_id=target_id,
            interface_name=target_iface.name,
            details={"target": target_iface.name, "reason": reason}
        )

        # Execute native Layer-3 route switch
        success = self.backend.set_default_route(target_iface.name, target_iface.gateway)

        # Post-flight verification: inspect actual routing table
        active_route = self.backend.get_default_route()
        verified = (active_route is not None) and (active_route[0] == target_iface.name)

        if success or verified:
            # Transition old active to READY (or maintain degraded ALERT/OFFLINE)
            if old_active_iface:
                if old_active_iface.state == InterfaceState.ONLINE:
                    old_active_iface.state = InterfaceState.READY

            # Promote target to ONLINE
            target_iface.state = InterfaceState.ONLINE
            self._active_interface_id = target_id
            self.recovery.mark_fully_reclaimed(target_id)

            self.bus.publish(
                EventType.ROUTE_SWITCHED,
                f"Successfully switched active path to {target_iface.friendly_name} (gateway: {target_iface.gateway})",
                interface_id=target_id,
                interface_name=target_iface.name,
                details={"verified": verified}
            )
            return True
        else:
            self.bus.publish(
                EventType.STATE_TRANSITION,
                f"Failover to {target_iface.friendly_name} failed during route application.",
                interface_id=target_id,
                interface_name=target_iface.name,
            )
            return False

    def start_loop(self) -> None:
        """Starts background monitoring loop in dedicated thread."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._loop_thread.start()

    def stop_loop(self) -> None:
        """Stops monitoring loop."""
        with self._lock:
            self._is_running = False
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=1.5)

    def _run_loop(self) -> None:
        while self._is_running:
            try:
                self.tick()
            except Exception:
                pass
            time.sleep(self.probe_interval_sec)
