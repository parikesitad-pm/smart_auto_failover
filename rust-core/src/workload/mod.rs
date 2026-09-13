use crate::models::WorkloadProfile;

pub struct WorkloadDetector {
    current_profile: WorkloadProfile,
}

impl WorkloadDetector {
    pub fn new() -> Self {
        Self {
            current_profile: WorkloadProfile::VideoConference,
        }
    }

    pub fn set_profile(&mut self, profile: WorkloadProfile) {
        self.current_profile = profile;
    }

    pub fn current_profile(&self) -> WorkloadProfile {
        self.current_profile
    }

    /// Passive process-based workload inference.
    /// Informs Policy Engine; NEVER directly switches interfaces.
    pub fn detect_active_workload(&self, active_process_names: &[String]) -> WorkloadProfile {
        let is_broadcast = active_process_names.iter().any(|p| {
            let low = p.to_lowercase();
            low.contains("obs") || low.contains("vmix") || low.contains("wirecast") || low.contains("streamlabs")
        });

        if is_broadcast {
            return WorkloadProfile::LiveProduction;
        }

        let is_conferencing = active_process_names.iter().any(|p| {
            let low = p.to_lowercase();
            low.contains("zoom") || low.contains("teams") || low.contains("webex") || low.contains("meet")
        });

        if is_conferencing {
            return WorkloadProfile::VideoConference;
        }

        self.current_profile
    }
}

impl Default for WorkloadDetector {
    fn default() -> Self {
        Self::new()
    }
}
