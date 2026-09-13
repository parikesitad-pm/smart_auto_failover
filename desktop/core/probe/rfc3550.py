"""
AutoFailover 3.0 Core - RFC 3550 Interarrival Jitter Calculation
Author: parikesitad-pm
© 2026
"""

import time
import socket
from typing import Tuple, Optional


class RFC3550JitterTracker:
    """
    Implements RFC 3550 Section 6.4.1 interarrival jitter estimation:
    D(i-1, i) = (R_i - S_i) - (R_{i-1} - S_{i-1})
    J(i) = J(i-1) + (|D(i-1, i)| - J(i-1)) / 16
    """
    def __init__(self):
        self.jitter_ms: float = 0.0
        self.prev_transit: Optional[float] = None
        self.samples_count: int = 0

    def update(self, send_time: float, recv_time: float) -> float:
        """
        Record packet timestamps and compute smoothed RFC 3550 jitter in milliseconds.
        send_time and recv_time are in seconds (e.g. from time.monotonic()).
        """
        transit = (recv_time - send_time) * 1000.0  # ms
        self.samples_count += 1

        if self.prev_transit is None:
            self.prev_transit = transit
            return self.jitter_ms

        d = abs(transit - self.prev_transit)
        self.prev_transit = transit

        # Smoothing algorithm: J = J + (|D| - J) / 16
        self.jitter_ms += (d - self.jitter_ms) / 16.0
        return self.jitter_ms

    def reset(self) -> None:
        self.jitter_ms = 0.0
        self.prev_transit = None
        self.samples_count = 0


import struct


def probe_socket_rtt(target_host: str, target_port: int = 443, timeout_sec: float = 0.8, source_ip: Optional[str] = None) -> Tuple[bool, float]:
    """
    Perform a low-overhead socket connection to measure precise round-trip time.
    Configures SO_REUSEADDR and SO_LINGER (1, 0) to abort gracefully upon close,
    preventing TIME_WAIT socket exhaustion in the OS kernel TCP/IP stack.
    Returns (success: bool, rtt_ms: float).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_sec)

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Linger for 0 seconds: Discards pending data and sends TCP RST on close
        # Completely prevents socket accumulation in kernel TIME_WAIT state
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    except Exception:
        pass

    if source_ip and source_ip != "0.0.0.0" and source_ip != "N/A":
        try:
            sock.bind((source_ip, 0))
        except Exception:
            pass  # Fall back to default routing if interface binding is restricted

    start_time = time.monotonic()
    try:
        sock.connect((target_host, target_port))
        rtt_ms = (time.monotonic() - start_time) * 1000.0
        return True, rtt_ms
    except socket.timeout:
        return False, timeout_sec * 1000.0
    except Exception:
        return False, 0.0
    finally:
        try:
            sock.close()
        except Exception:
            pass
