from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import time


class PriorityLevel(Enum):
    P1 = 1  # Primary (LAN 1)
    P2 = 2  # Secondary (LAN 2)
    P3 = 3  # Fallback (Wi-Fi)

    @property
    def label(self) -> str:
        if self == PriorityLevel.P1:
            return "Priority 1 (Primary LAN)"
        elif self == PriorityLevel.P2:
            return "Priority 2 (Secondary LAN)"
        else:
            return "Priority 3 (Fallback Wi-Fi)"

    @property
    def short_label(self) -> str:
        if self == PriorityLevel.P1:
            return "LAN 1"
        elif self == PriorityLevel.P2:
            return "LAN 2"
        else:
            return "Wi-Fi"


class InterfaceStatus(Enum):
    ONLINE = "ONLINE"
    STANDBY = "STANDBY"
    DEGRADED = "DEGRADED"
    RTO_FAILING = "RTO FAILING"
    DISCONNECTED = "DISCONNECTED"


class LogLevel(Enum):
    INFO = "INFO"
    WARNING = "WARN"
    FAILOVER = "FAILOVER"
    RECOVERY = "RECOVERY"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class SpeedtestProvider(Enum):
    CLOUDFLARE = "Cloudflare Speedtest"
    NPERF = "nPerf / Multi-CDN"
    FAST = "Fast.com (Netflix CDN)"
    OOKLA = "Ookla Speedtest"


@dataclass
class PingResult:
    success: bool
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    error: str = ""
    target: str = ""


@dataclass
class AdapterInfo:
    alias: str
    index: int = 0
    ipv4: str = ""
    gateway: str = ""
    is_connected: bool = False
    is_admin_enabled: bool = True
    metric: int = 0
    auto_metric: bool = True
    adapter_type: str = "Ethernet"  # Ethernet / Wireless / Unknown
    description: str = ""
    physical_media_type: str = ""
    is_physical: bool = True


@dataclass
class AdapterPortSummary:
    total_ethernet: int = 0
    total_wireless: int = 0
    connected_count: int = 0
    active_route_alias: str = ""


@dataclass
class TrafficStats:
    alias: str
    bytes_sent_sec: float = 0.0
    bytes_recv_sec: float = 0.0
    download_kbps: float = 0.0
    upload_kbps: float = 0.0
    jitter_ms: float = 0.0


@dataclass
class SpeedtestResult:
    alias: str
    ip: str
    provider: SpeedtestProvider
    ping_ms: float = 0.0
    jitter_ms: float = 0.0
    download_mbps: float = 0.0
    upload_mbps: float = 0.0
    loaded_latency_ms: float = 0.0
    packet_loss_pct: float = 0.0
    timestamp: str = ""
    success: bool = True
    error: str = ""
    server_location: str = ""
    isp_info: str = ""


@dataclass
class FailoverConfig:
    ping_target_primary: str = "1.1.1.1"
    ping_target_secondary: str = "8.8.8.8"
    ping_interval_sec: float = 1.0
    ping_timeout_ms: int = 800
    failover_rto_threshold: int = 2
    recovery_success_threshold: int = 5
    metric_p1_normal: int = 10
    metric_p2_normal: int = 20
    metric_p3_normal: int = 30
    metric_demoted: int = 50
    p1_alias: str = ""
    p2_alias: str = ""
    p3_alias: str = ""
    auto_start: bool = False
    theme_mode: str = "Dark"  # "Dark" or "Light"
    sound_enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "ping_target_primary": self.ping_target_primary,
            "ping_target_secondary": self.ping_target_secondary,
            "ping_interval_sec": self.ping_interval_sec,
            "ping_timeout_ms": self.ping_timeout_ms,
            "failover_rto_threshold": self.failover_rto_threshold,
            "recovery_success_threshold": self.recovery_success_threshold,
            "metric_p1_normal": self.metric_p1_normal,
            "metric_p2_normal": self.metric_p2_normal,
            "metric_p3_normal": self.metric_p3_normal,
            "metric_demoted": self.metric_demoted,
            "p1_alias": self.p1_alias,
            "p2_alias": self.p2_alias,
            "p3_alias": self.p3_alias,
            "auto_start": self.auto_start,
            "theme_mode": self.theme_mode,
            "sound_enabled": self.sound_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FailoverConfig":
        valid_keys = cls.__annotations__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class MonitoredInterfaceState:
    priority: PriorityLevel
    alias: str = ""
    ip: str = ""
    gateway: str = ""
    is_connected: bool = False
    is_admin_enabled: bool = True
    current_metric: int = 0
    assigned_metric: int = 0
    is_active_route: bool = False
    consecutive_rto: int = 0
    consecutive_success: int = 0
    last_latency_ms: float = 0.0
    jitter_ms: float = 0.0
    download_kbps: float = 0.0
    upload_kbps: float = 0.0
    latency_history: List[float] = field(default_factory=list)
    total_pings: int = 0
    total_lost: int = 0
    status: InterfaceStatus = InterfaceStatus.DISCONNECTED

    @property
    def packet_loss_pct(self) -> float:
        if self.total_pings == 0:
            return 0.0
        return (self.total_lost / self.total_pings) * 100.0


@dataclass
class LogEvent:
    timestamp: str
    level: LogLevel
    message: str
