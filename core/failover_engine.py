from datetime import datetime
import threading
import time
from typing import Callable, Dict, List, Optional

from .models import (
    FailoverConfig,
    InterfaceStatus,
    LogEvent,
    LogLevel,
    MonitoredInterfaceState,
    PingResult,
    PriorityLevel,
)
from .network_manager import NetworkManager
from .ping_probe import ConcurrentPingManager, PingProbe


class FailoverEngine:
    """
    3-Tier Network Health Monitor and Dynamic Metric Failover Engine.
    Handles proactive ICMP health checks and smooth metric handoffs for Zoom.
    """

    def __init__(
        self,
        config: FailoverConfig,
        on_state_update: Optional[Callable[[Dict[PriorityLevel, MonitoredInterfaceState]], None]] = None,
        on_log: Optional[Callable[[LogEvent]], None] = None,
    ):
        self.config = config
        self.on_state_update = on_state_update
        self.on_log = on_log

        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._ping_manager = ConcurrentPingManager(max_workers=4)

        # Track state for each priority level
        self.states: Dict[PriorityLevel, MonitoredInterfaceState] = {}
        self._healthy_status: Dict[PriorityLevel, bool] = {}
        for p in PriorityLevel:
            alias = getattr(config, f"{p.name.lower()}_alias", "")
            self.states[p] = MonitoredInterfaceState(priority=p, alias=alias)
            self._healthy_status[p] = True

        # Record of initial metrics before engine started
        self._initial_metrics: Dict[str, int] = {}
        self.dry_run = not NetworkManager.is_admin()

    def set_dry_run(self, dry_run: bool):
        self.dry_run = dry_run

    def update_config(self, new_config: FailoverConfig):
        self.config = new_config
        for p in PriorityLevel:
            alias = getattr(new_config, f"{p.name.lower()}_alias", "")
            if p not in self.states:
                self.states[p] = MonitoredInterfaceState(priority=p, alias=alias)
                self._healthy_status[p] = True
            else:
                self.states[p].alias = alias

    def log(self, level: LogLevel, message: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        event = LogEvent(timestamp=now_str, level=level, message=message)
        if self.on_log:
            try:
                self.on_log(event)
            except Exception as e:
                print(f"Error in on_log callback: {e}")

    def start(self):
        """Start monitoring loop in background thread."""
        if self._is_running:
            return

        self._is_running = True
        self._refresh_adapter_info()

        # Check admin status
        if not NetworkManager.is_admin():
            self.dry_run = True
            self.log(
                LogLevel.WARNING,
                "Running in SIMULATION MODE (No Administrator privileges). Route changes will only be simulated."
            )
        else:
            self.log(LogLevel.INFO, "Administrator privileges verified. Live route metric manipulation ENABLED.")

        # Initialize healthy status only for configured and connected interfaces
        for p, state in self.states.items():
            self._healthy_status[p] = bool(state.alias and state.is_connected)

        # Apply initial normal metric scheme
        self.log(LogLevel.INFO, "Initializing interface metrics to Normal baseline scheme...")
        self._apply_normal_metrics()

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="FailoverMonitor")
        self._thread.start()
        self.log(LogLevel.SUCCESS, "Smart Auto-Failover Monitor started.")

    def stop(self, restore_metrics: bool = True):
        """Stop monitoring loop and optionally restore automatic metrics."""
        if not self._is_running:
            return

        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self.log(LogLevel.INFO, "Smart Auto-Failover Monitor stopped.")

        if restore_metrics:
            self.restore_automatic_metrics()

    def restore_automatic_metrics(self):
        """Restore all monitored interfaces to Windows Automatic Metric."""
        self.log(LogLevel.INFO, "Restoring interfaces to Windows Automatic Metric...")
        aliases = [
            s.alias for s in self.states.values()
            if s.alias
        ]

        if self.dry_run:
            self.log(LogLevel.INFO, f"[SIMULATION] Would restore Automatic Metric for: {', '.join(aliases)}")
            return

        for alias in aliases:
            success, msg = NetworkManager.restore_automatic_metric(alias)
            if success:
                self.log(LogLevel.SUCCESS, f"Restored Automatic Metric on '{alias}'")
            else:
                self.log(LogLevel.ERROR, f"Failed to restore Automatic Metric on '{alias}': {msg}")

    def _refresh_adapter_info(self):
        """Query system adapters to sync current IPs, gateways, and metrics."""
        adapters = NetworkManager.get_all_adapters()
        adapter_map = {a.alias: a for a in adapters}

        for p, state in self.states.items():
            if not state.alias:
                state.is_connected = False
                state.status = InterfaceStatus.DISCONNECTED
                continue

            info = adapter_map.get(state.alias)
            if info:
                state.ip = info.ipv4
                state.gateway = info.gateway
                state.is_connected = info.is_connected
                state.current_metric = info.metric
                if state.alias not in self._initial_metrics:
                    self._initial_metrics[state.alias] = info.metric
            else:
                state.is_connected = False
                state.status = InterfaceStatus.DISCONNECTED

    def _apply_metric_if_changed(self, state: MonitoredInterfaceState, target_metric: int) -> bool:
        """Apply metric to interface only if target metric differs from assigned."""
        if not state.alias or not state.is_connected:
            return False

        if state.assigned_metric == target_metric:
            return False

        old_metric = state.assigned_metric or state.current_metric
        state.assigned_metric = target_metric

        if self.dry_run:
            self.log(
                LogLevel.INFO,
                f"[SIMULATION] Metric change on '{state.alias}' ({state.priority.short_label}): {old_metric} -> {target_metric}"
            )
            state.current_metric = target_metric
            return True

        success, msg = NetworkManager.set_interface_metric(state.alias, target_metric)
        if success:
            self.log(
                LogLevel.INFO,
                f"Metric updated on '{state.alias}' ({state.priority.short_label}): {old_metric} -> {target_metric}"
            )
            state.current_metric = target_metric
            return True
        else:
            self.log(LogLevel.ERROR, msg)
            return False

    def _apply_normal_metrics(self):
        """Set baseline metrics across configured interfaces: P1=10, P2=20, P3=30..."""
        for p, state in sorted(self.states.items(), key=lambda x: x[0].value):
            if not state.alias:
                continue
            if p == PriorityLevel.P1:
                metric = self.config.metric_p1_normal
            elif p == PriorityLevel.P2:
                metric = self.config.metric_p2_normal
            elif p == PriorityLevel.P3:
                metric = self.config.metric_p3_normal
            else:
                metric = min(49, 10 * p.value)
            self._apply_metric_if_changed(state, metric)

    def _monitor_loop(self):
        """Continuous health check loop."""
        while self._is_running:
            loop_start = time.perf_counter()

            # Refresh adapter IPs and link states in case of cable plug/unplug
            self._refresh_adapter_info()

            # Submit concurrent ping probes across configured targets
            probe_target = self.config.ping_target_primary or "1.1.1.1"
            futures = {}
            for p, state in self.states.items():
                if state.alias and state.ip and state.is_connected:
                    futures[p] = self._ping_manager.probe_interface(
                        source_ip=state.ip,
                        target=probe_target,
                        timeout_ms=self.config.ping_timeout_ms,
                    )
                else:
                    # Interface disconnected or missing IP
                    futures[p] = None

            # Collect results
            ping_results: Dict[PriorityLevel, Optional[PingResult]] = {}
            for p, future in futures.items():
                if future is not None:
                    try:
                        ping_results[p] = future.result(timeout=(self.config.ping_timeout_ms / 1000.0) + 0.8)
                    except Exception as e:
                        ping_results[p] = PingResult(success=False, error=str(e))
                else:
                    ping_results[p] = None

            # Process health states and check transitions
            self._evaluate_health_and_failover(ping_results)

            # Emit updated state to UI
            if self.on_state_update:
                try:
                    self.on_state_update(self.states)
                except Exception as e:
                    print(f"Error in on_state_update callback: {e}")

            # Sleep remainder of ping_interval_sec
            elapsed = time.perf_counter() - loop_start
            remaining_sleep = max(0.1, self.config.ping_interval_sec - elapsed)
            time.sleep(remaining_sleep)

    def _evaluate_health_and_failover(self, results: Dict[PriorityLevel, Optional[PingResult]]):
        """
        Evaluate ping results, update RTO/success counters, and trigger metric failover/recovery.
        Supports dynamic 1 up to 8 network interfaces.
        """
        for p, state in self.states.items():
            # Skip evaluation for unassigned/unmonitored slots
            if not state.alias:
                state.is_connected = False
                state.status = InterfaceStatus.DISCONNECTED
                state.consecutive_rto = 0
                state.consecutive_success = 0
                state.last_latency_ms = 0.0
                continue

            res = results.get(p)
            state.total_pings += 1

            if res is None or not state.is_connected or not state.ip:
                # Link down or no IP
                state.consecutive_rto += 1
                state.consecutive_success = 0
                state.total_lost += 1
                state.last_latency_ms = 0.0
                state.status = InterfaceStatus.DISCONNECTED
            elif res.success:
                state.consecutive_success += 1
                state.consecutive_rto = 0
                state.last_latency_ms = res.latency_ms
                state.latency_history.append(res.latency_ms)
                if len(state.latency_history) > 30:
                    state.latency_history.pop(0)

                # Check auto-recovery transition
                if not self._healthy_status.get(p, False):
                    if state.consecutive_success >= self.config.recovery_success_threshold:
                        self._healthy_status[p] = True
                        self.log(
                            LogLevel.RECOVERY,
                            f"★ {state.priority.short_label} ('{state.alias}') RECOVERED! "
                            f"({state.consecutive_success} consecutive successful pings)"
                        )
            else:
                # Ping failed / RTO
                state.consecutive_rto += 1
                state.consecutive_success = 0
                state.total_lost += 1
                state.last_latency_ms = 0.0
                state.latency_history.append(0.0)
                if len(state.latency_history) > 30:
                    state.latency_history.pop(0)

                # Check failover transition (only alert if interface was previously healthy)
                if self._healthy_status.get(p, False):
                    if state.consecutive_rto >= self.config.failover_rto_threshold:
                        self._healthy_status[p] = False
                        self.log(
                            LogLevel.FAILOVER,
                            f"⚡ ALERT: {state.priority.short_label} ('{state.alias}') EXPERIENCING PACKET LOSS / RTO! "
                            f"({state.consecutive_rto} consecutive timeouts - {res.error})"
                        )

        # Determine target active interface based on priority hierarchy (P1 -> P2 -> P3 ... -> P8)
        healthy_priorities = [
            p for p in sorted(self.states.keys(), key=lambda x: x.value)
            if self.states[p].alias and self.states[p].is_connected and self._healthy_status.get(p, False)
        ]

        active_priority = healthy_priorities[0] if healthy_priorities else None

        for p, s in self.states.items():
            if not s.alias:
                s.is_active_route = False
                continue
            if p == active_priority:
                s.is_active_route = True
                s.status = InterfaceStatus.ONLINE
                self._apply_metric_if_changed(s, self.config.metric_p1_normal)  # Promoted to 10
            else:
                s.is_active_route = False
                is_h = self._healthy_status.get(p, False) and s.is_connected
                if is_h:
                    s.status = InterfaceStatus.STANDBY
                    metric = min(49, 10 * p.value)
                    self._apply_metric_if_changed(s, metric)
                else:
                    s.status = InterfaceStatus.RTO_FAILING if s.is_connected else InterfaceStatus.DISCONNECTED
                    demoted_metric = self.config.metric_demoted if p == PriorityLevel.P1 else (self.config.metric_demoted + (p.value - 1) * 2)
                    self._apply_metric_if_changed(s, demoted_metric)

        # Check failover transition logs
        if active_priority is not None:
            active_state = self.states[active_priority]
            if not hasattr(self, "_last_active_p"):
                self._last_active_p = active_priority
            elif self._last_active_p != active_priority:
                old_p = self._last_active_p
                self._last_active_p = active_priority
                self.log(
                    LogLevel.FAILOVER,
                    f"⚡ FAILOVER EXECUTED: Default Route switched to {active_priority.short_label} ('{active_state.alias}', Metric {self.config.metric_p1_normal}). Zero-drop active!"
                )

        # Synchronize OS-level route priority
        ordered_aliases = [self.states[p].alias for p in healthy_priorities if self.states[p].alias]
        for s in self.states.values():
            if s.alias and s.alias not in ordered_aliases:
                ordered_aliases.append(s.alias)

        if ordered_aliases and any(ordered_aliases):
            active_name = ordered_aliases[0]
            if not hasattr(self, "_last_primary") or self._last_primary != active_name:
                self._last_primary = active_name
                if not self.dry_run:
                    NetworkManager.set_network_priority_order([a for a in ordered_aliases if a])
