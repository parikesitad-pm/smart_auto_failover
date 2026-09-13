use serde::{Deserialize, Serialize};
use tokio::sync::broadcast;

use crate::models::{AuthoritativeState, DeviceHealth, FailoverEvent, NetworkInterface};

/// Strongly typed engine events broadcast to observers (Tauri shell, logger).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "payload")]
pub enum EngineEvent {
    BootstrapStarted,
    InterfaceDiscoveryStarted,
    InterfaceDiscovered(Vec<NetworkInterface>),
    ProbeInitializationStarted,
    HealthEvaluationStarted,
    NetworkStateReady(AuthoritativeState),
    StateUpdated(AuthoritativeState),
    StateChanged(AuthoritativeState),
    DeviceHealthUpdated(DeviceHealth),
    FailoverStarted {
        previous_id: String,
        target_id: String,
        reason: String,
    },
    FailoverCompleted {
        previous_id: String,
        target_id: String,
        active_verified: bool,
    },
    FailoverTriggered(FailoverEvent),
    RouteOperationFailed {
        interface_id: String,
        operation: String,
        error: String,
    },
    AdminActionRequired {
        interface_id: String,
        interface_name: String,
        reason: String,
    },
    NewDeviceDetected {
        interface_id: String,
        interface_name: String,
    },
    RecoveryStarted {
        interface_id: String,
    },
    RecoveryCompleted {
        interface_id: String,
    },
    InterfaceUpdated(NetworkInterface),
    BootstrapError(String),
}

/// Thread-safe event bus distributing engine state notifications.
#[derive(Clone)]
pub struct EventBus {
    sender: broadcast::Sender<EngineEvent>,
}

impl EventBus {
    pub fn new(capacity: usize) -> Self {
        let (sender, _) = broadcast::channel(capacity);
        Self { sender }
    }

    pub fn publish(&self, event: EngineEvent) {
        // Send ignores Err if no active listeners are currently subscribed
        let _ = self.sender.send(event);
    }

    pub fn subscribe(&self) -> broadcast::Receiver<EngineEvent> {
        self.sender.subscribe()
    }
}

impl Default for EventBus {
    fn default() -> Self {
        Self::new(128)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_device_health_event_serialization() {
        let health = DeviceHealth::default();
        let event = EngineEvent::DeviceHealthUpdated(health);

        let json = serde_json::to_string(&event).expect("serialize event");
        assert!(json.contains("DeviceHealthUpdated"));

        let deserialized: EngineEvent = serde_json::from_str(&json).expect("deserialize event");
        match deserialized {
            EngineEvent::DeviceHealthUpdated(h) => {
                assert_eq!(h.system_pressure, "nominal");
            }
            _ => panic!("Expected DeviceHealthUpdated variant"),
        }
    }
}
