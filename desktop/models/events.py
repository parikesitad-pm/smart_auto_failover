"""
AutoFailover 3.0 Models - Meaningful Event Types
Author: parikesitad-pm
© 2026
"""

import time
import uuid
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EventType(str, Enum):
    INTERFACE_DISCOVERED = "INTERFACE_DISCOVERED"
    CARRIER_CONNECTED = "CARRIER_CONNECTED"
    CARRIER_DISCONNECTED = "CARRIER_DISCONNECTED"
    ADMIN_ENABLED = "ADMIN_ENABLED"
    ADMIN_DISABLED = "ADMIN_DISABLED"
    STATE_TRANSITION = "STATE_TRANSITION"
    HEALTH_DEGRADED = "HEALTH_DEGRADED"
    FAILOVER_TRIGGERED = "FAILOVER_TRIGGERED"
    RECOVERY_STABILIZED = "RECOVERY_STABILIZED"
    ROUTE_SWITCHED = "ROUTE_SWITCHED"
    ZERO_CONNECTION = "ZERO_CONNECTION"


class FailoverEvent(BaseModel):
    """
    Meaningful runtime event. Persisted to ring buffer / log.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = Field(default_factory=time.time)
    event_type: EventType
    interface_id: Optional[str] = None
    interface_name: Optional[str] = None
    message: str
    severity: str = "INFO"
    details: Dict[str, Any] = Field(default_factory=dict)
