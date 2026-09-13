use std::sync::Arc;
use tauri::{AppHandle, Emitter};
use rust_core::AutoFailoverCore;
use tracing::{debug, error};

/// Spawn event bridge forwarding rust-core events to the frontend via Tauri event system.
pub fn spawn_event_bridge(app_handle: AppHandle, core: Arc<AutoFailoverCore>) {
    let mut receiver = core.event_bus().subscribe();

    tauri::async_runtime::spawn(async move {
        debug!("Tauri event bridge initialized");
        while let Ok(event) = receiver.recv().await {
            if let Err(e) = app_handle.emit("network-engine-event", &event) {
                error!("Failed to emit network-engine-event to frontend: {}", e);
            }
        }
    });
}
