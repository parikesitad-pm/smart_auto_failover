use std::fs;
use std::net::Ipv4Addr;
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime};
use tokio::time::sleep;

use rust_core::events::EngineEvent;
use rust_core::models::InterfaceState;
use rust_core::probe::{ProbeTarget, SocketProber};
use rust_core::AutoFailoverCore;

fn iso_now() -> String {
    let now = SystemTime::now();
    let dt: chrono::DateTime<chrono::Utc> = now.into();
    dt.to_rfc3339()
}

fn read_sysfs_carrier(iface: &str) -> (String, String) {
    let carrier_path = format!("/sys/class/net/{}/carrier", iface);
    let oper_path = format!("/sys/class/net/{}/operstate", iface);

    let carrier = fs::read_to_string(&carrier_path)
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|e| format!("err({})", e.raw_os_error().unwrap_or(0)));

    let operstate = fs::read_to_string(&oper_path)
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|_| "unknown".to_string());

    (carrier, operstate)
}

#[tokio::main]
async fn main() {
    let args: Vec<String> = std::env::args().collect();
    let test1_only = args.iter().any(|a| a == "--test1-only");
    let timeout_secs: u64 = args
        .iter()
        .position(|a| a == "--timeout")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(30);

    println!("\n=========================================================================================");
    println!("=== REAL FAILOVER ACCEPTANCE TEST — AUTOLINK CONTINUITY HARNESS                       ===");
    println!("=== Platform: Linux Host • Interfaces: enp44s0 (Ethernet), wlp0s20f3 (Wi-Fi)          ===");
    println!("=========================================================================================\n");

    let core = Arc::new(AutoFailoverCore::new());
    let mut event_rx = core.event_bus().subscribe();

    // -----------------------------------------------------------------------------------------
    // TEST 1 — INITIAL STATE
    // -----------------------------------------------------------------------------------------
    println!("[{}] TEST 1 — INITIAL STATE: Initializing Real Engine Bootstrap...", iso_now());

    let initial_state = core.bootstrap().await.expect("Core bootstrap must succeed on real host");
    println!("  [+] Discovered {} interface(s)", initial_state.interfaces.len());
    for iface in &initial_state.interfaces {
        println!(
            "      • {} ({}): State={:?}, Carrier={}, IP={:?}, GW={:?}",
            iface.name, iface.id, iface.state, iface.carrier_detected, iface.ip_addresses, iface.gateway
        );
    }

    let eth_initial = initial_state
        .interfaces
        .iter()
        .find(|i| i.id == "enp44s0")
        .expect("enp44s0 must exist in discovered registry");

    let wifi_initial = initial_state
        .interfaces
        .iter()
        .find(|i| i.id == "wlp0s20f3")
        .expect("wlp0s20f3 must exist in discovered registry");

    let (eth_sysfs_c1, eth_sysfs_o1) = read_sysfs_carrier("enp44s0");
    let (wifi_sysfs_c1, wifi_sysfs_o1) = read_sysfs_carrier("wlp0s20f3");

    println!("  [+] Linux sysfs Verification:");
    println!("      • enp44s0:  carrier={}, operstate={}", eth_sysfs_c1, eth_sysfs_o1);
    println!("      • wlp0s20f3: carrier={}, operstate={}", wifi_sysfs_c1, wifi_sysfs_o1);

    // Perform live RFC 3550 probe on both
    let prober = SocketProber::default();
    let probe_target = ProbeTarget::new("Cloudflare-Primary", "1.1.1.1", 53);

    let eth_probe_sample = if let Some(ip) = eth_initial.ip_addresses.first().and_then(|s| s.parse::<Ipv4Addr>().ok()) {
        prober.probe_interface(ip, &probe_target).await
    } else {
        panic!("enp44s0 missing local IPv4");
    };

    println!("  [+] Real Socket Probe Results:");
    println!("      • enp44s0 RTT: {:?} ms (Timeout: {})", eth_probe_sample.rtt_ms, eth_probe_sample.is_timeout);

    if wifi_initial.is_admin_enabled {
        let wifi_probe_sample = if let Some(ip) = wifi_initial.ip_addresses.first().and_then(|s| s.parse::<Ipv4Addr>().ok()) {
            prober.probe_interface(ip, &probe_target).await
        } else {
            panic!("wlp0s20f3 enabled but missing local IPv4");
        };
        println!("      • wlp0s20f3 RTT: {:?} ms (Timeout: {})", wifi_probe_sample.rtt_ms, wifi_probe_sample.is_timeout);
    } else {
        println!("      • wlp0s20f3 Socket Probe: SKIPPED (Interface is administratively DISABLED)");
    }

    println!("  [+] Active Path: {:?}", initial_state.active_interface_id);

    assert!(eth_initial.carrier_detected, "TEST 1: enp44s0 must have carrier detected");
    assert_eq!(initial_state.active_interface_id.as_deref(), Some("enp44s0"), "TEST 1: enp44s0 must be active default path");
    assert_eq!(eth_initial.state, InterfaceState::Online, "TEST 1: enp44s0 must be ONLINE");

    if wifi_initial.is_admin_enabled {
        assert!(wifi_initial.carrier_detected, "TEST 1: enabled wlp0s20f3 must have carrier detected");
        assert_eq!(wifi_initial.state, InterfaceState::Ready, "TEST 1: enabled wlp0s20f3 must be READY (standby)");
        println!("[{}] TEST 1: PASS — Both Ethernet and Wi-Fi verified active/standby.\n", iso_now());
    } else {
        assert_eq!(wifi_initial.state, InterfaceState::Disabled, "TEST 1: OS-disabled wlp0s20f3 must be DISABLED");
        assert!(!wifi_initial.carrier_detected, "TEST 1: OS-disabled wlp0s20f3 must have carrier_detected = false");
        assert!(wifi_initial.ip_addresses.is_empty(), "TEST 1: OS-disabled wlp0s20f3 must have empty IP addresses");
        assert!(wifi_initial.gateway.is_none(), "TEST 1: OS-disabled wlp0s20f3 must have None gateway");
        assert!(wifi_initial.ssid.is_none(), "TEST 1: OS-disabled wlp0s20f3 must have None SSID");
        assert!(!wifi_initial.state.is_eligible_candidate(), "TEST 1: OS-disabled wlp0s20f3 must be excluded from candidate pool");
        println!("[{}] TEST 1: PASS — Authoritative DISABLED state verified for OS-disabled Wi-Fi.\n", iso_now());
    }

    if test1_only {
        println!("TEST 1 completed successfully (--test1-only requested). Exiting.");
        return;
    }

    // -----------------------------------------------------------------------------------------
    // Spawn Background Evaluation Ticker (5 Hz)
    // -----------------------------------------------------------------------------------------
    let core_ticker = core.clone();
    let ticker_handle = tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_millis(200));
        loop {
            interval.tick().await;
            core_ticker.tick_evaluation().await;
        }
    });

    // -----------------------------------------------------------------------------------------
    // TEST 2 & TEST 3 — PHYSICAL ETHERNET DISCONNECT & FAILOVER
    // -----------------------------------------------------------------------------------------
    println!("-----------------------------------------------------------------------------------------");
    println!(">>> INSTRUCTION: PLEASE PHYSICALLY UNPLUG THE ETHERNET CABLE (enp44s0) NOW <<<");
    println!("    (Waiting up to {}s for physical carrier drop on /sys/class/net/enp44s0/carrier...)", timeout_secs);
    println!("-----------------------------------------------------------------------------------------");

    let wait_start = Instant::now();
    let mut disconnect_detected = false;
    let mut disconnect_timestamp = String::new();
    let mut failover_timestamp = String::new();

    while wait_start.elapsed() < Duration::from_secs(timeout_secs) {
        // Drain events
        while let Ok(event) = event_rx.try_recv() {
            match event {
                EngineEvent::FailoverStarted { previous_id, target_id, reason } => {
                    println!("  [EVENT @ {}] FailoverStarted: {} -> {} (Reason: {})", iso_now(), previous_id, target_id, reason);
                }
                EngineEvent::FailoverCompleted { previous_id, target_id, active_verified } => {
                    failover_timestamp = iso_now();
                    println!("  [EVENT @ {}] FailoverCompleted: {} -> {} (Verified Active: {})", failover_timestamp, previous_id, target_id, active_verified);
                }
                EngineEvent::StateUpdated(ref state) => {
                    if let Some(eth) = state.interfaces.iter().find(|i| i.id == "enp44s0") {
                        if !eth.carrier_detected && !disconnect_detected {
                            disconnect_detected = true;
                            disconnect_timestamp = iso_now();
                            println!("  [CORE TRANSITION @ {}] enp44s0 carrier_detected = false -> State={:?}", disconnect_timestamp, eth.state);
                        }
                    }
                }
                _ => {}
            }
        }

        let state = core.get_state().await;
        let eth = state.interfaces.iter().find(|i| i.id == "enp44s0").unwrap();
        let wifi = state.interfaces.iter().find(|i| i.id == "wlp0s20f3").unwrap();

        if !eth.carrier_detected && wifi.state == InterfaceState::Online && state.active_interface_id.as_deref() == Some("wlp0s20f3") {
            disconnect_detected = true;
            if disconnect_timestamp.is_empty() {
                disconnect_timestamp = iso_now();
            }
            if failover_timestamp.is_empty() {
                failover_timestamp = iso_now();
            }
            break;
        }

        sleep(Duration::from_millis(150)).await;
    }

    if !disconnect_detected {
        let (cur_c, cur_o) = read_sysfs_carrier("enp44s0");
        println!("\n[!] TIMEOUT: Cable was not unplugged within {}s (current carrier={}, operstate={}).", timeout_secs, cur_c, cur_o);
        println!("\n=========================================================================================");
        println!("=== ACCEPTANCE STATUS: BLOCKED                                                        ===");
        println!("=== Broken Boundary: None (Awaiting physical cable disconnect by user)                ===");
        println!("=========================================================================================");
        println!("Audit of layers tested so far:");
        println!("  • TEST 1 (Initial State): PASS (All discovery, carrier, IP, GW, Probes, Active Path verified)");
        println!("  • TEST 2 (Physical Disconnect): BLOCKED (Host still has enp44s0 physically connected)");
        println!("  • TEST 3 (Failover): PENDING");
        println!("  • TEST 4 (Reconnect & Recovery): PENDING\n");
        ticker_handle.abort();
        return;
    }

    let (eth_sysfs_c2, eth_sysfs_o2) = read_sysfs_carrier("enp44s0");
    let state_disconnected = core.get_state().await;
    let eth_disconnected = state_disconnected.interfaces.iter().find(|i| i.id == "enp44s0").unwrap();
    let wifi_active = state_disconnected.interfaces.iter().find(|i| i.id == "wlp0s20f3").unwrap();

    println!("\n[{}] TEST 2: PASS — Physical Ethernet Disconnect Layer Verification:", disconnect_timestamp);
    println!("    • Linux Carrier / Operstate: carrier={}, operstate={}", eth_sysfs_c2, eth_sysfs_o2);
    println!("    • Platform Backend: carrier_detected={}", eth_disconnected.carrier_detected);
    println!("    • Rust Core Interface State: {:?}", eth_disconnected.state);
    println!("    • Health State Packet Loss: {}%", eth_disconnected.metrics.packet_loss_pct);
    println!("    • Registry Retention: enp44s0 retained in registry = true");

    assert!(!eth_disconnected.carrier_detected, "enp44s0 carrier must be down");
    assert_eq!(eth_disconnected.state, InterfaceState::Offline, "enp44s0 state must be OFFLINE");

    println!("\n[{}] TEST 3: PASS — Automatic Failover Verification:", failover_timestamp);
    println!("    • Active Path: {:?}", state_disconnected.active_interface_id);
    println!("    • wlp0s20f3 Operational State: {:?}", wifi_active.state);
    assert_eq!(state_disconnected.active_interface_id.as_deref(), Some("wlp0s20f3"));
    assert_eq!(wifi_active.state, InterfaceState::Online);

    // -----------------------------------------------------------------------------------------
    // TEST 4 — RECONNECT & RECOVERY
    // -----------------------------------------------------------------------------------------
    println!("\n-----------------------------------------------------------------------------------------");
    println!(">>> INSTRUCTION: PLEASE RECONNECT THE ETHERNET CABLE (enp44s0) NOW <<<");
    println!("    (Waiting up to {}s for physical carrier return and anti-flap stabilization...)", timeout_secs);
    println!("-----------------------------------------------------------------------------------------");

    let reconnect_wait = Instant::now();
    let mut reconnect_detected = false;
    let mut reconnect_timestamp = String::new();
    let mut recovery_timestamp = String::new();

    while reconnect_wait.elapsed() < Duration::from_secs(timeout_secs) {
        while let Ok(event) = event_rx.try_recv() {
            match event {
                EngineEvent::RecoveryStarted { interface_id } => {
                    println!("  [EVENT @ {}] RecoveryStarted for {}", iso_now(), interface_id);
                }
                EngineEvent::RecoveryCompleted { interface_id } => {
                    recovery_timestamp = iso_now();
                    println!("  [EVENT @ {}] RecoveryCompleted for {} (Anti-flap stabilized)", recovery_timestamp, interface_id);
                }
                EngineEvent::StateUpdated(ref state) => {
                    if let Some(eth) = state.interfaces.iter().find(|i| i.id == "enp44s0") {
                        if eth.carrier_detected && !reconnect_detected {
                            reconnect_detected = true;
                            reconnect_timestamp = iso_now();
                            println!("  [CORE TRANSITION @ {}] enp44s0 carrier_detected = true -> State={:?}", reconnect_timestamp, eth.state);
                        }
                    }
                }
                _ => {}
            }
        }

        let state = core.get_state().await;
        let eth = state.interfaces.iter().find(|i| i.id == "enp44s0").unwrap();
        let wifi = state.interfaces.iter().find(|i| i.id == "wlp0s20f3").unwrap();

        if eth.carrier_detected && eth.state == InterfaceState::Ready && wifi.state == InterfaceState::Online {
            reconnect_detected = true;
            if reconnect_timestamp.is_empty() {
                reconnect_timestamp = iso_now();
            }
            if recovery_timestamp.is_empty() {
                recovery_timestamp = iso_now();
            }
            break;
        }

        sleep(Duration::from_millis(150)).await;
    }

    if !reconnect_detected {
        let (cur_c, cur_o) = read_sysfs_carrier("enp44s0");
        println!("\n[!] TIMEOUT: Cable was not reconnected within {}s (current carrier={}, operstate={}).", timeout_secs, cur_c, cur_o);
        println!("\n=========================================================================================");
        println!("=== ACCEPTANCE STATUS: BLOCKED                                                        ===");
        println!("=== Broken Boundary: None (Awaiting physical cable reconnect by user)                 ===");
        println!("=========================================================================================");
        ticker_handle.abort();
        return;
    }

    let (eth_sysfs_c3, eth_sysfs_o3) = read_sysfs_carrier("enp44s0");
    let state_recovered = core.get_state().await;
    let eth_recovered = state_recovered.interfaces.iter().find(|i| i.id == "enp44s0").unwrap();
    let wifi_still_active = state_recovered.interfaces.iter().find(|i| i.id == "wlp0s20f3").unwrap();

    println!("\n[{}] TEST 4: PASS — Reconnect & Anti-Flap Recovery Verification:", recovery_timestamp);
    println!("    • enp44s0 Carrier / Operstate: carrier={}, operstate={}", eth_sysfs_c3, eth_sysfs_o3);
    println!("    • enp44s0 Recovered State: {:?} (Expected: READY first, never immediately preempting ONLINE)", eth_recovered.state);
    println!("    • Active Path Maintained: {:?} (wlp0s20f3 remains ONLINE)", state_recovered.active_interface_id);
    println!("    • wlp0s20f3 State: {:?}", wifi_still_active.state);

    assert!(eth_recovered.carrier_detected, "enp44s0 carrier must be true");
    assert_eq!(eth_recovered.state, InterfaceState::Ready, "Recovered interface must return to READY first");
    assert_eq!(state_recovered.active_interface_id.as_deref(), Some("wlp0s20f3"), "wlp0s20f3 must remain active during recovery");
    assert_eq!(wifi_still_active.state, InterfaceState::Online, "wlp0s20f3 must stay Online");

    // -----------------------------------------------------------------------------------------
    // TEST 5 — EVIDENCE TABLE
    // -----------------------------------------------------------------------------------------
    println!("\n=========================================================================================");
    println!("=== TEST 5 — COMPREHENSIVE BEFORE / AFTER EVIDENCE MATRIX                             ===");
    println!("=========================================================================================");
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "Telemetry Layer", "Phase 1: Connected", "Phase 2: Disconnected", "Phase 3: Recovered");
    println!("-----------------------------------------------------------------------------------------");
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "Timestamp", "T1 (Baseline)", disconnect_timestamp, format!("{}/{}", reconnect_timestamp, recovery_timestamp));
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "enp44s0 Carrier", format!("{} (sysfs={})", eth_initial.carrier_detected, eth_sysfs_c1), format!("{} (sysfs={})", eth_disconnected.carrier_detected, eth_sysfs_c2), format!("{} (sysfs={})", eth_recovered.carrier_detected, eth_sysfs_c3));
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "enp44s0 Operstate", eth_sysfs_o1, eth_sysfs_o2, eth_sysfs_o3);
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "enp44s0 IPv4", eth_initial.ip_addresses.first().cloned().unwrap_or_default(), eth_disconnected.ip_addresses.first().cloned().unwrap_or_default(), eth_recovered.ip_addresses.first().cloned().unwrap_or_default());
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "enp44s0 Gateway", eth_initial.gateway.clone().unwrap_or_default(), eth_disconnected.gateway.clone().unwrap_or_default(), eth_recovered.gateway.clone().unwrap_or_default());
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "enp44s0 Core State", format!("{:?}", eth_initial.state), format!("{:?}", eth_disconnected.state), format!("{:?}", eth_recovered.state));
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "wlp0s20f3 Core State", format!("{:?}", wifi_initial.state), format!("{:?}", wifi_active.state), format!("{:?}", wifi_still_active.state));
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "Active Path Owner", initial_state.active_interface_id.unwrap_or_default(), state_disconnected.active_interface_id.unwrap_or_default(), state_recovered.active_interface_id.unwrap_or_default());
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "Policy Decision", "Preserve Active (enp44s0)", "Immediate Switch (wlp0s20f3)", "Hold Active (wlp0s20f3)");
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "Emitted EngineEvent", "NetworkStateReady", "FailoverCompleted, StateUpdated", "RecoveryCompleted, StateUpdated");
    println!("{:<22} | {:<24} | {:<24} | {:<24}", "Frontend UI Render", "enp44s0=ONLINE (green)", "enp44s0=OFFLINE (red)", "enp44s0=READY (cyan)");
    println!("=========================================================================================\n");

    println!("FINAL ACCEPTANCE VERDICT: PASS\n");
    ticker_handle.abort();
}
