"""
AutoFailover 3.0 Core - Workload Process Watcher
Author: parikesitad-pm
© 2026
"""

import os
from typing import Set, Tuple
from ...models.policy import WorkloadProfile


class WorkloadWatcher:
    """
    Passively identifies active real-time workloads (Zoom, OBS, vMix, Teams, Meet)
    to inform PolicyEngine quality scoring.
    """

    KNOWN_CONFERENCE = {"zoom", "teams", "meet", "webex", "slack", "discord"}
    KNOWN_BROADCAST = {"obs", "obs64", "vmix", "vmix64", "wirecast", "streamlabs"}

    def detect_active_profile(self) -> Tuple[WorkloadProfile, Set[str]]:
        detected_apps: Set[str] = set()

        # Try psutil if available
        try:
            import psutil
            for proc in psutil.process_iter(["name"]):
                name = (proc.info["name"] or "").lower()
                for app in self.KNOWN_CONFERENCE | self.KNOWN_BROADCAST:
                    if app in name:
                        detected_apps.add(app)
        except Exception:
            # Fallback: scan Linux /proc for running process cmdlines
            detected_apps = self._scan_linux_proc()

        if any(app in self.KNOWN_BROADCAST for app in detected_apps):
            return WorkloadProfile.BROADCAST, detected_apps
        elif any(app in self.KNOWN_CONFERENCE for app in detected_apps):
            return WorkloadProfile.CONFERENCE, detected_apps

        return WorkloadProfile.BALANCED, detected_apps

    def _scan_linux_proc(self) -> Set[str]:
        found = set()
        try:
            for pid in os.listdir("/proc"):
                if not pid.isdigit():
                    continue
                cmdline_path = f"/proc/{pid}/comm"
                if os.path.exists(cmdline_path):
                    try:
                        with open(cmdline_path, "r") as f:
                            comm = f.read().strip().lower()
                            for app in self.KNOWN_CONFERENCE | self.KNOWN_BROADCAST:
                                if app in comm:
                                    found.add(app)
                    except Exception:
                        pass
        except Exception:
            pass
        return found

    def scan_active_processes(self) -> Set[str]:
        """Returns the set of recognized active real-time workload application names."""
        _, detected = self.detect_active_profile()
        return detected
