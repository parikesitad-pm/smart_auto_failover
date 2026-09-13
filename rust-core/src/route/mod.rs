use std::sync::Arc;
use tracing::info;

use crate::platform::{PlatformBackend, PlatformError};

pub struct RouteManager {
    platform: Arc<dyn PlatformBackend>,
}

impl RouteManager {
    pub fn new(platform: Arc<dyn PlatformBackend>) -> Self {
        Self { platform }
    }

    /// Promote interface as the primary default gateway by applying lowest metric (e.g., 50).
    pub async fn promote_primary_route(&self, interface_name: &str) -> Result<(), PlatformError> {
        info!("RouteManager: promoting '{}' to primary route (metric 50)", interface_name);
        self.platform.set_route_metric(interface_name, 50).await
    }

    /// Demote interface to standby by elevating route metric (e.g., 200).
    pub async fn demote_standby_route(&self, interface_name: &str, priority_rank: u32) -> Result<(), PlatformError> {
        let metric = 100 + (priority_rank * 50);
        info!("RouteManager: demoting '{}' to standby route (metric {})", interface_name, metric);
        self.platform.set_route_metric(interface_name, metric).await
    }

    /// Query current active default interface from kernel routing table.
    pub async fn get_active_default_interface(&self) -> Result<Option<String>, PlatformError> {
        self.platform.get_active_default_interface().await
    }

    /// Verify whether the expected target interface has become the active default gateway.
    pub async fn verify_active_route(&self, expected_target: &str) -> Result<bool, PlatformError> {
        let active = self.get_active_default_interface().await?;
        Ok(active.map(|a| a == expected_target).unwrap_or(false))
    }

    /// Retrieve gateway IP address for given interface.
    pub async fn get_interface_gateway(&self, interface_name: &str) -> Result<Option<String>, PlatformError> {
        self.platform.get_interface_gateway(interface_name).await
    }
}
