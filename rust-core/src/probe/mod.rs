use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::net::{IpAddr, Ipv4Addr, SocketAddr};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::net::UdpSocket;
use tracing::debug;

/// Explicit, configurable probe target
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ProbeTarget {
    pub id: String,
    pub host: String,
    pub port: u16,
}

impl ProbeTarget {
    pub fn new(id: &str, host: &str, port: u16) -> Self {
        Self {
            id: id.to_string(),
            host: host.to_string(),
            port,
        }
    }

    pub fn default_targets() -> Vec<Self> {
        vec![
            Self::new("cloudflare", "1.1.1.1", 53),
            Self::new("google", "8.8.8.8", 53),
            Self::new("quad9", "9.9.9.9", 53),
        ]
    }
}

/// Recorded outcome of an active interface probe.
/// Distinguishes between successful responses, timeouts (RTO), and socket bind/network errors.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProbeSample {
    pub target_id: String,
    pub rtt_ms: Option<f64>,
    pub is_timeout: bool,
    pub error: Option<String>,
    pub timestamp_ms: u64,
}

/// RFC 3550 Jitter Calculator
/// Standard formulation: J(i) = J(i-1) + (|D(i-1, i)| - J(i-1)) / 16.0
#[derive(Debug, Clone)]
pub struct Rfc3550JitterEstimator {
    jitter: f64,
    last_transit: Option<f64>,
}

impl Rfc3550JitterEstimator {
    pub fn new() -> Self {
        Self {
            jitter: 0.0,
            last_transit: None,
        }
    }

    /// Update jitter with a new observed round-trip / transit time measurement in milliseconds.
    pub fn sample(&mut self, transit_ms: f64) -> f64 {
        if let Some(prev_transit) = self.last_transit {
            let d = (transit_ms - prev_transit).abs();
            self.jitter += (d - self.jitter) / 16.0;
        }
        self.last_transit = Some(transit_ms);
        self.jitter
    }

    pub fn current_jitter(&self) -> f64 {
        self.jitter
    }

    pub fn reset(&mut self) {
        self.jitter = 0.0;
        self.last_transit = None;
    }
}

impl Default for Rfc3550JitterEstimator {
    fn default() -> Self {
        Self::new()
    }
}

/// Real UDP socket prober bound to a specific local interface IP address.
/// Uses minimal standard DNS queries with strict bounded timeouts and retries.
pub struct SocketProber {
    timeout: Duration,
    retry_limit: u32,
}

impl SocketProber {
    pub fn new(timeout_ms: u64, retry_limit: u32) -> Self {
        Self {
            timeout: Duration::from_millis(timeout_ms),
            retry_limit,
        }
    }

    fn current_timestamp_ms() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_millis() as u64)
            .unwrap_or(0)
    }

    /// Build standard 17-byte DNS root query (query '.' for type A)
    fn build_dns_query() -> [u8; 17] {
        [
            0xaf, 0x01, // Transaction ID
            0x01, 0x00, // Flags: Standard query, recursion desired
            0x00, 0x01, // Questions: 1
            0x00, 0x00, // Answer RRs: 0
            0x00, 0x00, // Authority RRs: 0
            0x00, 0x00, // Additional RRs: 0
            0x00,       // Name: root (.)
            0x00, 0x01, // Type: A (1)
            0x00, 0x01, // Class: IN (1)
        ]
    }

    /// Perform asynchronous UDP probe strictly bound to local interface IP.
    pub async fn probe_interface(
        &self,
        local_ip: Ipv4Addr,
        target: &ProbeTarget,
    ) -> ProbeSample {
        let target_ip: IpAddr = match target.host.parse() {
            Ok(ip) => ip,
            Err(e) => {
                return ProbeSample {
                    target_id: target.id.clone(),
                    rtt_ms: None,
                    is_timeout: false,
                    error: Some(format!("Invalid target host IP '{}': {}", target.host, e)),
                    timestamp_ms: Self::current_timestamp_ms(),
                };
            }
        };

        let target_addr = SocketAddr::new(target_ip, target.port);
        let bind_addr = SocketAddr::new(IpAddr::V4(local_ip), 0);

        let mut attempts = 0;
        let query = Self::build_dns_query();
        let mut buf = [0u8; 512];

        while attempts <= self.retry_limit {
            attempts += 1;

            let socket = match UdpSocket::bind(bind_addr).await {
                Ok(s) => s,
                Err(e) => {
                    return ProbeSample {
                        target_id: target.id.clone(),
                        rtt_ms: None,
                        is_timeout: false,
                        error: Some(format!("Socket bind to {} failed: {}", bind_addr, e)),
                        timestamp_ms: Self::current_timestamp_ms(),
                    };
                }
            };

            let start = Instant::now();
            if let Err(e) = socket.send_to(&query, target_addr).await {
                debug!("Probe send_to {} failed: {}", target_addr, e);
                continue;
            }

            match tokio::time::timeout(self.timeout, socket.recv_from(&mut buf)).await {
                Ok(Ok((bytes_read, _from))) if bytes_read >= 12 => {
                    let rtt = start.elapsed().as_secs_f64() * 1000.0;
                    return ProbeSample {
                        target_id: target.id.clone(),
                        rtt_ms: Some(rtt),
                        is_timeout: false,
                        error: None,
                        timestamp_ms: Self::current_timestamp_ms(),
                    };
                }
                Ok(Ok(_)) => {
                    // Truncated packet
                    continue;
                }
                Ok(Err(e)) => {
                    debug!("Probe recv_from {} error: {}", target_addr, e);
                    continue;
                }
                Err(_) => {
                    // Explicit Timeout (RTO)
                    debug!("Probe to {} timed out after {:?}", target_addr, self.timeout);
                }
            }
        }

        ProbeSample {
            target_id: target.id.clone(),
            rtt_ms: None,
            is_timeout: true,
            error: Some(format!("Probe timed out after {} attempts", attempts)),
            timestamp_ms: Self::current_timestamp_ms(),
        }
    }
}

impl Default for SocketProber {
    fn default() -> Self {
        Self::new(400, 1) // 400ms timeout, 1 retry
    }
}

/// Rolling window metric collector for path quality
#[derive(Debug, Clone)]
pub struct RollingPathProbe {
    pub interface_id: String,
    jitter_estimator: Rfc3550JitterEstimator,
    recent_latencies: VecDeque<f64>,
    recent_packets: VecDeque<bool>, // true = success, false = dropped / timeout
    window_size: usize,
    last_probe_time: Option<Instant>,
    last_sample_rtt: Option<f64>,
}

impl RollingPathProbe {
    pub fn new(interface_id: String, window_size: usize) -> Self {
        Self {
            interface_id,
            jitter_estimator: Rfc3550JitterEstimator::new(),
            recent_latencies: VecDeque::with_capacity(window_size),
            recent_packets: VecDeque::with_capacity(window_size),
            window_size,
            last_probe_time: None,
            last_sample_rtt: None,
        }
    }

    pub fn record_sample(&mut self, latency_ms: Option<f64>) {
        self.last_sample_rtt = latency_ms;
        if let Some(lat) = latency_ms {
            self.jitter_estimator.sample(lat);
            if self.recent_latencies.len() >= self.window_size {
                self.recent_latencies.pop_front();
            }
            self.recent_latencies.push_back(lat);

            if self.recent_packets.len() >= self.window_size {
                self.recent_packets.pop_front();
            }
            self.recent_packets.push_back(true);
        } else {
            // Packet loss or timeout
            if self.recent_packets.len() >= self.window_size {
                self.recent_packets.pop_front();
            }
            self.recent_packets.push_back(false);
        }
        self.last_probe_time = Some(Instant::now());
    }

    pub fn average_latency(&self) -> f64 {
        if self.recent_latencies.is_empty() {
            return 0.0;
        }
        let sum: f64 = self.recent_latencies.iter().sum();
        sum / self.recent_latencies.len() as f64
    }

    pub fn current_jitter(&self) -> f64 {
        self.jitter_estimator.current_jitter()
    }

    pub fn packet_loss_pct(&self) -> f64 {
        if self.recent_packets.is_empty() {
            return 0.0;
        }
        let dropped = self.recent_packets.iter().filter(|&&ok| !ok).count();
        (dropped as f64 / self.recent_packets.len() as f64) * 100.0
    }

    pub fn last_sample(&self) -> Option<f64> {
        self.last_sample_rtt
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rfc3550_jitter_calculation() {
        let mut estimator = Rfc3550JitterEstimator::new();
        assert_eq!(estimator.current_jitter(), 0.0);

        // First sample initializes last_transit
        estimator.sample(20.0);
        assert_eq!(estimator.current_jitter(), 0.0);

        // Transit difference = |28 - 20| = 8.0. J = 0 + (8.0 - 0)/16 = 0.5
        let j1 = estimator.sample(28.0);
        assert!((j1 - 0.5).abs() < 1e-6);

        // Transit difference = |24 - 28| = 4.0. J = 0.5 + (4.0 - 0.5)/16 = 0.5 + 0.21875 = 0.71875
        let j2 = estimator.sample(24.0);
        assert!((j2 - 0.71875).abs() < 1e-6);
    }

    #[test]
    fn test_rolling_path_probe_metrics() {
        let mut probe = RollingPathProbe::new("eth0".to_string(), 10);
        probe.record_sample(Some(10.0));
        probe.record_sample(Some(12.0));
        probe.record_sample(None); // 1 drop out of 3 = 33.33%
        assert!((probe.packet_loss_pct() - 33.33).abs() < 0.1);
        assert!((probe.average_latency() - 11.0).abs() < 1e-6);
    }

    #[tokio::test]
    async fn test_probe_timeout_distinction() {
        let prober = SocketProber::new(10, 0); // 10ms timeout to unroutable IP
        let target = ProbeTarget::new("unroutable", "192.0.2.1", 53); // RFC 5737 TEST-NET-1 (unroutable)
        let sample = prober.probe_interface(Ipv4Addr::new(127, 0, 0, 1), &target).await;

        assert!(sample.is_timeout);
        assert!(sample.rtt_ms.is_none());
        assert_eq!(sample.target_id, "unroutable");
    }

    #[tokio::test]
    async fn test_invalid_target_error_handling() {
        let prober = SocketProber::new(50, 0);
        let target = ProbeTarget::new("bad_host", "999.999.999.999", 53);
        let sample = prober.probe_interface(Ipv4Addr::new(127, 0, 0, 1), &target).await;

        assert!(sample.rtt_ms.is_none());
        assert!(sample.error.is_some());
    }
}
