"""
AutoFailover 3.0 Centralized Resource Resolver
Author: parikesitad-pm
© 2026

Provides centralized asset discovery across development mode and PyInstaller
frozen environments without depending on the current working directory.
"""

import os
import sys


def get_base_dir() -> str:
    """
    Returns the root directory for resolving application assets across
    development source tree and PyInstaller frozen runtime.
    """
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return sys._MEIPASS
        return os.path.dirname(os.path.abspath(sys.executable))

    # Development mode: resolve to repository root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)


def get_asset_path(filename: str) -> str:
    """
    Resolves the absolute path to a bundled asset file (e.g. 'modula_3.0.png').
    Checks multiple expected bundle and package locations.
    """
    base = get_base_dir()
    current_dir = os.path.dirname(os.path.abspath(__file__))

    candidates = [
        os.path.join(base, "desktop", "assets", filename),
        os.path.join(base, "assets", filename),
        os.path.join(current_dir, "assets", filename),
        os.path.join(base, filename),
    ]

    for path in candidates:
        if os.path.isfile(path):
            return path

    # Fallback to standard package assets directory
    return os.path.join(current_dir, "assets", filename)
