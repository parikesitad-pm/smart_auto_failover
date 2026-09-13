use std::sync::Arc;
use tauri::State;
use rust_core::models::{AuthoritativeState, DeviceHealth, PolicyConfig, SpeedtestReport, SystemIdentity, SystemTelemetry};
use rust_core::AutoFailoverCore;


#[tauri::command]
pub async fn get_interface_state(
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<AuthoritativeState, String> {
    Ok(core.get_state().await)
}

#[tauri::command]
pub async fn enable_interface(
    id: String,
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<AuthoritativeState, String> {
    core.enable_interface(&id).await
}

#[tauri::command]
pub async fn disable_interface(
    id: String,
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<AuthoritativeState, String> {
    core.disable_interface(&id).await
}

#[tauri::command]
pub async fn request_policy_update(
    config: PolicyConfig,
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<AuthoritativeState, String> {
    Ok(core.update_policy_config(config).await)
}

#[tauri::command]
pub async fn force_core_reinit(
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<AuthoritativeState, String> {
    core.reinitialize().await
}

/// Re-run interface discovery after new device detection.
#[tauri::command]
pub async fn refresh_topology(
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<AuthoritativeState, String> {
    core.refresh_topology().await
}

/// Manual on-demand speedtest trigger.
/// Strictly isolated from continuous failover monitoring.
#[tauri::command]
pub async fn run_speedtest(
    interface_id: String,
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<SpeedtestReport, String> {
    Ok(core.run_manual_speedtest(&interface_id).await)
}

/// Query passive CPU/RAM/GPU telemetry sampled at ~1 Hz.
#[tauri::command]
pub async fn get_system_telemetry(
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<SystemTelemetry, String> {
    Ok(core.get_state().await.system_telemetry)
}

/// Query dedicated Device Health domain snapshot (~1 Hz).
#[tauri::command]
pub async fn get_device_health(
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<DeviceHealth, String> {
    Ok(core.get_device_health().await)
}

/// Query compact hardware and system identity for bootstrap presentation.
#[tauri::command]
pub async fn get_system_identity(
    core: State<'_, Arc<AutoFailoverCore>>,
) -> Result<SystemIdentity, String> {
    core.get_system_identity().await
}
