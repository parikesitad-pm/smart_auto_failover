import platform
from typing import List, Optional, Tuple

from core.models import AdapterInfo
from core.backends.base_backend import BaseNetworkBackend
from core.backends.windows_backend import WindowsBackend
from core.backends.macos_backend import MacOSBackend


class NetworkManager:
    """
    Cross-platform facade that automatically delegates network operations
    to the appropriate OS backend (Windows or macOS).
    """

    _backend: Optional[BaseNetworkBackend] = None

    @classmethod
    def get_backend(cls) -> BaseNetworkBackend:
        if cls._backend is None:
            system = platform.system()
            if system == "Windows":
                cls._backend = WindowsBackend()
            elif system == "Darwin":
                cls._backend = MacOSBackend()
            else:
                # Default fallback
                cls._backend = WindowsBackend()
        return cls._backend

    @classmethod
    def get_os_name(cls) -> str:
        s = platform.system()
        if s == "Darwin":
            return "macOS"
        elif s == "Windows":
            return "Windows"
        return s

    @classmethod
    def is_admin(cls) -> bool:
        return cls.get_backend().is_admin()

    @classmethod
    def request_elevation(cls) -> bool:
        return cls.get_backend().request_elevation()

    @classmethod
    def get_all_adapters(cls) -> List[AdapterInfo]:
        return cls.get_backend().get_all_adapters()

    @classmethod
    def set_interface_metric(cls, alias: str, metric: int) -> Tuple[bool, str]:
        return cls.get_backend().set_interface_metric(alias, metric)

    @classmethod
    def set_network_priority_order(cls, ordered_aliases: List[str]) -> Tuple[bool, str]:
        return cls.get_backend().set_network_priority_order(ordered_aliases)

    @classmethod
    def restore_automatic_metric(cls, alias: str) -> Tuple[bool, str]:
        results = cls.get_backend().restore_defaults([alias])
        if results:
            return results[0][1], results[0][2]
        return True, "Restored"

    @classmethod
    def restore_all_automatic_metrics(cls, aliases: List[str]) -> List[Tuple[str, bool, str]]:
        return cls.get_backend().restore_defaults(aliases)
