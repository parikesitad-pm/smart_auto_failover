"""
AutoFailover 3.0 Packaging Entrypoint
Author: parikesitad-pm
© 2026

This dedicated launcher is used by PyInstaller to package the application
while preserving desktop as a clean, proper Python package with valid package context.
"""

import sys
import os

# Ensure repository root is on sys.path if running unpackaged
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from desktop.main import main

if __name__ == "__main__":
    main()
