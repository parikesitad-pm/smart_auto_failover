use serde::{Deserialize, Serialize};

use crate::models::FailoverEvent;

/// Summary report of network resilience events and session continuity.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionReport {
    pub session_duration_seconds: u64,
    pub total_failovers: u32,
    pub uninterrupted_uptime_pct: f64,
    pub failover_history: Vec<FailoverEvent>,
}

impl Default for SessionReport {
    fn default() -> Self {
        Self {
            session_duration_seconds: 0,
            total_failovers: 0,
            uninterrupted_uptime_pct: 100.0,
            failover_history: Vec::new(),
        }
    }
}
