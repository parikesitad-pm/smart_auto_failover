"""
AutoFailover 3.0 Models - Policy Engine Configurations & Candidate Scoring
Author: parikesitad-pm
© 2026
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class WorkloadProfile(str, Enum):
    CONFERENCE = "conference"       # Real-time interactive (Zoom, Teams, Meet): Jitter & Loss prioritized
    BROADCAST = "broadcast"         # Outbound high-bitrate stream (OBS, vMix): Loss critical
    BALANCED = "balanced"           # General low-latency multi-purpose


class PolicyConfig(BaseModel):
    """
    Arbitration rules and thresholds.
    """
    takeover_margin: float = 12.0               # Candidate must exceed active by this margin to prevent flapping
    latency_alert_threshold_ms: float = 120.0   # Degradation threshold
    jitter_alert_threshold_ms: float = 18.0     # RFC 3550 jitter degradation threshold
    packet_loss_alert_threshold_pct: float = 3.0
    preferred_interface_id: Optional[str] = None
    recovery_cooldown_seconds: float = 5.0      # Stabilization hold before reclaim consideration
    workload_profile: WorkloadProfile = WorkloadProfile.CONFERENCE


class CandidateScore(BaseModel):
    """
    Mathematical path evaluation score broken down by components.
    """
    interface_id: str
    total_score: float = 0.0
    latency_score: float = 0.0
    jitter_score: float = 0.0
    loss_penalty: float = 0.0
    preference_bonus: float = 0.0
