"""
Unit tests for MODULA - Smart Auto Failover v2.2 additions:
- SoundEngine (cross-platform audio synthesizer & notifications)
- BandwidthQoSManager (process scanner, priority scheduling & NetQoS)
- SystemTelemetry (Fastfetch hardware diagnostic & CCleaner junk scan)
- FailoverConfig v2.2 compatibility
"""
import unittest

from core.bandwidth_qos import BandwidthQoSManager
from core.models import FailoverConfig
from core.sound_engine import SoundEngine, SoundType
from core.system_telemetry import SystemTelemetry


class TestSoundEngine(unittest.TestCase):
    def setUp(self):
        SoundEngine.set_enabled(True)

    def test_sound_engine_enable_disable(self):
        self.assertTrue(SoundEngine.is_enabled())
        SoundEngine.set_enabled(False)
        self.assertFalse(SoundEngine.is_enabled())
        SoundEngine.set_enabled(True)
        self.assertTrue(SoundEngine.is_enabled())

    def test_sound_engine_play_all_types(self):
        # Ensure playing sounds does not raise any exceptions
        types = [
            SoundType.CONNECT,
            SoundType.DISCONNECT,
            SoundType.FAILOVER,
            SoundType.ACTION,
            SoundType.SUCCESS,
            SoundType.QOS_APPLIED,
            SoundType.CLEAN_COMPLETE,
        ]
        # In test environment, mute to prevent actual beep noise during test runs
        SoundEngine.set_enabled(False)
        for st in types:
            try:
                SoundEngine.play(st)
            except Exception as e:
                self.fail(f"SoundEngine.play({st}) raised exception: {e}")

        # Enable back and test with mock/non-blocking
        SoundEngine.set_enabled(True)
        for st in types:
            try:
                SoundEngine.play(st)
            except Exception as e:
                self.fail(f"SoundEngine.play({st}) raised exception when enabled: {e}")


class TestBandwidthQoS(unittest.TestCase):
    def test_scan_active_media_apps(self):
        apps = BandwidthQoSManager.get_active_media_apps()
        self.assertIsInstance(apps, list)
        for app in apps:
            self.assertTrue(hasattr(app, "name"))
            self.assertTrue(hasattr(app, "allocated_pct"))
            self.assertTrue(hasattr(app, "friendly_name"))
            self.assertGreaterEqual(app.allocated_pct, 0.0)

    def test_apply_allocation_dry(self):
        allocations = {
            "Zoom.exe": 70.0,
            "obs64.exe": 20.0,
            "spotify.exe": 10.0,
        }
        ok, msg = BandwidthQoSManager.apply_qos_policy(allocations)
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)


class TestSystemTelemetry(unittest.TestCase):
    def test_get_hardware_specs(self):
        specs = SystemTelemetry.get_hardware_specs()
        self.assertIsNotNone(specs.os_name)
        self.assertIsNotNone(specs.cpu_name)
        self.assertGreater(specs.cpu_cores, 0)
        self.assertGreater(specs.ram_total_gb, 0)
        self.assertIsNotNone(specs.gpu_integrated)
        self.assertIsNotNone(specs.gpu_discrete)
        self.assertIsInstance(specs.disks, list)

    def test_get_live_metrics(self):
        metrics = SystemTelemetry.get_live_metrics()
        self.assertGreaterEqual(metrics.cpu_percent, 0.0)
        self.assertGreater(metrics.ram_total_gb, 0.0)
        self.assertGreater(metrics.ram_percent, 0.0)

    def test_scan_junk(self):
        items, size_bytes = SystemTelemetry.scan_junk()
        self.assertIsInstance(items, list)
        self.assertGreaterEqual(size_bytes, 0)


class TestFailoverConfigV22(unittest.TestCase):
    def test_config_sound_enabled(self):
        cfg = FailoverConfig()
        self.assertTrue(hasattr(cfg, "sound_enabled"))
        self.assertTrue(cfg.sound_enabled)

        # Test dict round-trip
        d = cfg.to_dict()
        self.assertIn("sound_enabled", d)
        self.assertTrue(d["sound_enabled"])

        d["sound_enabled"] = False
        loaded = FailoverConfig.from_dict(d)
        self.assertFalse(loaded.sound_enabled)


if __name__ == "__main__":
    unittest.main()
