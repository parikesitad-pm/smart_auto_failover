pub mod linux;
pub mod macos;
pub mod windows;

use async_trait::async_trait;
use thiserror::Error;

use crate::models::{InterfaceKind, InterfaceNetworkInfo, SystemIdentity};

#[derive(Error, Debug)]
pub enum PlatformError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Interface '{0}' not found")]
    NotFound(String),

    #[error("Operation not permitted (insufficient privileges): {0}")]
    PermissionDenied(String),

    #[error("Platform unsupported or feature unavailable: {0}")]
    Unsupported(String),

    #[error("Command execution failed: {0}")]
    ExecutionFailed(String),
}

/// Raw discovered device from OS enumeration.
#[derive(Debug, Clone)]
pub struct RawDiscoveredDevice {
    pub name: String,
    pub kind: InterfaceKind,
    pub mac: Option<String>,
    pub ip_addresses: Vec<String>,
    pub gateway: Option<String>,
    pub carrier: bool,
    pub admin_up: bool,
    pub is_physical: bool,
    pub metric: u32,
}

/// Platform-agnostic interface manipulation interface.
#[async_trait]
pub trait PlatformBackend: Send + Sync {
    /// Query native OS network subsystem for physical and virtual interfaces.
    async fn discover_adapters(&self) -> Result<Vec<RawDiscoveredDevice>, PlatformError>;

    /// Administratively toggle adapter up/down state.
    async fn set_interface_admin_state(&self, name: &str, up: bool) -> Result<(), PlatformError>;

    /// Adjust routing table gateway metric (Layer-3 metric steering).
    async fn set_route_metric(&self, name: &str, metric: u32) -> Result<(), PlatformError>;

    /// Verify physical link carrier state.
    async fn check_carrier(&self, name: &str) -> Result<bool, PlatformError>;

    /// Determine currently active default route interface (Layer-3 gateway owner).
    async fn get_active_default_interface(&self) -> Result<Option<String>, PlatformError>;

    /// Retrieve gateway IP address for given interface.
    async fn get_interface_gateway(&self, name: &str) -> Result<Option<String>, PlatformError>;

    /// Retrieve compact system identity for bootstrap summary.
    async fn get_system_identity(&self) -> Result<SystemIdentity, PlatformError>;

    /// Retrieve detailed network addressing and gateway info for a single interface.
    async fn get_interface_network_info(&self, name: &str) -> Result<Option<InterfaceNetworkInfo>, PlatformError>;
}

/// Factory creating the active OS platform backend.
pub fn create_platform_backend() -> Box<dyn PlatformBackend> {
    #[cfg(target_os = "linux")]
    {
        Box::new(linux::LinuxBackend::new())
    }
    #[cfg(target_os = "windows")]
    {
        Box::new(windows::WindowsBackend::new())
    }
    #[cfg(target_os = "macos")]
    {
        Box::new(macos::MacosBackend::new())
    }
    #[cfg(not(any(target_os = "linux", target_os = "windows", target_os = "macos")))]
    {
        Box::new(linux::LinuxBackend::new())
    }
}
