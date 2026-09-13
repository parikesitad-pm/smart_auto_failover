use crate::models::{
    CandidateScore, InterfaceState, NetworkInterface, PolicyConfig, WorkloadProfile,
};

pub struct PolicyEngine;

impl PolicyEngine {
    /// Calculate candidate path quality score (0.0 - 100.0+).
    /// Weighted according to workload profile requirements.
    pub fn compute_score(
        interface: &NetworkInterface,
        config: &PolicyConfig,
        profile: WorkloadProfile,
    ) -> CandidateScore {
        if !interface.state.is_eligible_candidate() && interface.state != InterfaceState::Online {
            return CandidateScore {
                interface_id: interface.id.clone(),
                total_score: 0.0,
                latency_score: 0.0,
                jitter_score: 0.0,
                loss_penalty: 0.0,
                preference_bonus: 0.0,
            };
        }

        let m = &interface.metrics;

        // Weights adapted to workload profile
        let (lat_w, jit_w, loss_w) = match profile {
            WorkloadProfile::VideoConference => (30.0, 35.0, 35.0),
            WorkloadProfile::LiveProduction => (20.0, 25.0, 55.0), // Loss is critical for broadcast
            WorkloadProfile::General | WorkloadProfile::Custom => (35.0, 35.0, 30.0),
        };

        // Latency component (0ms -> full, 200ms -> 0)
        let latency_score = (1.0 - (m.latency_ms / 200.0).clamp(0.0, 1.0)) * lat_w;

        // Jitter component (0ms -> full, 25ms -> 0)
        let jitter_score = (1.0 - (m.jitter_ms / 25.0).clamp(0.0, 1.0)) * jit_w;

        // Loss penalty: severe linear/exponential penalty
        let loss_penalty = (m.packet_loss_pct / 10.0).clamp(0.0, 1.0) * loss_w;

        // Small bonus for preferred interface if defined
        let preference_bonus = if config
            .preferred_interface_id
            .as_ref()
            .map(|id| id == &interface.id)
            .unwrap_or(false)
        {
            5.0
        } else {
            0.0
        };

        let raw_total = latency_score + jitter_score - loss_penalty + preference_bonus;
        let total_score = raw_total.clamp(0.0, 120.0);

        CandidateScore {
            interface_id: interface.id.clone(),
            total_score,
            latency_score,
            jitter_score,
            loss_penalty,
            preference_bonus,
        }
    }

    /// Evaluate if failover switch is required.
    /// Returns Some(target_interface_id, reason) if switch should occur, or None if current path remains.
    pub fn evaluate_failover(
        interfaces: &[NetworkInterface],
        active_id: Option<&str>,
        config: &PolicyConfig,
        profile: WorkloadProfile,
    ) -> Option<(String, String)> {
        // Find active interface
        let active_iface = interfaces.iter().find(|i| {
            active_id
                .map(|id| i.id == id)
                .unwrap_or(i.state == InterfaceState::Online)
        });

        // Eligible candidates: must be READY or healthy ALERT, with carrier
        let mut scored_candidates: Vec<(&NetworkInterface, CandidateScore)> = interfaces
            .iter()
            .filter(|i| {
                // Must not be the active interface
                active_iface.map(|a| a.id != i.id).unwrap_or(true)
                    && i.state.is_eligible_candidate()
                    && i.carrier_detected
                    && i.is_admin_enabled
            })
            .map(|i| (i, Self::compute_score(i, config, profile)))
            .collect();

        // Sort candidates descending by score
        scored_candidates.sort_by(|a, b| {
            b.1.total_score
                .partial_cmp(&a.1.total_score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        let best_candidate = scored_candidates.first();

        // Case 1: Active path is missing or offline/unusable
        // In this case, takeover_margin DOES NOT apply per Master Prompt §10
        let active_is_unusable = match active_iface {
            None => true,
            Some(a) => {
                a.state == InterfaceState::Offline
                    || a.state == InterfaceState::Disabled
                    || !a.is_admin_enabled
                    || !a.carrier_detected
                    || a.metrics.packet_loss_pct >= 100.0
            }
        };

        if active_is_unusable {
            if let Some((candidate, score)) = best_candidate {
                return Some((
                    candidate.id.clone(),
                    format!(
                        "Immediate takeover: active path is unusable/offline. Selected candidate score: {:.1}",
                        score.total_score
                    ),
                ));
            } else {
                return None; // No eligible candidates available
            }
        }

        // Case 2: Active path is present. Check candidate against takeover margin.
        // candidate_score >= active_score + takeover_margin
        let active = active_iface.unwrap();
        let active_score = Self::compute_score(active, config, profile);

        if let Some((candidate, candidate_score)) = best_candidate {
            let required_score = active_score.total_score + config.takeover_margin;
            if candidate_score.total_score >= required_score {
                return Some((
                    candidate.id.clone(),
                    format!(
                        "Policy takeover: candidate '{}' score ({:.1}) beats active '{}' score ({:.1}) by margin ({:.1})",
                        candidate.id, candidate_score.total_score, active.id, active_score.total_score, config.takeover_margin
                    ),
                ));
            }
        }

        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::{InterfaceKind, PathMetrics};

    fn make_test_iface(id: &str, state: InterfaceState, lat: f64, jit: f64, loss: f64) -> NetworkInterface {
        NetworkInterface {
            id: id.to_string(),
            name: id.to_string(),
            kind: InterfaceKind::Ethernet,
            mac: None,
            ip_addresses: vec!["192.168.1.100".to_string()],
            gateway: Some("192.168.1.1".to_string()),
            state,
            metrics: PathMetrics {
                latency_ms: lat,
                jitter_ms: jit,
                packet_loss_pct: loss,
                ..Default::default()
            },
            is_admin_enabled: true,
            is_physical: true,
            carrier_detected: true,
            metric_priority: 100,
            ssid: None,
            netmask: None,
            link_speed: None,
        }
    }

    #[test]
    fn test_no_switch_for_tiny_performance_delta() {
        let config = PolicyConfig {
            takeover_margin: 15.0,
            ..Default::default()
        };
        let active = make_test_iface("eth0", InterfaceState::Online, 20.0, 2.0, 0.0);
        let candidate = make_test_iface("eth1", InterfaceState::Ready, 18.0, 1.8, 0.0); // Slightly better, but within margin

        let interfaces = vec![active, candidate];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("eth0"),
            &config,
            WorkloadProfile::VideoConference,
        );

        // Anti-flap margin prevents unnecessary switch
        assert!(decision.is_none());
    }

    #[test]
    fn test_immediate_switch_when_active_becomes_offline() {
        let config = PolicyConfig {
            takeover_margin: 15.0,
            ..Default::default()
        };
        let mut active = make_test_iface("eth0", InterfaceState::Offline, 0.0, 0.0, 100.0);
        active.carrier_detected = false;

        let candidate = make_test_iface("wlan0", InterfaceState::Ready, 25.0, 3.0, 0.0);

        let interfaces = vec![active, candidate];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("eth0"),
            &config,
            WorkloadProfile::VideoConference,
        );

        assert!(decision.is_some());
        let (target, reason) = decision.unwrap();
        assert_eq!(target, "wlan0");
        assert!(reason.contains("Immediate takeover"));
    }

    #[test]
    fn test_takeover_when_margin_exceeded() {
        let config = PolicyConfig {
            takeover_margin: 15.0,
            ..Default::default()
        };
        // Active degraded significantly
        let active = make_test_iface("eth0", InterfaceState::Alert, 120.0, 18.0, 4.0);
        // Candidate is pristine
        let candidate = make_test_iface("eth1", InterfaceState::Ready, 10.0, 1.0, 0.0);

        let interfaces = vec![active, candidate];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("eth0"),
            &config,
            WorkloadProfile::VideoConference,
        );

        assert!(decision.is_some());
        assert_eq!(decision.unwrap().0, "eth1");
    }

    #[test]
    fn test_recovered_preferred_path_does_not_hijack_without_margin() {
        let config = PolicyConfig {
            takeover_margin: 15.0,
            preferred_interface_id: Some("eth0".to_string()),
            ..Default::default()
        };
        // Active is currently wlan0 and healthy
        let active = make_test_iface("wlan0", InterfaceState::Online, 15.0, 2.0, 0.0);
        // eth0 just recovered into READY with similar performance
        let eth0 = make_test_iface("eth0", InterfaceState::Ready, 14.0, 2.0, 0.0);

        let interfaces = vec![active, eth0];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("wlan0"),
            &config,
            WorkloadProfile::VideoConference,
        );

        // Does NOT hijack active connection
        assert!(decision.is_none());
    }

    #[test]
    fn test_scenario_1_active_path_healthy_no_switch() {
        let config = PolicyConfig::default();
        let active = make_test_iface("eth0", InterfaceState::Online, 10.0, 1.0, 0.0);
        let candidate = make_test_iface("wifi", InterfaceState::Ready, 35.0, 4.0, 0.0);

        let interfaces = vec![active, candidate];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("eth0"),
            &config,
            WorkloadProfile::VideoConference,
        );
        assert!(decision.is_none());
    }

    #[test]
    fn test_scenario_6_recovered_preferred_path_reclaims_when_margin_exceeded() {
        let config = PolicyConfig {
            takeover_margin: 15.0,
            preferred_interface_id: Some("eth0".to_string()),
            ..Default::default()
        };
        // Active is cellular on high latency/jitter
        let active = make_test_iface("cell", InterfaceState::Online, 90.0, 15.0, 2.0);
        // Preferred eth0 recovered with pristine fiber latency
        let eth0 = make_test_iface("eth0", InterfaceState::Ready, 5.0, 0.5, 0.0);

        let interfaces = vec![active, eth0];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("cell"),
            &config,
            WorkloadProfile::VideoConference,
        );

        assert!(decision.is_some());
        let (target, reason) = decision.unwrap();
        assert_eq!(target, "eth0");
        assert!(reason.contains("Policy takeover"));
    }

    #[test]
    fn test_scenario_7_disabled_adapter_never_selected() {
        let config = PolicyConfig::default();
        let mut active = make_test_iface("eth0", InterfaceState::Offline, 0.0, 0.0, 100.0);
        active.carrier_detected = false;

        // Disabled adapter has pristine metrics but is administratively disabled
        let mut disabled = make_test_iface("eth1", InterfaceState::Disabled, 2.0, 0.2, 0.0);
        disabled.is_admin_enabled = false;

        // Ready secondary has higher latency but is enabled
        let secondary = make_test_iface("wifi", InterfaceState::Ready, 30.0, 3.0, 0.0);

        let interfaces = vec![active, disabled, secondary];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("eth0"),
            &config,
            WorkloadProfile::VideoConference,
        );

        assert!(decision.is_some());
        let (target, _) = decision.unwrap();
        // Disabled eth1 must NEVER be selected; wifi is chosen
        assert_eq!(target, "wifi");
    }

    #[test]
    fn test_scenario_8_new_interface_available_only_after_evaluation() {
        let config = PolicyConfig::default();
        let active = make_test_iface("eth0", InterfaceState::Online, 12.0, 1.2, 0.0);
        // Newly admitted interface is in candidate pool as READY
        let new_dev = make_test_iface("dock0", InterfaceState::Ready, 10.0, 1.0, 0.0);

        let interfaces = vec![active, new_dev];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("eth0"),
            &config,
            WorkloadProfile::VideoConference,
        );

        // Does not hijack healthy active connection without beating takeover margin
        assert!(decision.is_none());
    }

    #[test]
    fn test_scenario_9_active_interface_disappears_triggers_failover() {
        let config = PolicyConfig::default();
        // Active interface is absent from discovered interface list (e.g. unplugged USB adapter)
        let fallback = make_test_iface("wifi", InterfaceState::Ready, 25.0, 2.5, 0.0);

        let interfaces = vec![fallback];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("unplugged_usb"),
            &config,
            WorkloadProfile::VideoConference,
        );

        assert!(decision.is_some());
        assert_eq!(decision.unwrap().0, "wifi");
    }

    #[test]
    fn test_scenario_10_multiple_simultaneous_failures_selects_best_remaining() {
        let config = PolicyConfig::default();
        let mut eth0 = make_test_iface("eth0", InterfaceState::Offline, 0.0, 0.0, 100.0);
        eth0.carrier_detected = false;

        let mut eth1 = make_test_iface("eth1", InterfaceState::Offline, 0.0, 0.0, 100.0);
        eth1.carrier_detected = false;

        let wifi_weak = make_test_iface("wifi", InterfaceState::Alert, 80.0, 12.0, 3.0);
        let cell_good = make_test_iface("cell", InterfaceState::Ready, 40.0, 4.0, 0.0);

        let interfaces = vec![eth0, eth1, wifi_weak, cell_good];
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("eth0"),
            &config,
            WorkloadProfile::VideoConference,
        );

        assert!(decision.is_some());
        // Cell is healthier than wifi_weak, both eth links are down
        assert_eq!(decision.unwrap().0, "cell");
    }
}
