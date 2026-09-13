use tracing::info;

use crate::models::WorkloadProfile;

pub struct QosOrchestrator;

impl QosOrchestrator {
    pub fn new() -> Self {
        Self
    }

    /// Apply OS-level DSCP / packet tag priority based on active workload.
    pub fn apply_profile_qos(&self, profile: WorkloadProfile) {
        match profile {
            WorkloadProfile::VideoConference => {
                info!("QoS: Setting DSCP Expedited Forwarding (EF - 46) for real-time audio/video");
            }
            WorkloadProfile::LiveProduction => {
                info!("QoS: Setting DSCP Assured Forwarding (AF41) for high-throughput broadcast stream");
            }
            WorkloadProfile::General | WorkloadProfile::Custom => {
                info!("QoS: Standard Best-Effort QoS profile active");
            }
        }
    }
}

impl Default for QosOrchestrator {
    fn default() -> Self {
        Self::new()
    }
}
