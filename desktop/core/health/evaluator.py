"""
AutoFailover 3.0 Core - Network Health Evaluator & State Assessment
Author: parikesitad-pm
© 2026
"""

from ...models.interface import InterfaceState
from ...models.metrics import PathMetrics
from ...models.policy import PolicyConfig


class HealthEngine:
    """
    Computes composite Network Health index (0–100) and assesses path degradation.
    """

    @staticmethod
    def calculate_health_index(metrics: PathMetrics) -> int:
        """
        Calculate composite 0–100 Network Health Index.
        Factors:
          - Latency (35% weight): 0ms -> 100, 150ms+ -> 0
          - Jitter (35% weight): 0ms -> 100, 30ms+ -> 0
          - Packet loss (30% weight): 0% -> 100, 10%+ -> 0
        """
        if metrics.packet_loss_pct >= 100.0:
            return 0

        # Latency penalty: 0ms -> 100, 150ms+ -> 0
        lat_ratio = max(0.0, min(1.0, metrics.latency_ms / 150.0))
        lat_score = (1.0 - lat_ratio) * 100.0

        # Jitter penalty: 0ms -> 100, 30ms+ -> 0
        jit_ratio = max(0.0, min(1.0, metrics.jitter_ms / 30.0))
        jit_score = (1.0 - jit_ratio) * 100.0

        # Loss penalty: 0% -> 100, 10%+ -> 0
        loss_ratio = max(0.0, min(1.0, metrics.packet_loss_pct / 10.0))
        loss_score = (1.0 - loss_ratio) * 100.0

        composite = (lat_score * 0.35) + (jit_score * 0.35) + (loss_score * 0.30)
        return max(0, min(100, round(composite)))

    @staticmethod
    def evaluate_state(
        current_state: InterfaceState,
        metrics: PathMetrics,
        config: PolicyConfig,
        carrier_detected: bool,
    ) -> InterfaceState:
        """
        Evaluate path state transitions based on live metrics and carrier state.
        Note: Does NOT promote to ONLINE; only determines if degraded (ALERT) or stable standby (READY).
        """
        # Administrative disabled takes strict precedence
        if current_state == InterfaceState.DISABLED:
            return InterfaceState.DISABLED

        # Hard physical link disconnect
        if not carrier_detected:
            return InterfaceState.OFFLINE

        # Degradation conditions
        is_degraded = (
            metrics.latency_ms >= config.latency_alert_threshold_ms
            or metrics.jitter_ms >= config.jitter_alert_threshold_ms
            or metrics.packet_loss_pct >= config.packet_loss_alert_threshold_pct
        )

        if current_state == InterfaceState.ONLINE:
            return InterfaceState.ALERT if is_degraded else InterfaceState.ONLINE
        elif current_state == InterfaceState.ALERT:
            return InterfaceState.ALERT if is_degraded else InterfaceState.READY
        elif current_state == InterfaceState.OFFLINE:
            return InterfaceState.ALERT if is_degraded else InterfaceState.READY
        elif current_state == InterfaceState.READY:
            return InterfaceState.ALERT if is_degraded else InterfaceState.READY

        return InterfaceState.OFFLINE
