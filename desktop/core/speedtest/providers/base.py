"""
AutoFailover 3.0 Core - Speed Test Provider Base & Result Model
Author: parikesitad-pm
© 2026
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field


class SpeedTestResult(BaseModel):
    """
    Common normalized speed test result across all providers.
    On-demand benchmarking only; never directly alters failover scoring.
    """
    provider: str
    interface: str = "default"
    download_mbps: float = 0.0
    upload_mbps: float = 0.0
    ping_ms: float = 0.0
    jitter_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)
    duration: float = 0.0
    status: str = "QUEUED"  # SUCCESS, FAILED, UNAVAILABLE, RUNNING, QUEUED, CANCELLED
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Backward compatibility aliases
    test_id: str = Field(default_factory=lambda: f"st_{int(time.time() * 1000)}")

    @property
    def latency_ms(self) -> float:
        return self.ping_ms

    @property
    def interface_id(self) -> str:
        return self.interface

    @property
    def success(self) -> bool:
        return self.status == "SUCCESS"


class BaseSpeedTestProvider(ABC):
    """Abstract base adapter for isolated speed test providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identification name."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """User-facing brand name."""
        pass

    @abstractmethod
    def run_benchmark(
        self,
        interface: str = "default",
        source_ip: Optional[str] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> SpeedTestResult:
        """Executes on-demand benchmark and returns normalized SpeedTestResult."""
        pass
