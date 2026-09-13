#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

pub mod commands;
pub mod events;
pub mod ipc;

use std::sync::Arc;
use std::time::Duration;
use rust_core::AutoFailoverCore;
use tracing::info;

fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    info!("Initializing AutoFailover 3.0 Desktop Engine...");

    let core = Arc::new(AutoFailoverCore::new());
    let core_for_ticker = core.clone();
    let core_for_telemetry = core.clone();
    let core_for_topology = core.clone();

    tauri::Builder::default()
        .manage(core.clone())
        .invoke_handler(tauri::generate_handler![
            commands::get_interface_state,
            commands::enable_interface,
            commands::disable_interface,
            commands::request_policy_update,
            commands::force_core_reinit,
            commands::refresh_topology,
            commands::run_speedtest,
            commands::get_system_telemetry,
            commands::get_device_health,
            commands::get_system_identity,
            commands::core_handshake,
        ])
        .setup(move |app| {
            let app_handle = app.handle().clone();

            // 1. Spawn event bridge streaming events from core to frontend
            events::spawn_event_bridge(app_handle, core.clone());

            // 2. Trigger non-blocking asynchronous core bootstrap
            let core_for_bootstrap = core.clone();
            tauri::async_runtime::spawn(async move {
                let _ = core_for_bootstrap.bootstrap().await;
            });

            // 3. Primary network health & policy evaluation ticker at 5 Hz (200ms)
            // Evaluates link health, EWMA scoring, and failover triggers
            tauri::async_runtime::spawn(async move {
                let mut interval = tokio::time::interval(Duration::from_millis(200));
                loop {
                    interval.tick().await;
                    core_for_ticker.tick_evaluation().await;
                }
            });

            // 4. Passive device health & system telemetry ticker at ~1 Hz (1000ms)
            // Non-blocking sampling of CPU, RAM, and GPU from system counters
            tauri::async_runtime::spawn(async move {
                let mut interval = tokio::time::interval(Duration::from_millis(1000));
                loop {
                    interval.tick().await;
                    core_for_telemetry.tick_device_health().await;
                }
            });

            // 5. Periodic hardware topology detector at 0.5 Hz (2000ms)
            // Detects newly attached network devices without silently modifying visible UI
            tauri::async_runtime::spawn(async move {
                let mut interval = tokio::time::interval(Duration::from_millis(2000));
                loop {
                    interval.tick().await;
                    core_for_topology.check_topology_changes().await;
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running AutoFailover 3.0 desktop application");
}
