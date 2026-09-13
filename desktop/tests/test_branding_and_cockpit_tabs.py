"""
AutoFailover 3.0 Tests - Branding, Assets & Cockpit Information Architecture
Author: parikesitad-pm
© 2026
"""

import os
import unittest
from unittest.mock import MagicMock
from desktop.resources import get_asset_path
from desktop.models.interface import NetworkInterface, InterfaceState, InterfaceMediaType
from desktop.ui.dashboard.cockpit import get_health_rating


class TestBrandingAndCockpitIA(unittest.TestCase):
    """Verifies branding asset resolution and Cockpit IA behavior."""

    def test_cross_platform_assets_exist(self):
        """Ensures PNG, ICO, and ICNS assets resolve to real files."""
        png = get_asset_path("modula_3.0.png")
        ico = get_asset_path("modula_3.0.ico")
        icns = get_asset_path("modula_3.0.icns")

        self.assertTrue(os.path.isfile(png), f"PNG asset missing: {png}")
        self.assertTrue(os.path.isfile(ico), f"ICO asset missing: {ico}")
        self.assertTrue(os.path.isfile(icns), f"ICNS asset missing: {icns}")

    def test_health_rating_computation(self):
        """Verifies health rating tiers and disconnected handling."""
        r_disc, _ = get_health_rating(100, is_connected=False)
        self.assertEqual(r_disc, "NO CONNECTION")

        r_zero, _ = get_health_rating(0, is_connected=True)
        self.assertEqual(r_zero, "NO CONNECTION")

        r_crit, _ = get_health_rating(25, is_connected=True)
        self.assertEqual(r_crit, "CRITICAL")

        r_poor, _ = get_health_rating(45, is_connected=True)
        self.assertEqual(r_poor, "POOR")

        r_deg, _ = get_health_rating(65, is_connected=True)
        self.assertEqual(r_deg, "DEGRADED")

        r_healthy, _ = get_health_rating(80, is_connected=True)
        self.assertEqual(r_healthy, "HEALTHY")

        r_exc, _ = get_health_rating(95, is_connected=True)
        self.assertEqual(r_exc, "EXCELLENT")


if __name__ == "__main__":
    unittest.main()
