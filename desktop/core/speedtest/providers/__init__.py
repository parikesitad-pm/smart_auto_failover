"""
AutoFailover 3.0 Core - Speed Test Provider Exports
Author: parikesitad-pm
© 2026
"""

from .base import BaseSpeedTestProvider, SpeedTestResult
from .cloudflare import CloudflareSpeedTestProvider
from .fast import FastSpeedTestProvider
from .ookla import OoklaSpeedTestProvider
from .nperf import NPerfSpeedTestProvider

__all__ = [
    "BaseSpeedTestProvider",
    "SpeedTestResult",
    "CloudflareSpeedTestProvider",
    "FastSpeedTestProvider",
    "OoklaSpeedTestProvider",
    "NPerfSpeedTestProvider",
]
