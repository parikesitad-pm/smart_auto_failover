"""
AutoFailover 3.0 Core - Policy Decision Engine
Author: parikesitad-pm
© 2026
"""

from typing import List, Optional, Tuple
from ...models.interface import NetworkInterface, InterfaceState, InterfaceMediaType
from ...models.policy import CandidateScore, PolicyConfig, WorkloadProfile


def is_ethernet_interface(iface: NetworkInterface) -> bool:
    """Check if interface is physical Ethernet."""
    if iface.media_type == InterfaceMediaType.ETHERNET:
        return True
    name_l = iface.name.lower()
    fname_l = iface.friendly_name.lower()
    if "eth" in name_l or "ethernet" in fname_l:
        return True
    if name_l.startswith("en") and not any(w in fname_l for w in ("wi-fi", "wifi", "wireless")):
        return True
    return False


def is_wifi_interface(iface: NetworkInterface) -> bool:
    """Check if interface is wireless Wi-Fi."""
    if iface.media_type == InterfaceMediaType.WIFI:
        return True
    name_l = iface.name.lower()
    fname_l = iface.friendly_name.lower()
    return (
        any(w in name_l for w in ("wlan", "wifi", "wlp"))
        or any(w in fname_l for w in ("wi-fi", "wifi", "wireless"))
        or iface.ssid is not None
    )


def get_ethernet_rank(iface: NetworkInterface, all_interfaces: List[NetworkInterface]) -> int:
    """
    Returns deterministic rank (0 for eth0 / primary, 1 for eth1 / secondary, etc.)
    among available Ethernet interfaces.
    """
    eths = sorted(
        [i for i in all_interfaces if is_ethernet_interface(i)],
        key=lambda i: (i.name.lower(), i.friendly_name.lower(), i.id),
    )
    for idx, e in enumerate(eths):
        if e.id == iface.id:
            return idx
    return 99


class PolicyEngine:
    """
    Evaluates candidate quality scores and determines authoritative failover decisions.
    Philosophy: "Switch when necessary, not because you can."

    Workload Awareness & Active Path Protection Rules (Zoom, OBS Studio, vMix):
    1. Online priority: Physical Ethernet is always prioritized over Wi-Fi.
    2. Case 5 (Normal): eth0, eth1, wifi healthy -> eth0 is selected as primary.
    3. Case 2: Only eth0 and wifi -> eth0 is prioritized as long as healthy.
    4. Case 3: eth0 degraded/ALERT/RTO -> immediately failover to eth1.
    5. Case 4: eth0 and eth1 both degraded/ALERT/RTO -> immediately failover to wifi.
    6. Active Workload Continuity: When an Ethernet path (eth0 or eth1) is ONLINE and HEALTHY,
       do not perform impulsive switching between healthy Ethernet paths for minor speed differences.
       When eth1 is active, maintain eth1 unless it experiences degradation/RTO/disconnect.
    """

    @classmethod
    def compute_score(
        cls,
        interface: NetworkInterface,
        config: PolicyConfig,
        profile: WorkloadProfile,
        all_interfaces: Optional[List[NetworkInterface]] = None,
    ) -> CandidateScore:
        """
        Calculate quality score (0.0 to 150.0+) for an interface path.
        Weighted according to workload profile requirements and media priority.
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

        # Preference bonus if explicitly configured
        preference_bonus = 5.0 if config.preferred_interface_id == interface.id else 0.0

        # Structural Media Priority Bonus:
        # Physical Ethernet receives +25.0 bonus over Wi-Fi
        if is_ethernet_interface(interface):
            preference_bonus += 25.0
            # Primary Ethernet (eth0 / rank 0) receives +5.0 baseline priority in normal state (Case 5)
            if all_interfaces:
                rank = get_ethernet_rank(interface, all_interfaces)
                if rank == 0:
                    preference_bonus += 5.0

        raw_total = latency_score + jitter_score - loss_penalty + preference_bonus
        total_score = max(0.0, min(150.0, raw_total))

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
                (cls.compute_score(i, config, profile, interfaces), i)
                for i in candidates
            ]
            scored.sort(key=lambda pair: pair[0].total_score, reverse=True)
            best_score, best_candidate = scored[0]

            if best_score.total_score > 0.0:
                reason = f"Active path disconnected/unusable - Emergency failover to {best_candidate.friendly_name}"
                return best_candidate.id, reason
            return None

        # 2. DEGRADED ACTIVE PATH: Active is in ALERT state (or experiencing packet loss / RTO)
        if active_iface.state == InterfaceState.ALERT or active_iface.metrics.packet_loss_pct >= config.packet_loss_alert_threshold_pct:
            ready_candidates = [i for i in interfaces if i.id != active_iface.id and i.state == InterfaceState.READY]
            if ready_candidates:
                scored = [
                    (cls.compute_score(i, config, profile, interfaces), i)
                    for i in ready_candidates
                ]
                scored.sort(key=lambda pair: pair[0].total_score, reverse=True)
                best_score, best_candidate = scored[0]

                active_score = cls.compute_score(active_iface, config, profile, interfaces)
                if best_score.total_score > active_score.total_score:
                    # Distinguish specific case in reason
                    if is_ethernet_interface(active_iface) and is_ethernet_interface(best_candidate):
                        reason = f"Active Ethernet {active_iface.friendly_name} degraded (ALERT/RTO) - Immediate switch to standby {best_candidate.friendly_name}"
                    elif is_ethernet_interface(active_iface) and is_wifi_interface(best_candidate):
                        reason = f"All Ethernet paths degraded/ALERT - Emergency failover to Wi-Fi {best_candidate.friendly_name}"
                    else:
                        reason = f"Active path degraded (ALERT) - Switch to healthy standby {best_candidate.friendly_name}"
                    return best_candidate.id, reason

        # 3. NORMAL OPERATION & WORKLOAD CONTINUITY PROTECTION (Zoom, vMix, OBS)
        # Active path is healthy (ONLINE, not ALERT, packet loss < threshold).
        active_score = cls.compute_score(active_iface, config, profile, interfaces)
        eligible_candidates = [
            i for i in interfaces
            if i.id != active_iface.id and i.state == InterfaceState.READY
        ]

        if not eligible_candidates:
            return None

        scored_candidates = [
            (cls.compute_score(i, config, profile, interfaces), i)
            for i in eligible_candidates
        ]
        scored_candidates.sort(key=lambda pair: pair[0].total_score, reverse=True)
        best_candidate_score, best_candidate = scored_candidates[0]

        # Case A: Active path is already Ethernet (eth0 or eth1)
        # WORKLOAD PROTECTION RULE:
        # If the active Ethernet is healthy and performing well, DO NOT switch between Ethernet paths
        # merely for small latency/throughput differences, preserving ongoing Zoom/vMix/OBS sessions.
        # "apabila terbaik eth1 kecuali network disconnected/rto kasih ganti prioritas ke terbaik misal dari eth1 ke eth0."
        if is_ethernet_interface(active_iface):
            # If candidate is Wi-Fi, Ethernet already wins with higher score.
            # If candidate is another Ethernet:
            if is_ethernet_interface(best_candidate):
                # Only switch if candidate exceeds active by a substantial takeover margin AND active is noticeably degraded
                required_score = active_score.total_score + max(config.takeover_margin, 20.0)
                if best_candidate_score.total_score >= required_score:
                    reason = (
                        f"Standby Ethernet {best_candidate.friendly_name} ({best_candidate_score.total_score:.1f}) "
                        f"significantly superior to active {active_iface.friendly_name} ({active_score.total_score:.1f})"
                    )
                    return best_candidate.id, reason
                # Otherwise, protect active session continuity!
                return None

        # Case B: Active path is Wi-Fi, and a physical Ethernet (eth0 or eth1) is restored and READY
        # Since Ethernet is inherently superior to Wi-Fi, promote healthy Ethernet back.
        if is_wifi_interface(active_iface) and is_ethernet_interface(best_candidate):
            required_score = active_score.total_score + config.takeover_margin
            if best_candidate_score.total_score >= required_score:
                reason = (
                    f"Physical Ethernet {best_candidate.friendly_name} restored and healthy "
                    f"- Reclaiming primary wire path from Wi-Fi {active_iface.friendly_name}"
                )
                return best_candidate.id, reason

        # General Anti-Flap Equation for other cases
        required_score = active_score.total_score + config.takeover_margin
        if best_candidate_score.total_score >= required_score:
            reason = (
                f"Candidate {best_candidate.friendly_name} score ({best_candidate_score.total_score:.1f}) "
                f"exceeds active ({active_score.total_score:.1f}) by takeover margin ({config.takeover_margin})"
            )
            return best_candidate.id, reason

        return None
