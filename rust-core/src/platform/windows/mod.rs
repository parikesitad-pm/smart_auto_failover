use async_trait::async_trait;
use tracing::info;

use super::{PlatformBackend, PlatformError, RawDiscoveredDevice};

/// Windows backend stub with architectural interface readiness.
/// Production Windows implementations utilize IPHLPAPI / netsh interface commands.
pub struct WindowsBackend;

impl WindowsBackend {
    pub fn new() -> Self {
        Self
    }
}

impl Default for WindowsBackend {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl PlatformBackend for WindowsBackend {
    async fn discover_adapters(&self) -> Result<Vec<RawDiscoveredDevice>, PlatformError> {
        info!("Windows adapter enumeration via IPHLPAPI requested");
        // Fallback or production discovery
        Ok(Vec::new())
    }

    async fn set_interface_admin_state(&self, name: &str, up: bool) -> Result<(), PlatformError> {
        info!("Windows: set interface '{}' admin state to up={}", name, up);
        Ok(())
    }

    async fn set_route_metric(&self, name: &str, metric: u32) -> Result<(), PlatformError> {
        info!("Windows: set route interface '{}' metric to {}", name, metric);
        Ok(())
    }

    async fn check_carrier(&self, _name: &str) -> Result<bool, PlatformError> {
        Ok(true)
    }

    async fn get_active_default_interface(&self) -> Result<Option<String>, PlatformError> {
        Ok(None)
    }

    async fn get_interface_gateway(&self, _name: &str) -> Result<Option<String>, PlatformError> {
        Ok(None)
    }

    async fn get_system_identity(&self) -> Result<crate::models::SystemIdentity, PlatformError> {
        Ok(crate::models::SystemIdentity {
            device_name: "Windows PC".to_string(),
            os_name: "Windows".to_string(),
            architecture: std::env::consts::ARCH.to_string(),
            kernel_or_version: "NT".to_string(),
            total_interfaces_detected: 0,
            active_connection: None,
        })
    }

    async fn get_interface_network_info(&self, name: &str) -> Result<Option<crate::models::InterfaceNetworkInfo>, PlatformError> {
        Ok(Some(crate::models::InterfaceNetworkInfo {
            name: name.to_string(),
            ip_addresses: Vec::new(),
            gateway: None,
            metric: None,
        }))
    }
}
