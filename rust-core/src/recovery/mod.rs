use std::collections::HashMap;
use std::time::{Duration, Instant};

/// Anti-flap recovery monitor that enforces stability duration before a recovering interface is marked READY.
/// Implements Master Prompt Section 2 & 10: "Preserve healthy active path; recovered preferred interface must return to READY first".
#[derive(Debug, Clone)]
pub struct RecoveryArbiter {
    min_stability_duration: Duration,
    link_up_timestamps: HashMap<String, Instant>,
    stabilized_interfaces: HashMap<String, bool>,
}

impl RecoveryArbiter {
    pub fn new(min_stability_duration: Duration) -> Self {
        Self {
            min_stability_duration,
            link_up_timestamps: HashMap::new(),
            stabilized_interfaces: HashMap::new(),
        }
    }

    /// Record link carrier recovery.
    /// Returns true if this starts a new recovery transition cycle.
    pub fn on_link_up(&mut self, interface_id: &str) -> bool {
        if self.link_up_timestamps.contains_key(interface_id) {
            false
        } else {
            self.link_up_timestamps.insert(interface_id.to_string(), Instant::now());
            self.stabilized_interfaces.insert(interface_id.to_string(), false);
            true
        }
    }

    /// Record link state and determine if interface has completed the stability cooldown.
    pub fn is_stabilized(&mut self, interface_id: &str, carrier_up: bool) -> bool {
        if !carrier_up {
            self.reset(interface_id);
            return false;
        }

        if let Some(already) = self.stabilized_interfaces.get(interface_id) {
            if *already {
                return true;
            }
        }

        let now = Instant::now();
        let up_since = match self.link_up_timestamps.get(interface_id) {
            Some(t) => *t,
            None => {
                self.link_up_timestamps.insert(interface_id.to_string(), now);
                now
            }
        };

        let stabilized = now.duration_since(up_since) >= self.min_stability_duration;
        if stabilized {
            self.stabilized_interfaces.insert(interface_id.to_string(), true);
        }
        stabilized
    }

    /// Mark recovery cycle complete and stabilized as READY.
    pub fn mark_completed(&mut self, interface_id: &str) {
        self.stabilized_interfaces.insert(interface_id.to_string(), true);
    }

    pub fn reset(&mut self, interface_id: &str) {
        self.link_up_timestamps.remove(interface_id);
        self.stabilized_interfaces.remove(interface_id);
    }

    pub fn is_recovering(&self, interface_id: &str) -> bool {
        self.link_up_timestamps.contains_key(interface_id)
            && !self.stabilized_interfaces.get(interface_id).copied().unwrap_or(false)
    }
}

impl Default for RecoveryArbiter {
    fn default() -> Self {
        Self::new(Duration::from_millis(2500)) // 2.5s anti-flap stability cooldown
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_recovery_lifecycle_and_cooldown() {
        let mut arbiter = RecoveryArbiter::new(Duration::from_millis(50));

        // 1. Initial carrier up starts recovery
        let is_new = arbiter.on_link_up("eth0");
        assert!(is_new);
        assert!(arbiter.is_recovering("eth0"));
        assert!(!arbiter.is_stabilized("eth0", true));

        // 2. Second on_link_up does not re-trigger new cycle
        assert!(!arbiter.on_link_up("eth0"));

        // 3. Before cooldown elapses, not stabilized
        assert!(!arbiter.is_stabilized("eth0", true));

        // 4. After duration, stabilized
        std::thread::sleep(Duration::from_millis(60));
        assert!(arbiter.is_stabilized("eth0", true));
        assert!(!arbiter.is_recovering("eth0"));
    }

    #[test]
    fn test_recovery_resets_on_carrier_loss() {
        let mut arbiter = RecoveryArbiter::new(Duration::from_millis(100));
        arbiter.on_link_up("eth1");

        // Carrier drops mid-cooldown
        let stabilized = arbiter.is_stabilized("eth1", false);
        assert!(!stabilized);
        assert!(!arbiter.is_recovering("eth1"));
    }
}
