"""
AutoFailover 3.0 Core - Speedtest Package Public API
Author: parikesitad-pm
© 2026
"""

from .providers.base import SpeedTestResult, BaseSpeedTestProvider
from .runner import (
    SpeedtestRunner,
    SpeedTestRunner,
    SpeedtestResult,
    SpeedtestProvider,
    SpeedTestProvider,
    SpeedtestMode,
    SpeedTestMode,
)

__all__ = [
    "SpeedtestRunner",
    "SpeedTestRunner",
    "SpeedtestResult",
    "SpeedTestResult",
    "BaseSpeedTestProvider",
    "SpeedtestProvider",
    "SpeedTestProvider",
    "SpeedtestMode",
    "SpeedTestMode",
]
