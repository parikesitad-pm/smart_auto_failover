import unittest
from core.models import SpeedtestProvider
from core.speedtest_engine import SpeedtestManager, CloudflareSpeedtestRunner


class TestSpeedtestEngine(unittest.TestCase):
    def test_invalid_ip_handling(self):
        runner = CloudflareSpeedtestRunner()
        res = runner.run("Dummy", "169.254.1.1")
        self.assertFalse(res.success)
        self.assertIn("Invalid", res.error)

    def test_provider_registry(self):
        self.assertIn(SpeedtestProvider.CLOUDFLARE, SpeedtestManager.RUNNERS)
        self.assertIn(SpeedtestProvider.NPERF, SpeedtestManager.RUNNERS)
        self.assertIn(SpeedtestProvider.OOKLA, SpeedtestManager.RUNNERS)


if __name__ == "__main__":
    unittest.main()
