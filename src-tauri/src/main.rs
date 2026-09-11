// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub id: String,
    pub name: String,
    pub carrier: String,
    pub media_type: String,
    pub enabled: bool,
    pub state: String,
    pub latency: f64,
    pub jitter: f64,
    pub score: f64,
    pub bg_probing_score: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PolicyConfig {
    pub takeover_margin: f64,
    pub rfc3550_weight: f64,
    pub latency_weight: f64,
    pub workload_profile: String,
}

#[tauri::command]
fn enable_interface(id: String) -> Result<(), String> {
    println!("[IPC Core] enable_interface called for: {}", id);
    // Platform-specific enable -> verify operational state -> admit to READY pool
    Ok(())
}

#[tauri::command]
fn disable_interface(id: String) -> Result<(), String> {
    println!("[IPC Core] disable_interface called for: {}", id);
    // Platform-specific disable -> exclude from eligible candidates
    Ok(())
}

#[tauri::command]
fn request_policy_update(config: PolicyConfig) -> Result<(), String> {
    println!("[IPC Core] request_policy_update: {:?}", config);
    Ok(())
}

#[tauri::command]
fn get_interface_state() -> Result<Vec<NetworkInterface>, String> {
    Ok(vec![
        NetworkInterface {
            id: "eth1".into(),
            name: "Ethernet 1".into(),
            carrier: "Active 1Gbps".into(),
            media_type: "ethernet".into(),
            enabled: true,
            state: "ONLINE".into(),
            latency: 8.2,
            jitter: 1.2,
            score: 98.4,
            bg_probing_score: 98.4,
        },
        NetworkInterface {
            id: "eth2".into(),
            name: "ETH 2 (Docking)".into(),
            carrier: "Active 1Gbps".into(),
            media_type: "ethernet".into(),
            enabled: true,
            state: "READY".into(),
            latency: 14.1,
            jitter: 1.5,
            score: 89.2,
            bg_probing_score: 89.2,
        },
        NetworkInterface {
            id: "wifi".into(),
            name: "Wi-Fi 6".into(),
            carrier: "SSID: Studio_5G".into(),
            media_type: "wifi".into(),
            enabled: true,
            state: "READY".into(),
            latency: 26.8,
            jitter: 3.4,
            score: 76.5,
            bg_probing_score: 76.5,
        },
        NetworkInterface {
            id: "usb".into(),
            name: "USB 5G Modem".into(),
            carrier: "Modem: LTE/5G High".into(),
            media_type: "cellular".into(),
            enabled: true,
            state: "READY".into(),
            latency: 61.4,
            jitter: 8.9,
            score: 54.0,
            bg_probing_score: 54.0,
        },
    ])
}

#[tauri::command]
fn force_core_reinit() -> Result<(), String> {
    println!("[IPC Core] force_core_reinit: Hardware rescan initiated.");
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            enable_interface,
            disable_interface,
            request_policy_update,
            get_interface_state,
            force_core_reinit
        ])
        .run(tauri::generate_context!())
        .expect("error while running AutoFailover 3.0 application");
}
