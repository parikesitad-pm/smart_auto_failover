import sys
from .base import PlatformBackend


def get_platform_backend() -> PlatformBackend:
    """Returns native backend for current operating system."""
    if sys.platform.startswith("linux"):
        from .linux.backend import LinuxPlatformBackend
        return LinuxPlatformBackend()
    elif sys.platform == "win32":
        from .windows.backend import WindowsPlatformBackend
        return WindowsPlatformBackend()
    elif sys.platform == "darwin":
        from .macos.backend import MacOSPlatformBackend
        return MacOSPlatformBackend()
    else:
        from .linux.backend import LinuxPlatformBackend
        return LinuxPlatformBackend()


__all__ = ["PlatformBackend", "get_platform_backend"]
