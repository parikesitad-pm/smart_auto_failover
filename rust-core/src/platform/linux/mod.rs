use async_trait::async_trait;
use std::collections::HashMap;
use std::fs;
use std::net::Ipv4Addr;
use std::path::Path;
use std::process::Command;
use tracing::{debug, warn};

use super::{PlatformBackend, PlatformError, RawDiscoveredDevice};
use crate::models::{InterfaceKind, InterfaceNetworkInfo, SystemIdentity};

#[derive(Debug, Clone)]
struct LinuxRouteEntry {
    iface: String,
    destination: String,
    gateway: String,
    flags: u32,
    metric: u32,
}

pub struct LinuxBackend;

impl LinuxBackend {
    pub fn new() -> Self {
        Self
    }

    fn classify_interface(name: &str, is_physical: bool) -> InterfaceKind {
        if name.starts_with("wl") || name.starts_with("wlan") {
            InterfaceKind::WiFi
        } else if name.starts_with("en") || name.starts_with("eth") {
            InterfaceKind::Ethernet
        } else if name.starts_with("ww") || name.starts_with("ppp") {
            InterfaceKind::Cellular
        } else if is_physical {
            InterfaceKind::Ethernet
        } else {
            InterfaceKind::Virtual
        }
    }

    /// Parse hex IP from /proc/net/route into standard dotted-decimal IPv4 string.
    /// In /proc/net/route, IPv4 addresses are stored in little-endian 32-bit hex.
    fn hex_to_ipv4(hex_str: &str) -> Option<String> {
        let val = u32::from_str_radix(hex_str, 16).ok()?;
        let bytes = val.to_le_bytes();
        let ip = Ipv4Addr::new(bytes[0], bytes[1], bytes[2], bytes[3]);
        Some(ip.to_string())
    }

    /// Parse kernel routing table directly from /proc/net/route without subprocess overhead.
    fn read_proc_net_route() -> Vec<LinuxRouteEntry> {
        let content = match fs::read_to_string("/proc/net/route") {
            Ok(c) => c,
            Err(_) => return Vec::new(),
        };

        let mut routes = Vec::new();
        for (idx, line) in content.lines().enumerate() {
            if idx == 0 {
                continue; // Skip header
            }
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 8 {
                continue;
            }

            let iface = parts[0].to_string();
            let destination = parts[1].to_string();
            let gw_hex = parts[2];
            let flags = u32::from_str_radix(parts[3], 16).unwrap_or(0);
            let metric = parts[6].parse::<u32>().unwrap_or(0);

            let gateway = Self::hex_to_ipv4(gw_hex).unwrap_or_else(|| "0.0.0.0".to_string());

            routes.push(LinuxRouteEntry {
                iface,
                destination,
                gateway,
                flags,
                metric,
            });
        }
        routes
    }

    /// Query local IPv4 addresses assigned to interfaces using ip -o -4 addr.
    fn read_ipv4_addresses() -> HashMap<String, Vec<String>> {
        let mut map: HashMap<String, Vec<String>> = HashMap::new();

        let output = match Command::new("ip")
            .args(["-o", "-4", "addr", "show"])
            .output()
        {
            Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).to_string(),
            _ => return map,
        };

        for line in output.lines() {
            // Format: 2: enp44s0    inet 192.168.50.88/24 ...
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 4 && parts[2] == "inet" {
                let iface_name = parts[1].to_string();
                let ip_cidr = parts[3];
                let ip = ip_cidr.split('/').next().unwrap_or(ip_cidr).to_string();
                map.entry(iface_name).or_default().push(ip);
            }
        }

        map
    }
}

impl Default for LinuxBackend {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl PlatformBackend for LinuxBackend {
    async fn discover_adapters(&self) -> Result<Vec<RawDiscoveredDevice>, PlatformError> {
        let net_dir = Path::new("/sys/class/net");
        if !net_dir.exists() {
            return Err(PlatformError::NotFound("/sys/class/net directory not found".to_string()));
        }

        let routes = Self::read_proc_net_route();
        let ip_map = Self::read_ipv4_addresses();

        let mut devices = Vec::new();
        let entries = fs::read_dir(net_dir)?;

        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();

            // Ignore loopback
            if name == "lo" {
                continue;
            }

            let iface_path = entry.path();
            let is_physical = iface_path.join("device").exists();

            // Read carrier: 1 = link carrier present
            let carrier = fs::read_to_string(iface_path.join("carrier"))
                .map(|s| s.trim() == "1")
                .unwrap_or(false);

            // Read operstate: up, down, dormant, lowerlayerdown, unknown
            let operstate = fs::read_to_string(iface_path.join("operstate"))
                .map(|s| s.trim().to_lowercase())
                .unwrap_or_else(|_| "unknown".to_string());

            // Read administrative state from flags (bit 0x1 is IFF_UP)
            let admin_up = fs::read_to_string(iface_path.join("flags"))
                .ok()
                .and_then(|s| {
                    let hex_str = s.trim().trim_start_matches("0x");
                    u32::from_str_radix(hex_str, 16).ok()
                })
                .map(|flags| (flags & 0x1) != 0)
                .unwrap_or_else(|| operstate == "up" || operstate == "unknown");

            // Read MAC address
            let mac = fs::read_to_string(iface_path.join("address"))
                .map(|s| s.trim().to_string())
                .ok()
                .filter(|m| !m.is_empty() && m != "00:00:00:00:00:00");

            let kind = Self::classify_interface(&name, is_physical);
            let ip_addresses = ip_map.get(&name).cloned().unwrap_or_default();

            // Find default route gateway and metric for this interface if configured
            let default_route = routes.iter().find(|r| r.iface == name && r.destination == "00000000");
            let gateway = default_route.and_then(|r| {
                if r.gateway == "0.0.0.0" {
                    None
                } else {
                    Some(r.gateway.clone())
                }
            });
            let metric = default_route.map(|r| r.metric).unwrap_or(100);

            devices.push(RawDiscoveredDevice {
                name,
                kind,
                mac,
                ip_addresses,
                gateway,
                carrier,
                admin_up,
                is_physical,
                metric,
            });
        }

        debug!("Discovered {} interfaces via Linux /sys/class/net", devices.len());
        Ok(devices)
    }

    async fn set_interface_admin_state(&self, name: &str, up: bool) -> Result<(), PlatformError> {
        let state_arg = if up { "up" } else { "down" };
        let output = Command::new("ip")
            .args(["link", "set", name, state_arg])
            .output()?;

        if !output.status.success() {
            let err = String::from_utf8_lossy(&output.stderr);
            if err.contains("Operation not permitted") || err.contains("Permission denied") {
                return Err(PlatformError::PermissionDenied(format!(
                    "Cannot set interface '{}' state: insufficient permissions ({})",
                    name, err.trim()
                )));
            }
            warn!("Failed to set interface '{}' to {}: {}", name, state_arg, err);
            return Err(PlatformError::ExecutionFailed(format!("ip link error: {}", err.trim())));
        }

        Ok(())
    }

    async fn set_route_metric(&self, name: &str, metric: u32) -> Result<(), PlatformError> {
        debug!("Linux: adjusting route metric for {} to {}", name, metric);
        let gw = self.get_interface_gateway(name).await?.unwrap_or_default();

        let mut cmd = Command::new("ip");
        cmd.args(["route", "replace", "default"]);
        if !gw.is_empty() && gw != "0.0.0.0" {
            cmd.args(["via", &gw]);
        }
        cmd.args(["dev", name, "metric", &metric.to_string()]);

        let output = cmd.output()?;
        if !output.status.success() {
            let err = String::from_utf8_lossy(&output.stderr);
            if err.contains("Operation not permitted") || err.contains("Permission denied") {
                return Err(PlatformError::PermissionDenied(format!(
                    "Cannot adjust route metric for '{}': permission denied ({})",
                    name, err.trim()
                )));
            }
            return Err(PlatformError::ExecutionFailed(format!("ip route error: {}", err.trim())));
        }

        Ok(())
    }

    async fn check_carrier(&self, name: &str) -> Result<bool, PlatformError> {
        let iface_path = format!("/sys/class/net/{}", name);
        if !Path::new(&iface_path).exists() {
            return Ok(false);
        }

        let operstate = fs::read_to_string(format!("{}/operstate", iface_path))
            .map(|s| s.trim().to_lowercase())
            .unwrap_or_else(|_| "unknown".to_string());

        if operstate == "down" || operstate == "dormant" || operstate == "lowerlayerdown" {
            return Ok(false);
        }

        let carrier = fs::read_to_string(format!("{}/carrier", iface_path))
            .map(|s| s.trim() == "1")
            .unwrap_or(false);

        Ok(carrier && (operstate == "up" || operstate == "unknown"))
    }

    async fn get_active_default_interface(&self) -> Result<Option<String>, PlatformError> {
        let routes = Self::read_proc_net_route();
        // Active default gateway is the default route (Destination == "00000000") with lowest metric
        let mut default_routes: Vec<&LinuxRouteEntry> = routes
            .iter()
            .filter(|r| r.destination == "00000000" && (r.flags & 2 != 0 || r.gateway != "0.0.0.0"))
            .collect();

        default_routes.sort_by_key(|r| r.metric);

        Ok(default_routes.first().map(|r| r.iface.clone()))
    }

    async fn get_interface_gateway(&self, name: &str) -> Result<Option<String>, PlatformError> {
        let routes = Self::read_proc_net_route();
        let gw = routes
            .iter()
            .find(|r| r.iface == name && r.destination == "00000000" && r.gateway != "0.0.0.0")
            .map(|r| r.gateway.clone());

        Ok(gw)
    }

    async fn get_system_identity(&self) -> Result<SystemIdentity, PlatformError> {
        let device_name = fs::read_to_string("/sys/class/dmi/id/product_name")
            .ok()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .or_else(|| {
                fs::read_to_string("/etc/hostname")
                    .ok()
                    .map(|s| s.trim().to_string())
                    .filter(|s| !s.is_empty())
            })
            .unwrap_or_else(|| "Linux Device".to_string());

        let os_name = fs::read_to_string("/etc/os-release")
            .ok()
            .and_then(|content| {
                for line in content.lines() {
                    if let Some(val) = line.strip_prefix("PRETTY_NAME=") {
                        return Some(val.trim_matches('"').to_string());
                    }
                }
                for line in content.lines() {
                    if let Some(val) = line.strip_prefix("NAME=") {
                        return Some(val.trim_matches('"').to_string());
                    }
                }
                None
            })
            .unwrap_or_else(|| "Linux".to_string());

        let architecture = std::env::consts::ARCH.to_string();

        let kernel_or_version = fs::read_to_string("/proc/sys/kernel/osrelease")
            .map(|s| s.trim().to_string())
            .unwrap_or_else(|_| "Linux Kernel".to_string());

        let total_interfaces_detected = fs::read_dir("/sys/class/net")
            .map(|entries| {
                entries
                    .flatten()
                    .filter(|e| e.file_name() != "lo")
                    .count()
            })
            .unwrap_or(0);

        let active_connection = self.get_active_default_interface().await.ok().flatten();

        Ok(SystemIdentity {
            device_name,
            os_name,
            architecture,
            kernel_or_version,
            total_interfaces_detected,
            active_connection,
        })
    }

    async fn get_interface_network_info(&self, name: &str) -> Result<Option<InterfaceNetworkInfo>, PlatformError> {
        let ip_map = Self::read_ipv4_addresses();
        let ip_addresses = ip_map.get(name).cloned().unwrap_or_default();
        let gateway = self.get_interface_gateway(name).await?;

        let routes = Self::read_proc_net_route();
        let metric = routes
            .iter()
            .find(|r| r.iface == name && r.destination == "00000000")
            .map(|r| r.metric);

        Ok(Some(InterfaceNetworkInfo {
            name: name.to_string(),
            ip_addresses,
            gateway,
            metric,
        }))
    }
}
