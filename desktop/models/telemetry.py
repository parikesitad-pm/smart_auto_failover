"""
AutoFailover 3.0 Models - Device Telemetry
Author: parikesitad-pm
© 2026
"""

import time
from typing import Optional
from pydantic import BaseModel, Field


class DeviceHealth(BaseModel):
    """
    Contextual system telemetry (sampled passively at ~1 Hz).
    MUST NOT independently trigger network failover.
    """
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    ram_percent: float = 0.0
    gpu_percent: Optional[float] = None
    pressure: str = "nominal"  # nominal, moderate, critical
    timestamp: float = Field(default_factory=time.time)
