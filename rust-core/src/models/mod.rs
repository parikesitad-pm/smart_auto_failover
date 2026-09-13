use serde::{Deserialize, Serialize};

/// High-level operational state of a network interface.
/// Distinct state model per Master Prompt §7.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum InterfaceState {
    /// Currently active default outbound path carrying production traffic.
    Online,
    /// Physically detected, healthy carrier, validated and available as standby failover candidate.
    Ready,
    /// Detected but experiencing degradation (high jitter/latency/packet loss).
    Alert,
    /// Physical link lost or disconnected cable.
    Offline,
    /// Administratively disabled at OS level (excluded from eligible pool unless enabled by user).
    Disabled,
}

impl InterfaceState {
    pub fn is_eligible_candidate(&self) -> bool {
        matches!(self, InterfaceState::Ready | InterfaceState::Alert)
    }
}

/// Physical or virtual medium category.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum InterfaceKind {
    Ethernet,
    WiFi,
    Cellular,
    Virtual,
    Unknown,
}

/// Latency, jitter, and throughput metrics.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PathMetrics {
    pub latency_ms: f64,
    /// Statistical jitter calculated according to IETF RFC 3550.
    pub jitter_ms: f64,
    pub packet_loss_pct: f64,
    pub download_mbps: f64,
    pub upload_mbps: f64,
    pub ewma_score: f64,
    pub consecutive_drops: u32,
}

impl Default for PathMetrics {
    fn default() -> Self {
        Self {
            latency_ms: 0.0,
            jitter_ms: 0.0,
            packet_loss_pct: 0.0,
            download_mbps: 0.0,
            upload_mbps: 0.0,
            ewma_score: 100.0,
            consecutive_drops: 0,
        }
    }
}

/// Fully qualified network adapter profile.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub id: String,
    pub name: String,
    pub kind: InterfaceKind,
    pub mac: Option<String>,
    pub ip_addresses: Vec<String>,
    pub gateway: Option<String>,
    pub state: InterfaceState,
    pub metrics: PathMetrics,
    pub is_admin_enabled: bool,
    pub is_physical: bool,
    pub carrier_detected: bool,
    pub metric_priority: u32,
}

/// Multi-metric scoring formula weights and takeover anti-flap thresholds.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PolicyConfig {
    /// Takeover margin required for normal healthy candidate takeover:
    /// `candidate_score >= active_score + takeover_margin`
    pub takeover_margin: f64,
    pub latency_alert_threshold_ms: f64,
    pub jitter_alert_threshold_ms: f64,
    pub packet_loss_alert_threshold_pct: f64,
    pub hard_down_timeout_ms: u64,
    pub preferred_interface_id: Option<String>,
}

impl Default for PolicyConfig {
    fn default() -> Self {
        Self {
            takeover_margin: 15.0,
            latency_alert_threshold_ms: 85.0,
            jitter_alert_threshold_ms: 12.0,
            packet_loss_alert_threshold_pct: 2.0,
            hard_down_timeout_ms: 1500,
            preferred_interface_id: Some("eth0".to_string()),
        }
    }
}

/// Active workload sensitivity profile.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum WorkloadProfile {
    General,
    VideoConference,
    LiveProduction,
    Custom,
}

impl Default for WorkloadProfile {
    fn default() -> Self {
        WorkloadProfile::VideoConference
    }
}

/// Decomposed scoring evaluation result.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CandidateScore {
    pub interface_id: String,
    pub total_score: f64,
    pub latency_score: f64,
    pub jitter_score: f64,
    pub loss_penalty: f64,
    pub preference_bonus: f64,
}

/// Failover transition record.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FailoverEvent {
    pub timestamp_ms: u64,
    pub previous_interface_id: String,
    pub new_interface_id: String,
    pub reason: String,
    pub previous_score: f64,
    pub new_score: f64,
}

/// Passive system load indicators sampled at low frequency (~1 Hz).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SystemTelemetry {
    pub cpu_percent: f64,
    pub ram_used_mb: u64,
    pub ram_total_mb: u64,
    pub ram_percent: f64,
    pub gpu_percent: Option<f64>,
    pub sample_timestamp_ms: u64,
}

impl Default for SystemTelemetry {
    fn default() -> Self {
        Self {
            cpu_percent: 0.0,
            ram_used_mb: 0,
            ram_total_mb: 0,
            ram_percent: 0.0,
            gpu_percent: None,
            sample_timestamp_ms: 0,
        }
    }
}

/// On-demand isolated speedtest measurement report.
/// Strictly non-authoritative: NEVER directly factored into failover decision scoring.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SpeedtestReport {
    pub test_id: String,
    pub interface_id: String,
    pub download_mbps: f64,
    pub upload_mbps: f64,
    pub ping_ms: f64,
    pub timestamp_ms: u64,
    pub deferred_due_to_workload: bool,
}

/// Hardware telemetry capability flags indicating which metrics the platform supports.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DeviceCapabilities {
    pub cpu_monitoring: bool,
    pub memory_monitoring: bool,
    pub gpu_monitoring: bool,
    pub gpu_memory_monitoring: bool,
}

impl Default for DeviceCapabilities {
    fn default() -> Self {
        Self {
            cpu_monitoring: true,
            memory_monitoring: true,
            gpu_monitoring: false,
            gpu_memory_monitoring: false,
        }
    }
}

/// GPU telemetry metrics.
/// All fields are Option to explicitly represent unsupported capabilities without faking metrics.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct GpuMetrics {
    pub gpu_usage_percent: Option<f64>,
    pub gpu_memory_used_mb: Option<u64>,
    pub gpu_memory_total_mb: Option<u64>,
    pub gpu_name: Option<String>,
}

/// Dedicated Device Health domain model.
/// Strictly decoupled from Network Health scoring and failover arbitration.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DeviceHealth {
    pub cpu_usage_percent: f64,
    pub memory_used_mb: u64,
    pub memory_total_mb: u64,
    pub memory_percent: f64,
    pub gpu: GpuMetrics,
    pub timestamp_ms: u64,
    pub platform: String,
    pub capabilities: DeviceCapabilities,
    /// System pressure level computed for workload awareness (nominal, moderate, critical).
    /// NEVER triggers network failover.
    pub system_pressure: String,
}

impl Default for DeviceHealth {
    fn default() -> Self {
        Self {
            cpu_usage_percent: 0.0,
            memory_used_mb: 0,
            memory_total_mb: 0,
            memory_percent: 0.0,
            gpu: GpuMetrics::default(),
            timestamp_ms: 0,
            platform: std::env::consts::OS.to_string(),
            capabilities: DeviceCapabilities::default(),
            system_pressure: "nominal".to_string(),
        }
    }
}

/// Authoritative runtime state published to observers.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AuthoritativeState {
    pub interfaces: Vec<NetworkInterface>,
    pub active_interface_id: Option<String>,
    pub overall_health_index: u32,
    pub workload_profile: WorkloadProfile,
    pub policy_config: PolicyConfig,
    pub last_failover: Option<FailoverEvent>,
    pub system_telemetry: SystemTelemetry,
    pub device_health: DeviceHealth,
    pub last_speedtest: Option<SpeedtestReport>,
    pub timestamp_ms: u64,
}

/// Compact hardware and system identity for fast bootstrap presentation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SystemIdentity {
    pub device_name: String,
    pub os_name: String,
    pub architecture: String,
    pub kernel_or_version: String,
    pub total_interfaces_detected: usize,
    pub active_connection: Option<String>,
}

/// Interface network details including IPv4 addresses and gateway.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct InterfaceNetworkInfo {
    pub name: String,
    pub ip_addresses: Vec<String>,
    pub gateway: Option<String>,
    pub metric: Option<u32>,
}
