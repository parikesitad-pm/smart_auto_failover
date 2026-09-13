"""
AutoFailover 3.0 - Speedtest Runner Characterization Tests
Author: parikesitad-pm
© 2026
"""

import unittest
from desktop.core.speedtest import (
    SpeedtestRunner,
    SpeedtestResult,
    SpeedtestProvider,
    SpeedTestRunner,
    SpeedTestResult,
)


class TestSpeedtestRunner(unittest.TestCase):
    def test_canonical_export_parity(self):
        """Verify SpeedtestRunner and SpeedTestRunner refer to the same class."""
        self.assertIs(SpeedtestRunner, SpeedTestRunner)
        self.assertIs(SpeedtestResult, SpeedTestResult)

    def test_speedtest_result_latency_contract(self):
        """Verify latency_ms and ping_ms are present on SpeedtestResult."""
        res = SpeedtestResult(
            test_id="test_001",
            provider=SpeedtestProvider.CLOUDFLARE,
            interface_id="eth0",
            ping_ms=12.5,
            latency_ms=12.5,
            download_mbps=85.2,
            upload_mbps=42.1,
            success=True,
        )
        self.assertEqual(res.ping_ms, 12.5)
        self.assertEqual(res.latency_ms, 12.5)
        self.assertEqual(res.download_mbps, 85.2)

    def test_runner_single_test_method(self):
        """Verify run_single_test executes and returns valid SpeedtestResult."""
        runner = SpeedtestRunner()
        res = runner.run_single_test("ookla", interface_id="eth0")
        self.assertIsInstance(res, SpeedtestResult)
        self.assertEqual(res.provider, SpeedtestProvider.OOKLA)

    def test_runner_bulk_tests_method(self):
        """Verify run_bulk_tests returns list across all 4 providers."""
        runner = SpeedtestRunner()
        results = runner.run_bulk_tests(interface_id="wlan0")
        self.assertEqual(len(results), 4)
        providers = [r.provider for r in results]
        self.assertIn(SpeedtestProvider.CLOUDFLARE, providers)
        self.assertIn(SpeedtestProvider.OOKLA, providers)
        self.assertIn(SpeedtestProvider.FAST, providers)
        self.assertIn(SpeedtestProvider.NPERF, providers)


if __name__ == "__main__":
    unittest.main()
