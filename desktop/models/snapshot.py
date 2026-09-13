"""
AutoFailover 3.0 Models - Runtime Snapshot
Author: parikesitad-pm
© 2026
"""

import time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .interface import NetworkInterface
from .telemetry import DeviceHealth


class RuntimeSnapshot(BaseModel):
    """
    Immutable thread-safe snapshot of the complete AutoFailover runtime.
    Produced exclusively by the background engine; consumed read-only by the UI thread.
    Guarantees zero blocking of the Tkinter event loop.
    """
    interfaces: List[NetworkInterface] = Field(default_factory=list)
    active_interface_id: Optional[str] = None
    active_interface: Optional[NetworkInterface] = None
    standby_interface: Optional[NetworkInterface] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    device_health: Optional[DeviceHealth] = None
    workload_apps: List[str] = Field(default_factory=list)
    workload_profile: str = "BALANCED"
    engine_status: str = "NO ELIGIBLE PATH"
    engine_subtext: str = "Waiting for usable interface"
    takeover_margin: float = 15.0
    subprocess_count_per_min: int = 0
    discovery_duration_ms: float = 0.0
    ui_refresh_duration_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)
