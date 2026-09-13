use std::sync::Arc;
use tracing::{debug, info};

use crate::models::{InterfaceState, NetworkInterface, PathMetrics};
use crate::platform::PlatformBackend;

pub struct DiscoveryEngine {
    platform: Arc<dyn PlatformBackend>,
}

impl DiscoveryEngine {
    pub fn new(platform: Arc<dyn PlatformBackend>) -> Self {
        Self { platform }
    }

    /// Dynamically discover physical and usable network adapters.
    /// Distinguishes between DISABLED, OFFLINE, and candidate states.
    pub async fn discover_interfaces(&self) -> Vec<NetworkInterface> {
        let raw_devices = match self.platform.discover_adapters().await {
            Ok(devices) => devices,
            Err(err) => {
                debug!("Interface discovery fallback: {}", err);
                Vec::new()
            }
        };

        let mut result = Vec::new();

        for dev in raw_devices {
            // Determine initial state:
            // 1. If admin is down -> DISABLED (per Master Prompt §7: DISABLED distinct from OFFLINE)
            // 2. If carrier is false -> OFFLINE
            // 3. Otherwise -> READY (will be evaluated by Policy Engine)
            let state = if !dev.admin_up {
                InterfaceState::Disabled
            } else if !dev.carrier {
                InterfaceState::Offline
            } else {
                InterfaceState::Ready
            };

            result.push(NetworkInterface {
                id: dev.name.clone(),
                name: dev.name,
                kind: dev.kind,
                mac: dev.mac,
                ip_addresses: dev.ip_addresses,
                gateway: dev.gateway,
                state,
                metrics: PathMetrics::default(),
                is_admin_enabled: dev.admin_up,
                is_physical: dev.is_physical,
                carrier_detected: dev.carrier,
                metric_priority: dev.metric,
                ssid: dev.ssid,
            });
        }

        info!("Discovered {} usable network interfaces", result.len());
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::InterfaceKind;
    use crate::platform::{PlatformBackend, PlatformError, RawDiscoveredDevice};
    use async_trait::async_trait;

    struct MockPlatform {
        devices: Vec<RawDiscoveredDevice>,
    }

    #[async_trait]
    impl PlatformBackend for MockPlatform {
        async fn discover_adapters(&self) -> Result<Vec<RawDiscoveredDevice>, PlatformError> {
            Ok(self.devices.clone())
        }
        async fn set_interface_admin_state(&self, _name: &str, _up: bool) -> Result<(), PlatformError> {
            Ok(())
        }
        async fn set_route_metric(&self, _name: &str, _metric: u32) -> Result<(), PlatformError> {
            Ok(())
        }
        async fn check_carrier(&self, _name: &str) -> Result<bool, PlatformError> {
            Ok(true)
        }
        async fn get_active_default_interface(&self) -> Result<Option<String>, PlatformError> {
            Ok(self.devices.first().map(|d| d.name.clone()))
        }
        async fn get_interface_gateway(&self, name: &str) -> Result<Option<String>, PlatformError> {
            Ok(self.devices.iter().find(|d| d.name == name).and_then(|d| d.gateway.clone()))
        }
        async fn get_system_identity(&self) -> Result<crate::models::SystemIdentity, PlatformError> {
            Ok(crate::models::SystemIdentity {
                device_name: "Mock Machine".to_string(),
                os_name: "Linux".to_string(),
                architecture: "x86_64".to_string(),
                kernel_or_version: "6.0".to_string(),
                total_interfaces_detected: self.devices.len(),
                active_connection: self.devices.first().map(|d| d.name.clone()),
            })
        }
        async fn get_interface_network_info(&self, name: &str) -> Result<Option<crate::models::InterfaceNetworkInfo>, PlatformError> {
            let dev = self.devices.iter().find(|d| d.name == name);
            Ok(dev.map(|d| crate::models::InterfaceNetworkInfo {
                name: d.name.clone(),
                ip_addresses: d.ip_addresses.clone(),
                gateway: d.gateway.clone(),
                metric: Some(d.metric),
            }))
        }
    }

    #[tokio::test]
    async fn test_initial_discovery_maps_states_correctly() {
        let mock_platform = Arc::new(MockPlatform {
            devices: vec![
                RawDiscoveredDevice {
                    name: "eth0".to_string(),
                    kind: InterfaceKind::Ethernet,
                    mac: Some("aa:bb:cc:dd:ee:01".to_string()),
                    ip_addresses: vec!["192.168.1.10".to_string()],
                    gateway: Some("192.168.1.1".to_string()),
                    carrier: true,
                    admin_up: true,
                    is_physical: true,
                    metric: 100,
                    ssid: None,
                },
                RawDiscoveredDevice {
                    name: "wlan0".to_string(),
                    kind: InterfaceKind::WiFi,
                    mac: Some("aa:bb:cc:dd:ee:02".to_string()),
                    ip_addresses: vec![],
                    gateway: None,
                    carrier: false,
                    admin_up: true,
                    is_physical: true,
                    metric: 600,
                    ssid: None,
                },
                RawDiscoveredDevice {
                    name: "eth1".to_string(),
                    kind: InterfaceKind::Ethernet,
                    mac: Some("aa:bb:cc:dd:ee:03".to_string()),
                    ip_addresses: vec![],
                    gateway: None,
                    carrier: false,
                    admin_up: false,
                    is_physical: true,
                    metric: 200,
                    ssid: None,
                },
            ],
        });

        let discovery = DiscoveryEngine::new(mock_platform);
        let discovered = discovery.discover_interfaces().await;

        assert_eq!(discovered.len(), 3);
        assert_eq!(discovered[0].state, InterfaceState::Ready);
        assert_eq!(discovered[1].state, InterfaceState::Offline);
        assert_eq!(discovered[2].state, InterfaceState::Disabled);
    }
}
