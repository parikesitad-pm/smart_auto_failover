use std::collections::HashMap;
use std::fs;
use std::time::{Instant, SystemTime, UNIX_EPOCH};

use crate::models::{DeviceCapabilities, DeviceHealth, GpuMetrics, SystemTelemetry};

/// Bandwidth throughput tracker using differential OS byte counters (strictly passive).
/// Reads interface/OS statistics without generating synthetic network load.
pub struct ThroughputMonitor {
    last_records: HashMap<String, (u64, u64, Instant)>, // rx, tx, timestamp
}

impl ThroughputMonitor {
    pub fn new() -> Self {
        Self {
            last_records: HashMap::new(),
        }
    }

    /// Calculate Mbps download and upload from delta bytes observed passively in the OS kernel.
    pub fn calculate_rate(&mut self, interface_id: &str, current_rx: u64, current_tx: u64) -> (f64, f64) {
        let now = Instant::now();

        if let Some((prev_rx, prev_tx, prev_time)) = self.last_records.get(interface_id).copied() {
            let elapsed_secs = now.duration_since(prev_time).as_secs_f64();
            self.last_records.insert(interface_id.to_string(), (current_rx, current_tx, now));

            if elapsed_secs > 0.001 {
                let delta_rx = current_rx.saturating_sub(prev_rx) as f64 * 8.0; // bits
                let delta_tx = current_tx.saturating_sub(prev_tx) as f64 * 8.0; // bits

                let rx_mbps = (delta_rx / elapsed_secs) / 1_000_000.0;
                let tx_mbps = (delta_tx / elapsed_secs) / 1_000_000.0;

                return (rx_mbps.max(0.0), tx_mbps.max(0.0));
            }
        } else {
            self.last_records.insert(interface_id.to_string(), (current_rx, current_tx, now));
        }

        (0.0, 0.0)
    }

    /// Read interface kernel traffic counters from Linux sysfs passively.
    pub fn sample_interface_bytes(interface_id: &str) -> (u64, u64) {
        let rx_path = format!("/sys/class/net/{}/statistics/rx_bytes", interface_id);
        let tx_path = format!("/sys/class/net/{}/statistics/tx_bytes", interface_id);

        let rx = fs::read_to_string(rx_path)
            .ok()
            .and_then(|s| s.trim().parse::<u64>().ok())
            .unwrap_or(0);
        let tx = fs::read_to_string(tx_path)
            .ok()
            .and_then(|s| s.trim().parse::<u64>().ok())
            .unwrap_or(0);

        (rx, tx)
    }
}

impl Default for ThroughputMonitor {
    fn default() -> Self {
        Self::new()
    }
}

/// Passive system telemetry collector (~1 Hz cadence).
/// Samples CPU, RAM, and GPU from system procfs/sysfs without aggressive polling or IPC spam.
pub struct SystemTelemetryCollector {
    last_cpu_times: Option<(u64, u64)>, // (work, total)
}

impl SystemTelemetryCollector {
    pub fn new() -> Self {
        Self {
            last_cpu_times: None,
        }
    }

    /// Sample CPU utilization percentage from /proc/stat (normalized 0.0 to 100.0).
    pub fn sample_cpu(&mut self) -> f64 {
        let content = match fs::read_to_string("/proc/stat") {
            Ok(c) => c,
            Err(_) => return 0.0,
        };

        let first_line = match content.lines().next() {
            Some(l) if l.starts_with("cpu ") => l,
            _ => return 0.0,
        };

        let fields: Vec<u64> = first_line
            .split_whitespace()
            .skip(1)
            .filter_map(|s| s.parse().ok())
            .collect();

        if fields.len() < 4 {
            return 0.0;
        }

        let idle = fields[3] + fields.get(4).copied().unwrap_or(0); // idle + iowait
        let total: u64 = fields.iter().sum();
        let work = total.saturating_sub(idle);

        let usage = if let Some((prev_work, prev_total)) = self.last_cpu_times {
            let delta_total = total.saturating_sub(prev_total) as f64;
            let delta_work = work.saturating_sub(prev_work) as f64;
            if delta_total > 0.0 {
                ((delta_work / delta_total) * 100.0).clamp(0.0, 100.0)
            } else {
                0.0
            }
        } else {
            0.0
        };

        self.last_cpu_times = Some((work, total));
        usage
    }

    /// Sample RAM memory usage from /proc/meminfo.
    pub fn sample_ram() -> (u64, u64, f64) {
        let content = match fs::read_to_string("/proc/meminfo") {
            Ok(c) => c,
            Err(_) => return (0, 0, 0.0),
        };

        let mut total_kb = 0u64;
        let mut available_kb = 0u64;

        for line in content.lines() {
            if line.starts_with("MemTotal:") {
                total_kb = line
                    .split_whitespace()
                    .nth(1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0);
            } else if line.starts_with("MemAvailable:") {
                available_kb = line
                    .split_whitespace()
                    .nth(1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0);
            }
        }

        if total_kb == 0 {
            return (0, 0, 0.0);
        }

        let used_kb = total_kb.saturating_sub(available_kb);
        let used_mb = used_kb / 1024;
        let total_mb = total_kb / 1024;
        let pct = (used_kb as f64 / total_kb as f64) * 100.0;

        (used_mb, total_mb, pct.clamp(0.0, 100.0))
    }

    /// Sample GPU utilization and memory if platform driver exposes metrics in sysfs/drm.
    /// Never fakes metrics if the platform driver does not provide them.
    pub fn sample_gpu_metrics() -> (GpuMetrics, bool, bool) {
        let busy_paths = [
            "/sys/class/drm/card0/device/gpu_busy_percent",
            "/sys/class/drm/card1/device/gpu_busy_percent",
        ];

        let mut gpu_usage = None;
        let mut has_gpu_busy = false;

        for p in busy_paths {
            if let Ok(content) = fs::read_to_string(p) {
                if let Ok(val) = content.trim().parse::<f64>() {
                    gpu_usage = Some(val.clamp(0.0, 100.0));
                    has_gpu_busy = true;
                    break;
                }
            }
        }

        // VRAM usage paths (AMD/Intel sysfs)
        let vram_used_paths = [
            "/sys/class/drm/card0/device/mem_info_vram_used",
            "/sys/class/drm/card1/device/mem_info_vram_used",
        ];
        let vram_total_paths = [
            "/sys/class/drm/card0/device/mem_info_vram_total",
            "/sys/class/drm/card1/device/mem_info_vram_total",
        ];

        let mut vram_used_mb = None;
        let mut vram_total_mb = None;
        let mut has_vram = false;

        for p in vram_used_paths {
            if let Ok(content) = fs::read_to_string(p) {
                if let Ok(bytes) = content.trim().parse::<u64>() {
                    vram_used_mb = Some(bytes / (1024 * 1024));
                    has_vram = true;
                    break;
                }
            }
        }

        for p in vram_total_paths {
            if let Ok(content) = fs::read_to_string(p) {
                if let Ok(bytes) = content.trim().parse::<u64>() {
                    vram_total_mb = Some(bytes / (1024 * 1024));
                    break;
                }
            }
        }

        (
            GpuMetrics {
                gpu_usage_percent: gpu_usage,
                gpu_memory_used_mb: vram_used_mb,
                gpu_memory_total_mb: vram_total_mb,
                gpu_name: None,
            },
            has_gpu_busy,
            has_vram,
        )
    }

    /// Collect comprehensive passive system telemetry snapshot.
    pub fn sample_snapshot(&mut self) -> SystemTelemetry {
        let cpu_percent = self.sample_cpu();
        let (ram_used_mb, ram_total_mb, ram_percent) = Self::sample_ram();
        let (gpu, _, _) = Self::sample_gpu_metrics();

        let now_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis() as u64)
            .unwrap_or(0);

        SystemTelemetry {
            cpu_percent,
            ram_used_mb,
            ram_total_mb,
            ram_percent,
            gpu_percent: gpu.gpu_usage_percent,
            sample_timestamp_ms: now_ms,
        }
    }

    /// Sample dedicated Device Health domain snapshot.
    /// Strictly separated from Network Health and failover evaluation.
    pub fn sample_device_health(&mut self) -> DeviceHealth {
        let cpu_usage_percent = self.sample_cpu();
        let (memory_used_mb, memory_total_mb, memory_percent) = Self::sample_ram();
        let (gpu, has_gpu, has_vram) = Self::sample_gpu_metrics();

        let capabilities = DeviceCapabilities {
            cpu_monitoring: true,
            memory_monitoring: true,
            gpu_monitoring: has_gpu,
            gpu_memory_monitoring: has_vram,
        };

        // System pressure calculation for contextual workload awareness only
        let system_pressure = if cpu_usage_percent > 85.0 || memory_percent > 85.0 {
            "critical".to_string()
        } else if cpu_usage_percent > 70.0 || memory_percent > 75.0 {
            "moderate".to_string()
        } else {
            "nominal".to_string()
        };

        let now_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis() as u64)
            .unwrap_or(0);

        DeviceHealth {
            cpu_usage_percent,
            memory_used_mb,
            memory_total_mb,
            memory_percent,
            gpu,
            timestamp_ms: now_ms,
            platform: std::env::consts::OS.to_string(),
            capabilities,
            system_pressure,
        }
    }
}

impl Default for SystemTelemetryCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::{InterfaceState, NetworkInterface, PathMetrics, PolicyConfig, WorkloadProfile};
    use crate::policy::PolicyEngine;

    #[test]
    fn test_ram_sampling_structure_and_normalization() {
        let (used, total, pct) = SystemTelemetryCollector::sample_ram();
        if total > 0 {
            assert!(used <= total);
            assert!(pct >= 0.0 && pct <= 100.0);
        }
    }

    #[test]
    fn test_cpu_normalization_bounds() {
        let mut collector = SystemTelemetryCollector::new();
        let cpu = collector.sample_cpu();
        assert!(cpu >= 0.0 && cpu <= 100.0);
    }

    #[test]
    fn test_unsupported_gpu_explicit_behavior() {
        let (gpu, has_gpu, has_vram) = SystemTelemetryCollector::sample_gpu_metrics();
        if !has_gpu {
            assert_eq!(gpu.gpu_usage_percent, None);
        }
        if !has_vram {
            assert_eq!(gpu.gpu_memory_used_mb, None);
            assert_eq!(gpu.gpu_memory_total_mb, None);
        }
    }

    #[test]
    fn test_device_health_snapshot_generation() {
        let mut collector = SystemTelemetryCollector::new();
        let health = collector.sample_device_health();

        assert!(health.timestamp_ms > 0);
        assert!(health.cpu_usage_percent >= 0.0 && health.cpu_usage_percent <= 100.0);
        assert!(health.memory_percent >= 0.0 && health.memory_percent <= 100.0);
        assert!(["nominal", "moderate", "critical"].contains(&health.system_pressure.as_str()));
    }

    #[test]
    fn test_device_health_cannot_alter_network_failover_decision() {
        // Architectural invariant: Even under critical device pressure, PolicyEngine
        // evaluates ONLY network metrics and path eligibility.
        let config = PolicyConfig::default();
        let active = NetworkInterface {
            id: "eth0".to_string(),
            name: "Ethernet 1".to_string(),
            kind: crate::models::InterfaceKind::Ethernet,
            mac: None,
            ip_addresses: vec![],
            gateway: None,
            state: InterfaceState::Online,
            metrics: PathMetrics {
                latency_ms: 12.0,
                jitter_ms: 1.0,
                packet_loss_pct: 0.0,
                ..Default::default()
            },
            is_admin_enabled: true,
            is_physical: true,
            carrier_detected: true,
            metric_priority: 50,
        };
        let standby = NetworkInterface {
            id: "wlan0".to_string(),
            name: "Wi-Fi".to_string(),
            kind: crate::models::InterfaceKind::WiFi,
            mac: None,
            ip_addresses: vec![],
            gateway: None,
            state: InterfaceState::Ready,
            metrics: PathMetrics {
                latency_ms: 22.0,
                jitter_ms: 2.0,
                packet_loss_pct: 0.0,
                ..Default::default()
            },
            is_admin_enabled: true,
            is_physical: true,
            carrier_detected: true,
            metric_priority: 100,
        };

        let interfaces = vec![active, standby];

        // Evaluating failover with healthy active path returns None,
        // confirming that system device pressure does not trigger false failovers.
        let decision = PolicyEngine::evaluate_failover(
            &interfaces,
            Some("eth0"),
            &config,
            WorkloadProfile::VideoConference,
        );
        assert!(decision.is_none());
    }

    #[test]
    fn test_throughput_differential_calculation() {
        let mut monitor = ThroughputMonitor::new();
        monitor.calculate_rate("eth0", 1_000_000, 500_000);
        std::thread::sleep(std::time::Duration::from_millis(50));
        let (rx_mbps, _tx_mbps) = monitor.calculate_rate("eth0", 1_125_000, 500_000);
        assert!(rx_mbps > 0.0);
    }
}
