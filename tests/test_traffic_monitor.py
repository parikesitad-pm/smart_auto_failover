import unittest
from core.traffic_monitor import TrafficMonitor


class TestTrafficMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = TrafficMonitor(history_len=10)

    def test_update_and_stats(self):
        stats = self.monitor.update()
        self.assertIsInstance(stats, dict)
        for alias, st in stats.items():
            self.assertGreaterEqual(st.download_kbps, 0.0)
            self.assertGreaterEqual(st.upload_kbps, 0.0)

    def test_jitter_calculation(self):
        # Consecutive samples: 20ms, 25ms, 18ms, 30ms
        j1 = self.monitor.record_latency_sample("eth0", 20.0)
        self.assertEqual(j1, 0.0)

        j2 = self.monitor.record_latency_sample("eth0", 25.0)
        self.assertGreater(j2, 0.0)

        j3 = self.monitor.record_latency_sample("eth0", 18.0)
        self.assertGreater(j3, 0.0)

        st = self.monitor.get_stats("eth0")
        self.assertGreater(st.jitter_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
