"""
AutoFailover 3.0 Core - Failover Engine & Runtime Orchestrator
Author: parikesitad-pm
© 2026
"""

import time
import threading
from typing import List, Dict, Optional, Callable, Any

from ...models.interface import NetworkInterface, InterfaceState
from ...models.policy import PolicyConfig, WorkloadProfile, CandidateScore
from ...models.events import EventType, FailoverEvent
from ...models.snapshot import RuntimeSnapshot
from ...platform.base import PlatformBackend
from ..probe.rfc3550 import RFC3550JitterTracker, probe_socket_rtt
from ..health.evaluator import HealthEngine
from ..policy.engine import PolicyEngine
from ..recovery.arbiter import RecoveryArbiter
from ..events.bus import EventBus
from ..workload.watcher import WorkloadWatcher
from ..telemetry.sampler import TelemetrySampler



class PolicyEngineWrapper:
    """Wrapper exposing policy engine methods and current runtime config."""

    def __init__(self, config: PolicyConfig):
        self.config = config

    def evaluate_failover(self, *args, **kwargs):
        return PolicyEngine.evaluate_failover(*args, **kwargs)

    def compute_score(self, *args, **kwargs):
        return PolicyEngine.compute_score(*args, **kwargs)


class FailoverOrchestrator:
    """
    Main runtime engine driving interface monitoring, probe sampling,
    policy decisions, failover execution, and recovery stabilization.
    Completely decoupled from the UI layer.
    """

    def __init__(
        self,
        platform_backend: PlatformBackend,
        event_bus: Optional[EventBus] = None,
        config: Optional[PolicyConfig] = None,
        probe_target_host: str = "1.1.1.1",
        probe_interval_sec: float = 0.5,
    ):
        self.backend = platform_backend
        self.bus = event_bus or EventBus()
        self.event_bus = self.bus
        self.config = config or PolicyConfig()
        self.policy_engine = PolicyEngineWrapper(self.config)

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
        self._initialized = False
        self._tick_count = 0
        self._loop_thread: Optional[threading.Thread] = None

        # Decoupled thread-safe snapshot for UI rendering
        self._snapshot_lock = threading.Lock()
        self._latest_snapshot: Optional[RuntimeSnapshot] = None
        self._last_telemetry_time: float = 0.0
        self._last_workload_time: float = 0.0
        self._cached_workload_apps: List[str] = []
        self._cached_workload_profile: WorkloadProfile = WorkloadProfile.BALANCED
        self._cached_device_health: Optional[Any] = None

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

    @property
    def metrics(self) -> Dict[str, Any]:
        """Provides map of interface metrics indexed by name and id."""
        with self._lock:
            m = {}
            for iface in self._interfaces.values():
                m[iface.name] = iface.metrics
                m[iface.id] = iface.metrics
            return m

    @property
    def latest_device_health(self) -> Any:
        """Returns the latest passively sampled device health."""
        if self._cached_device_health is not None:
            return self._cached_device_health
        return self.telemetry_sampler.sample()

    def _update_snapshot(self) -> RuntimeSnapshot:
        """Constructs an immutable thread-safe snapshot of the current state."""
        now = time.monotonic()
        with self._lock:
            ifaces_copy = [iface.model_copy() for iface in self._interfaces.values()]
            active_id = self._active_interface_id
            metrics_copy = {k: v.model_copy() if hasattr(v, "model_copy") else v for k, v in self.metrics.items()}

        active_if = None
        standby_if = None
        for iface in ifaces_copy:
            if iface.id == active_id:
                active_if = iface
            elif iface.state in (InterfaceState.READY, InterfaceState.ALERT) and not standby_if:
                standby_if = iface

        # Background low-cadence workload update (~2.5s)
        if now - self._last_workload_time >= 2.5 or not self._cached_workload_apps:
            try:
                prof, apps = self.workload_watcher.detect_active_profile()
                self._cached_workload_profile = prof
                self._cached_workload_apps = sorted(list(apps))
                self._last_workload_time = now
            except Exception:
                pass

        # Background low-cadence telemetry update (~1.0s)
        if now - self._last_telemetry_time >= 1.0 or self._cached_device_health is None:
            try:
                self._cached_device_health = self.telemetry_sampler.sample()
                self._last_telemetry_time = now
            except Exception:
                pass

        # Subprocess instrumentation from platform backend if supported
        sub_rate = 0
        if hasattr(self.backend, "get_instrumentation"):
            try:
                sub_rate = self.backend.get_instrumentation().get("subprocess_count_per_min", 0)
            except Exception:
                pass

        # Engine status & subtext
        if active_if:
            st_name = standby_if.friendly_name if standby_if else "None"
            engine_status = "ACTIVE PATH STABLE"
            engine_subtext = f"Active: {active_if.name} | Standby: {st_name} | Margin: {self.config.takeover_margin:.1f} pts"
        else:
            engine_status = "NO ELIGIBLE PATH"
            engine_subtext = "Waiting for usable interface"

        snap = RuntimeSnapshot(
            interfaces=ifaces_copy,
            active_interface_id=active_id,
            active_interface=active_if,
            standby_interface=standby_if,
            metrics=metrics_copy,
            device_health=self._cached_device_health,
            workload_apps=self._cached_workload_apps,
            workload_profile=self._cached_workload_profile.value if hasattr(self._cached_workload_profile, "value") else str(self._cached_workload_profile),
            engine_status=engine_status,
            engine_subtext=engine_subtext,
            takeover_margin=self.config.takeover_margin,
            subprocess_count_per_min=sub_rate,
            timestamp=time.time(),
        )

        with self._snapshot_lock:
            self._latest_snapshot = snap
        return snap

    def get_snapshot(self) -> RuntimeSnapshot:
        """
        Non-blocking read of the latest runtime snapshot.
        Guarantees Tkinter UI thread never blocks on native I/O or background locks.
        """
        with self._snapshot_lock:
            if self._latest_snapshot is not None:
                return self._latest_snapshot
        return self._update_snapshot()


    def set_interface_admin_state(self, iface_id_or_name: str, enabled: bool) -> bool:
        """Administratively enable or disable a network adapter."""
        with self._lock:
            target_iface = self._interfaces.get(iface_id_or_name)
            if not target_iface:
                for iface in self._interfaces.values():
                    if iface.name == iface_id_or_name:
                        target_iface = iface
            if not target_iface:
                return False
            if hasattr(self.backend, "set_interface_admin_state"):
                success = self.backend.set_interface_admin_state(target_iface.name, enabled)
            else:
                success = self.backend.set_interface_state(target_iface.name, enabled)
            if success:
                target_iface.admin_enabled = enabled
                if not enabled:
                    target_iface.state = InterfaceState.DISABLED
                    target_iface.clear_network_addressing()
                else:
                    target_iface.state = InterfaceState.READY
                self.bus.publish(
                    EventType.ADMIN_ENABLED if enabled else EventType.ADMIN_DISABLED,
                    f"Interface {target_iface.friendly_name} administratively {'enabled' if enabled else 'disabled'}",
                    interface_id=target_iface.id,
                    interface_name=target_iface.name,
                )
            return success


    def initialize(self) -> None:
        """Initial hardware discovery and registration gate."""
        with self._lock:
            discovered = self.backend.discover_interfaces()
            for iface in discovered:
                self._interfaces[iface.id] = iface
                if iface.id not in self._jitter_trackers:
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
                target_iface = self._interfaces.get(dev)
                if not target_iface:
                    for iface in self._interfaces.values():
                        if iface.name == dev:
                            target_iface = iface
                            break
                if target_iface:
                    if target_iface.state == InterfaceState.READY:
                        target_iface.state = InterfaceState.ONLINE
                    self._active_interface_id = target_iface.id
            elif self._interfaces:
                for iface in self._interfaces.values():
                    if iface.state == InterfaceState.ONLINE:
                        self._active_interface_id = iface.id
                        break
            self._initialized = True
            self._update_snapshot()

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
            self._tick_count += 1
            # Dynamic rediscovery if empty or periodic
            if not self._interfaces or (self._tick_count % 20 == 0):
                current_discovered = self.backend.discover_interfaces()
                for iface in current_discovered:
                    if iface.id not in self._interfaces:
                        self._interfaces[iface.id] = iface
                        self._jitter_trackers[iface.id] = RFC3550JitterTracker()
                        self.bus.publish(
                            EventType.INTERFACE_DISCOVERED,
                            f"Discovered interface {iface.friendly_name} [{iface.state.value}]",
                            interface_id=iface.id,
                            interface_name=iface.name,
                        )

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
                    iface.state = InterfaceState.OFFLINE
                    self.bus.publish(
                        EventType.CARRIER_DISCONNECTED,
                        f"Physical link disconnected on {iface.friendly_name}",
                        interface_id=iface_id,
                        interface_name=iface.name,
                    )

                if not iface.carrier:
                    if iface.state != InterfaceState.DISABLED:
                        iface.state = InterfaceState.OFFLINE
                    iface.clear_network_addressing()

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
            self._update_snapshot()

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
            if not self._initialized:
                self.initialize()
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

    def start(self) -> None:
        """Alias for start_loop to provide standard lifecycle interface."""
        self.start_loop()

    def stop(self) -> None:
        """Alias for stop_loop to provide standard lifecycle interface."""
        self.stop_loop()


    def _run_loop(self) -> None:
        while self._is_running:
            try:
                self.tick()
            except Exception:
                pass
            time.sleep(self.probe_interval_sec)
