import unittest
from core.models import FailoverConfig, PriorityLevel, InterfaceStatus, PingResult
from core.failover_engine import FailoverEngine


class TestFailoverEngine(unittest.TestCase):
    def setUp(self):
        self.config = FailoverConfig(
            p1_alias="LAN 1 (Ethernet 1)",
            p2_alias="LAN 2 (Ethernet 2)",
            p3_alias="Wi-Fi",
            failover_rto_threshold=2,
            recovery_success_threshold=5,
            metric_p1_normal=10,
            metric_p2_normal=20,
            metric_p3_normal=30,
            metric_demoted=50,
        )
        self.engine = FailoverEngine(config=self.config)
        self.engine.set_dry_run(True)

        # Mark all mock interfaces as connected with IPs
        self.engine.states[PriorityLevel.P1].is_connected = True
        self.engine.states[PriorityLevel.P1].ip = "192.168.10.101"

        self.engine.states[PriorityLevel.P2].is_connected = True
        self.engine.states[PriorityLevel.P2].ip = "192.168.20.102"

        self.engine.states[PriorityLevel.P3].is_connected = True
        self.engine.states[PriorityLevel.P3].ip = "192.168.1.181"

    def test_initial_normal_state(self):
        # All healthy ping
        results = {
            PriorityLevel.P1: PingResult(success=True, latency_ms=15.0),
            PriorityLevel.P2: PingResult(success=True, latency_ms=18.0),
            PriorityLevel.P3: PingResult(success=True, latency_ms=25.0),
        }
        self.engine._evaluate_health_and_failover(results)

        s1 = self.engine.states[PriorityLevel.P1]
        s2 = self.engine.states[PriorityLevel.P2]
        s3 = self.engine.states[PriorityLevel.P3]

        self.assertTrue(s1.is_active_route, "P1 should be active route")
        self.assertEqual(s1.assigned_metric, 10)
        self.assertEqual(s2.assigned_metric, 20)
        self.assertEqual(s3.assigned_metric, 30)
        self.assertEqual(s1.status, InterfaceStatus.ONLINE)
        self.assertEqual(s2.status, InterfaceStatus.STANDBY)

    def test_failover_on_two_consecutive_rtos(self):
        # Cycle 1: P1 fails once (not yet at threshold of 2)
        c1 = {
            PriorityLevel.P1: PingResult(success=False, error="RTO"),
            PriorityLevel.P2: PingResult(success=True, latency_ms=18.0),
            PriorityLevel.P3: PingResult(success=True, latency_ms=25.0),
        }
        self.engine._evaluate_health_and_failover(c1)
        # Still P1 active because threshold is 2
        self.assertTrue(self.engine.states[PriorityLevel.P1].is_active_route)

        # Cycle 2: P1 fails a second time (threshold reached!)
        c2 = {
            PriorityLevel.P1: PingResult(success=False, error="RTO"),
            PriorityLevel.P2: PingResult(success=True, latency_ms=18.0),
            PriorityLevel.P3: PingResult(success=True, latency_ms=25.0),
        }
        self.engine._evaluate_health_and_failover(c2)

        s1 = self.engine.states[PriorityLevel.P1]
        s2 = self.engine.states[PriorityLevel.P2]
        s3 = self.engine.states[PriorityLevel.P3]

        # Failover occurred: P2 is active!
        self.assertFalse(s1.is_active_route, "P1 should no longer be active")
        self.assertTrue(s2.is_active_route, "P2 must be promoted to active route")
        self.assertEqual(s2.assigned_metric, 10, "P2 should now have metric 10")
        self.assertEqual(s1.assigned_metric, 50, "P1 should be demoted to metric 50")
        self.assertEqual(s3.assigned_metric, 30, "P3 stays at standby metric 30")
        self.assertEqual(s1.status, InterfaceStatus.RTO_FAILING)
        self.assertEqual(s2.status, InterfaceStatus.ONLINE)

    def test_auto_recovery_after_five_successes(self):
        # First trigger failover to P2
        for _ in range(2):
            self.engine._evaluate_health_and_failover({
                PriorityLevel.P1: PingResult(success=False, error="RTO"),
                PriorityLevel.P2: PingResult(success=True, latency_ms=18.0),
                PriorityLevel.P3: PingResult(success=True, latency_ms=25.0),
            })
        self.assertTrue(self.engine.states[PriorityLevel.P2].is_active_route)

        # Now P1 comes back online: simulate 4 successes (recovery threshold is 5)
        for _ in range(4):
            self.engine._evaluate_health_and_failover({
                PriorityLevel.P1: PingResult(success=True, latency_ms=12.0),
                PriorityLevel.P2: PingResult(success=True, latency_ms=18.0),
                PriorityLevel.P3: PingResult(success=True, latency_ms=25.0),
            })
            # Still on P2 because not yet 5 consecutive successes
            self.assertTrue(self.engine.states[PriorityLevel.P2].is_active_route)

        # 5th success: auto-recovery triggers!
        self.engine._evaluate_health_and_failover({
            PriorityLevel.P1: PingResult(success=True, latency_ms=12.0),
            PriorityLevel.P2: PingResult(success=True, latency_ms=18.0),
            PriorityLevel.P3: PingResult(success=True, latency_ms=25.0),
        })

        s1 = self.engine.states[PriorityLevel.P1]
        s2 = self.engine.states[PriorityLevel.P2]
        s3 = self.engine.states[PriorityLevel.P3]

        self.assertTrue(s1.is_active_route, "P1 should be restored as active route")
        self.assertEqual(s1.assigned_metric, 10, "P1 restored to metric 10")
        self.assertEqual(s2.assigned_metric, 20, "P2 returned to standby metric 20")
        self.assertEqual(s3.assigned_metric, 30, "P3 at standby metric 30")


if __name__ == "__main__":
    unittest.main()

