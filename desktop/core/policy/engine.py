"""
AutoFailover 3.0 Core - Policy Decision Engine
Author: parikesitad-pm
© 2026
"""

from typing import List, Optional, Tuple
from ...models.interface import NetworkInterface, InterfaceState
from ...models.policy import CandidateScore, PolicyConfig, WorkloadProfile


class PolicyEngine:
    """
    Evaluates candidate quality scores and determines authoritative failover decisions.
    Philosophy: "Switch when necessary, not because you can."
    """

    @staticmethod
    def compute_score(
        interface: NetworkInterface,
        config: PolicyConfig,
        profile: WorkloadProfile,
    ) -> CandidateScore:
        """
        Calculate quality score (0.0 to 100.0+) for an interface path.
        Weighted according to workload profile requirements.
        """
        # Disabled or Offline interfaces receive 0 score
        if not interface.state.is_eligible_candidate() and interface.state != InterfaceState.ONLINE:
            return CandidateScore(
                interface_id=interface.id,
                total_score=0.0,
                latency_score=0.0,
                jitter_score=0.0,
                loss_penalty=0.0,
                preference_bonus=0.0,
            )

        m = interface.metrics

        # Component weights adapted to real-world workload profile
        if profile == WorkloadProfile.CONFERENCE:
            lat_w, jit_w, loss_w = 30.0, 35.0, 35.0
        elif profile == WorkloadProfile.BROADCAST:
            lat_w, jit_w, loss_w = 20.0, 25.0, 55.0  # Packet loss is critical for live streaming
        else:  # BALANCED
            lat_w, jit_w, loss_w = 35.0, 35.0, 30.0

        # Latency component (0ms -> full, 200ms -> 0)
        lat_ratio = max(0.0, min(1.0, m.latency_ms / 200.0))
        latency_score = (1.0 - lat_ratio) * lat_w

        # Jitter component (0ms -> full, 25ms -> 0)
        jit_ratio = max(0.0, min(1.0, m.jitter_ms / 25.0))
        jitter_score = (1.0 - jit_ratio) * jit_w

        # Packet loss penalty: linear up to 10%
        loss_ratio = max(0.0, min(1.0, m.packet_loss_pct / 10.0))
        loss_penalty = loss_ratio * loss_w

        # Preference bonus if configured
        preference_bonus = 5.0 if config.preferred_interface_id == interface.id else 0.0

        raw_total = latency_score + jitter_score - loss_penalty + preference_bonus
        total_score = max(0.0, min(120.0, raw_total))

        return CandidateScore(
            interface_id=interface.id,
            total_score=total_score,
            latency_score=latency_score,
            jitter_score=jitter_score,
            loss_penalty=loss_penalty,
            preference_bonus=preference_bonus,
        )

    @classmethod
    def evaluate_failover(
        cls,
        interfaces: List[NetworkInterface],
        active_id: Optional[str],
        config: PolicyConfig,
        profile: WorkloadProfile,
    ) -> Optional[Tuple[str, str]]:
        """
        Evaluate whether a path switch is justified.
        Returns Optional[(target_interface_id, reason)].
        None = keep current path.
        """
        active_iface = next((i for i in interfaces if i.id == active_id), None)

        # 1. EMERGENCY FAILOVER: Active path is missing, OFFLINE, or DISABLED
        if active_iface is None or not active_iface.state.is_usable():
            candidates = [i for i in interfaces if i.state.is_eligible_candidate()]
            if not candidates:
                return None  # Zero usable paths

            scored = [
                (cls.compute_score(i, config, profile), i)
                for i in candidates
            ]
            scored.sort(key=lambda pair: pair[0].total_score, reverse=True)
            best_score, best_candidate = scored[0]

            if best_score.total_score > 0.0:
                reason = "Active path disconnected/unusable - Emergency failover to best eligible candidate"
                return best_candidate.id, reason
            return None

        # 2. DEGRADED ACTIVE PATH: Active is in ALERT state
        if active_iface.state == InterfaceState.ALERT:
            ready_candidates = [i for i in interfaces if i.state == InterfaceState.READY]
            if ready_candidates:
                scored = [
                    (cls.compute_score(i, config, profile), i)
                    for i in ready_candidates
                ]
                scored.sort(key=lambda pair: pair[0].total_score, reverse=True)
                best_score, best_candidate = scored[0]

                active_score = cls.compute_score(active_iface, config, profile)
                if best_score.total_score > active_score.total_score:
                    reason = f"Active path degraded (ALERT) - Switch to healthy standby {best_candidate.friendly_name}"
                    return best_candidate.id, reason

        # 3. NORMAL TAKEOVER: Active is healthy ONLINE; candidate must exceed active + takeover_margin
        active_score = cls.compute_score(active_iface, config, profile)
        eligible_candidates = [
            i for i in interfaces
            if i.id != active_iface.id and i.state == InterfaceState.READY
        ]

        if not eligible_candidates:
            return None

        scored_candidates = [
            (cls.compute_score(i, config, profile), i)
            for i in eligible_candidates
        ]
        scored_candidates.sort(key=lambda pair: pair[0].total_score, reverse=True)
        best_candidate_score, best_candidate = scored_candidates[0]

        # Anti-Flap Equation: candidate_score >= active_score + takeover_margin
        required_score = active_score.total_score + config.takeover_margin
        if best_candidate_score.total_score >= required_score:
            reason = (
                f"Candidate {best_candidate.friendly_name} score ({best_candidate_score.total_score:.1f}) "
                f"exceeds active ({active_score.total_score:.1f}) by takeover margin ({config.takeover_margin})"
            )
            return best_candidate.id, reason

        return None
