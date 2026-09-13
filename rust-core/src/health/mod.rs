use crate::models::{InterfaceState, PathMetrics, PolicyConfig};

pub struct HealthEngine;

impl HealthEngine {
    /// Calculate composite 0–100 Network Health Index.
    /// Factors latency (weight: 35%), jitter (weight: 35%), and loss (weight: 30%).
    pub fn calculate_health_index(metrics: &PathMetrics) -> u32 {
        if metrics.packet_loss_pct >= 100.0 {
            return 0;
        }

        // Latency penalty: 0ms -> 100, 150ms+ -> 0
        let lat_score = (1.0 - (metrics.latency_ms / 150.0).clamp(0.0, 1.0)) * 100.0;

        // Jitter penalty: 0ms -> 100, 30ms+ -> 0
        let jit_score = (1.0 - (metrics.jitter_ms / 30.0).clamp(0.0, 1.0)) * 100.0;

        // Loss penalty: 0% -> 100, 10%+ -> 0
        let loss_score = (1.0 - (metrics.packet_loss_pct / 10.0).clamp(0.0, 1.0)) * 100.0;

        let composite = (lat_score * 0.35) + (jit_score * 0.35) + (loss_score * 0.30);
        composite.round().clamp(0.0, 100.0) as u32
    }

    /// Assess interface state transitions based on updated metrics and policy configuration.
    /// Note: Does NOT promote to ONLINE; only determines if degraded (ALERT) or stable (READY).
    pub fn evaluate_state(
        current_state: InterfaceState,
        metrics: &PathMetrics,
        config: &PolicyConfig,
        carrier_detected: bool,
    ) -> InterfaceState {
        // Administrative disabled takes precedence
        if current_state == InterfaceState::Disabled {
            return InterfaceState::Disabled;
        }

        // Hard link loss
        if !carrier_detected || metrics.packet_loss_pct >= 100.0 {
            return InterfaceState::Offline;
        }

        // Degradation check
        let is_degraded = metrics.latency_ms >= config.latency_alert_threshold_ms
            || metrics.jitter_ms >= config.jitter_alert_threshold_ms
            || metrics.packet_loss_pct >= config.packet_loss_alert_threshold_pct;

        match current_state {
            InterfaceState::Online => {
                if is_degraded {
                    InterfaceState::Alert
                } else {
                    InterfaceState::Online
                }
            }
            InterfaceState::Alert => {
                if is_degraded {
                    InterfaceState::Alert
                } else {
                    InterfaceState::Ready
                }
            }
            InterfaceState::Offline => {
                if is_degraded {
                    InterfaceState::Alert
                } else {
                    InterfaceState::Ready
                }
            }
            InterfaceState::Ready => {
                if is_degraded {
                    InterfaceState::Alert
                } else {
                    InterfaceState::Ready
                }
            }
            InterfaceState::Disabled => InterfaceState::Disabled,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_perfect_health_index() {
        let metrics = PathMetrics {
            latency_ms: 5.0,
            jitter_ms: 1.0,
            packet_loss_pct: 0.0,
            ..Default::default()
        };
        let index = HealthEngine::calculate_health_index(&metrics);
        assert!(index >= 95);
    }

    #[test]
    fn test_degraded_health_state() {
        let config = PolicyConfig::default();
        let degraded_metrics = PathMetrics {
            latency_ms: 120.0, // Exceeds 85ms
            jitter_ms: 2.0,
            packet_loss_pct: 0.0,
            ..Default::default()
        };
        let state = HealthEngine::evaluate_state(InterfaceState::Ready, &degraded_metrics, &config, true);
        assert_eq!(state, InterfaceState::Alert);
    }
}
