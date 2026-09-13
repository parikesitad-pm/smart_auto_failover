use std::sync::Arc;
use std::time::Duration;
use tracing::{info, warn};

use crate::models::{InterfaceState, NetworkInterface};
use crate::route::RouteManager;

pub struct FailoverEngine {
    route_manager: Arc<RouteManager>,
}

impl FailoverEngine {
    pub fn new(route_manager: Arc<RouteManager>) -> Self {
        Self { route_manager }
    }

    /// Execute seamless routing table priority transition with strict pre-flight validation and post-verification.
    /// Does not hold state locks during OS-level route manipulation.
    pub async fn execute_route_handover(
        &self,
        interfaces: &[NetworkInterface],
        previous_id: &str,
        target_id: &str,
        reason: &str,
    ) -> Result<(), String> {
        info!(
            "FAILOVER INITIATED: switching primary route from '{}' to '{}'. Reason: {}",
            previous_id, target_id, reason
        );

        // 1. Pre-flight Validation: Target interface must exist
        let target = interfaces
            .iter()
            .find(|i| i.id == target_id)
            .ok_or_else(|| format!("Target interface '{}' not found in registry", target_id))?;

        // 2. Pre-flight Validation: Operational and Administrative state
        if !target.is_admin_enabled {
            return Err(format!(
                "Cannot fail over to '{}': interface is administratively disabled",
                target_id
            ));
        }

        if !target.carrier_detected {
            return Err(format!(
                "Cannot fail over to '{}': no physical carrier link detected",
                target_id
            ));
        }

        if target.state == InterfaceState::Disabled || target.state == InterfaceState::Offline {
            return Err(format!(
                "Cannot fail over to '{}': invalid interface operational state ({:?})",
                target_id, target.state
            ));
        }

        // 3. Pre-flight Validation: Local IPv4 address must be present
        if target.ip_addresses.is_empty() {
            return Err(format!(
                "Cannot fail over to '{}': no local IP address assigned",
                target_id
            ));
        }

        // 4. Pre-flight Validation: Gateway address must exist and be routable
        let gw = self
            .route_manager
            .get_interface_gateway(target_id)
            .await
            .map_err(|e| format!("Pre-flight gateway query error for '{}': {}", target_id, e))?;

        match gw {
            Some(ref g) if !g.is_empty() && g != "0.0.0.0" => {
                // Gateway valid
            }
            _ => {
                return Err(format!(
                    "Cannot fail over to '{}': missing or unroutable gateway address",
                    target_id
                ));
            }
        }

        // 5. Promote target interface route priority with bounded timeout (1500ms)
        let promote_future = self.route_manager.promote_primary_route(target_id);
        match tokio::time::timeout(Duration::from_millis(1500), promote_future).await {
            Ok(Ok(())) => {}
            Ok(Err(e)) => {
                warn!("Route promotion error for '{}': {}", target_id, e);
                return Err(format!("Route promotion failed for '{}': {}", target_id, e));
            }
            Err(_) => {
                return Err(format!(
                    "Route promotion timed out after 1500ms for '{}'",
                    target_id
                ));
            }
        }

        // 6. Demote previous route priority to standby (best-effort, non-blocking)
        if !previous_id.is_empty() && previous_id != target_id {
            let _ = self.route_manager.demote_standby_route(previous_id, 1).await;
        }

        // 7. Post-handover Route Verification:
        // Never report ONLINE merely because a route command returned success.
        let verify_res = tokio::time::timeout(
            Duration::from_millis(1500),
            self.route_manager.verify_active_route(target_id),
        )
        .await;

        match verify_res {
            Ok(Ok(true)) => {
                info!(
                    "FAILOVER ROUTE HANDOVER COMPLETED: '{}' verified as active default route.",
                    target_id
                );
                Ok(())
            }
            Ok(Ok(false)) => {
                let actual = self
                    .route_manager
                    .get_active_default_interface()
                    .await
                    .ok()
                    .flatten();
                warn!(
                    "Post-handover route verification failed: expected active '{}', actual is '{:?}'",
                    target_id, actual
                );
                Err(format!(
                    "Post-handover active path verification failed: default route did not switch to '{}' (current active: '{:?}')",
                    target_id, actual
                ))
            }
            Ok(Err(e)) => Err(format!(
                "Post-handover verification query error for '{}': {}",
                target_id, e
            )),
            Err(_) => Err(format!(
                "Post-handover route verification timed out after 1500ms for '{}'",
                target_id
            )),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::{InterfaceKind, PathMetrics};
    use crate::platform::{PlatformBackend, PlatformError, RawDiscoveredDevice};
    use async_trait::async_trait;

    struct MockRoutePlatform {
        active_route: tokio::sync::Mutex<Option<String>>,
        fail_route: bool,
    }

    #[async_trait]
    impl PlatformBackend for MockRoutePlatform {
        async fn discover_adapters(&self) -> Result<Vec<RawDiscoveredDevice>, PlatformError> {
            Ok(Vec::new())
        }
        async fn set_interface_admin_state(&self, _name: &str, _up: bool) -> Result<(), PlatformError> {
            Ok(())
        }
        async fn set_route_metric(&self, name: &str, _metric: u32) -> Result<(), PlatformError> {
            if self.fail_route {
                return Err(PlatformError::ExecutionFailed("Mock route metric failure".into()));
            }
            *self.active_route.lock().await = Some(name.to_string());
            Ok(())
        }
        async fn check_carrier(&self, _name: &str) -> Result<bool, PlatformError> {
            Ok(true)
        }
        async fn get_active_default_interface(&self) -> Result<Option<String>, PlatformError> {
            Ok(self.active_route.lock().await.clone())
        }
        async fn get_interface_gateway(&self, _name: &str) -> Result<Option<String>, PlatformError> {
            Ok(Some("192.168.1.1".to_string()))
        }
        async fn get_system_identity(&self) -> Result<crate::models::SystemIdentity, PlatformError> {
            Ok(crate::models::SystemIdentity {
                device_name: "Mock Device".to_string(),
                os_name: "Linux".to_string(),
                architecture: "x86_64".to_string(),
                kernel_or_version: "6.0".to_string(),
                total_interfaces_detected: 2,
                active_connection: self.active_route.lock().await.clone(),
            })
        }
        async fn get_interface_network_info(&self, name: &str) -> Result<Option<crate::models::InterfaceNetworkInfo>, PlatformError> {
            Ok(Some(crate::models::InterfaceNetworkInfo {
                name: name.to_string(),
                ip_addresses: vec!["192.168.1.50".to_string()],
                gateway: Some("192.168.1.1".to_string()),
                metric: Some(100),
            }))
        }
    }

    fn make_test_iface(id: &str, state: InterfaceState, carrier: bool, admin: bool) -> NetworkInterface {
        NetworkInterface {
            id: id.to_string(),
            name: id.to_string(),
            kind: InterfaceKind::Ethernet,
            mac: None,
            ip_addresses: vec!["192.168.1.50".to_string()],
            gateway: Some("192.168.1.1".to_string()),
            state,
            metrics: PathMetrics::default(),
            is_admin_enabled: admin,
            is_physical: true,
            carrier_detected: carrier,
            metric_priority: 100,
        }
    }

    #[tokio::test]
    async fn test_failover_preflight_validates_target_state() {
        let platform = Arc::new(MockRoutePlatform {
            active_route: tokio::sync::Mutex::new(Some("eth0".to_string())),
            fail_route: false,
        });
        let route_mgr = Arc::new(RouteManager::new(platform));
        let engine = FailoverEngine::new(route_mgr);

        let active = make_test_iface("eth0", InterfaceState::Online, true, true);
        // Target is disabled
        let disabled_target = make_test_iface("eth1", InterfaceState::Disabled, true, false);

        let interfaces = vec![active, disabled_target];
        let result = engine
            .execute_route_handover(&interfaces, "eth0", "eth1", "test")
            .await;

        assert!(result.is_err());
        assert!(result.unwrap_err().contains("administratively disabled"));
    }

    #[tokio::test]
    async fn test_failover_preflight_validates_target_carrier() {
        let platform = Arc::new(MockRoutePlatform {
            active_route: tokio::sync::Mutex::new(Some("eth0".to_string())),
            fail_route: false,
        });
        let route_mgr = Arc::new(RouteManager::new(platform));
        let engine = FailoverEngine::new(route_mgr);

        let active = make_test_iface("eth0", InterfaceState::Online, true, true);
        // Target has no carrier
        let no_carrier = make_test_iface("eth1", InterfaceState::Offline, false, true);

        let interfaces = vec![active, no_carrier];
        let result = engine
            .execute_route_handover(&interfaces, "eth0", "eth1", "test")
            .await;

        assert!(result.is_err());
        assert!(result.unwrap_err().contains("no physical carrier"));
    }

    #[tokio::test]
    async fn test_failover_route_failure_returns_explicit_error() {
        let platform = Arc::new(MockRoutePlatform {
            active_route: tokio::sync::Mutex::new(Some("eth0".to_string())),
            fail_route: true, // Injected route failure
        });
        let route_mgr = Arc::new(RouteManager::new(platform));
        let engine = FailoverEngine::new(route_mgr);

        let active = make_test_iface("eth0", InterfaceState::Online, true, true);
        let candidate = make_test_iface("eth1", InterfaceState::Ready, true, true);

        let interfaces = vec![active, candidate];
        let result = engine
            .execute_route_handover(&interfaces, "eth0", "eth1", "test")
            .await;

        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Route promotion failed"));
    }

    #[tokio::test]
    async fn test_failover_postflight_verification_failure_returns_explicit_error() {
        // Platform route command succeeds, but active default route does not switch!
        struct UnswitchingPlatform {
            #[allow(dead_code)]
            active_route: tokio::sync::Mutex<Option<String>>,
        }

        #[async_trait]
        impl PlatformBackend for UnswitchingPlatform {
            async fn discover_adapters(&self) -> Result<Vec<RawDiscoveredDevice>, PlatformError> {
                Ok(Vec::new())
            }
            async fn set_interface_admin_state(&self, _name: &str, _up: bool) -> Result<(), PlatformError> {
                Ok(())
            }
            async fn set_route_metric(&self, _name: &str, _metric: u32) -> Result<(), PlatformError> {
                // Command succeeds, but does not update active_route
                Ok(())
            }
            async fn check_carrier(&self, _name: &str) -> Result<bool, PlatformError> {
                Ok(true)
            }
            async fn get_active_default_interface(&self) -> Result<Option<String>, PlatformError> {
                // Still stuck on eth0
                Ok(Some("eth0".to_string()))
            }
            async fn get_interface_gateway(&self, _name: &str) -> Result<Option<String>, PlatformError> {
                Ok(Some("192.168.1.1".to_string()))
            }
            async fn get_system_identity(&self) -> Result<crate::models::SystemIdentity, PlatformError> {
                Ok(crate::models::SystemIdentity {
                    device_name: "Mock".to_string(),
                    os_name: "Linux".to_string(),
                    architecture: "x86_64".to_string(),
                    kernel_or_version: "6.0".to_string(),
                    total_interfaces_detected: 2,
                    active_connection: Some("eth0".to_string()),
                })
            }
            async fn get_interface_network_info(&self, name: &str) -> Result<Option<crate::models::InterfaceNetworkInfo>, PlatformError> {
                Ok(Some(crate::models::InterfaceNetworkInfo {
                    name: name.to_string(),
                    ip_addresses: vec!["192.168.1.50".to_string()],
                    gateway: Some("192.168.1.1".to_string()),
                    metric: Some(100),
                }))
            }
        }

        let platform = Arc::new(UnswitchingPlatform {
            active_route: tokio::sync::Mutex::new(Some("eth0".to_string())),
        });
        let route_mgr = Arc::new(RouteManager::new(platform));
        let engine = FailoverEngine::new(route_mgr);

        let active = make_test_iface("eth0", InterfaceState::Online, true, true);
        let candidate = make_test_iface("eth1", InterfaceState::Ready, true, true);

        let interfaces = vec![active, candidate];
        let result = engine
            .execute_route_handover(&interfaces, "eth0", "eth1", "test")
            .await;

        assert!(result.is_err());
        let err_msg = result.unwrap_err();
        assert!(err_msg.contains("Post-handover active path verification failed"));
    }
}
