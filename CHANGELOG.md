# Changelog

All notable changes to **AutoFailover by Modula** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 3.0.0

### Added

- **Multi-OS Usage Guide & Instrument Cluster AutoFailover 3.0 Documentation**: Expanded `README.md` with complete installation, permission setup, build, and execution instructions for Windows (WebView2 & Administrator routing), macOS (Apple Silicon M1-M4 & Intel with BSD route privileges), and Linux (WebKitGTK 4.1 & `CAP_NET_ADMIN` / sudo capabilities). Added comprehensive usage instructions for the standalone **Instrument Cluster AutoFailover 3.0** (formerly Cockpit Widget), available via `http://localhost:3000/instrument_cluster_autofailover_3_0.html` and direct static HTML `frontend/public/instrument_cluster_autofailover_3_0.html`.
- **Product Positioning & Hierarchy Alignment**: Updated primary user-facing positioning to _"Navigate Your Internet Pipeline to Keep You Online"_ with supporting line _"Through Video Conference & Livestreaming Production"_ and tagline _"light seamless and usefull"_, removing _"Digital Network Cockpit"_ from all user-facing descriptions.
- **Progressive Real Splash Sequence**: Enhanced startup splash with honest step-by-step disclosure (`SYSTEM INITIALIZATION` → Device detected → OS detected → Architecture detected → Network interfaces discovered → Interface network details detected → Probe initialization → Initial health evaluation → Initial active path determined → `SYSTEM READY` → Cockpit).
- **Detailed Interface Discovery Cards**: Discovered interfaces now show Type, Admin State, Link State, IPv4 address, Netmask, Gateway, SSID (Wi-Fi), and Link Speed with explicit "N/A" for unsupported properties.
- **Post-Startup Device Detection Notification**: Aligned notification copy to _"New network device detected. Refresh to add it to the interface list."_ with action button `[ Refresh ]`.

### Fixed

- **Tauri 2 IPC Bridge & Authoritative State Synchronization**: Resolved critical issue where frontend was running on `@tauri-apps/api@1.6.0` checking legacy `window.__TAURI_IPC__`, causing the native Linux desktop app to silently fall back into browser mock simulation mode with hardcoded fake interfaces, frozen throughput, and synthetic `Math.random()` jitter intervals. Upgraded to `@tauri-apps/api@^2.11.1`, configured `src-tauri/capabilities/default.json`, completely removed synthetic telemetry intervals and hardcoded baseline fallback interfaces, and wired live Tauri 2 IPC events (`network-engine-event`) directly to authoritative `AuthoritativeState`.
- **Authoritative NO-USABLE-PATH State**: When zero usable paths exist (e.g. Ethernet disconnected and Wi-Fi disabled), Cockpit Header renders a crimson `NO CONNECTION • NO USABLE PATH` master status pill, Center Dial displays `--` and `NO CONNECTION` with `N/A` for latency and RFC 3550 jitter, and download/upload throughput drop cleanly to `0.0 Mbps`.
- **Dynamic Netmask & Link Speed Reporting**: Implemented dynamic netmask calculation from CIDR prefixes and real link speed extraction from Linux sysfs (`/sys/class/net/<dev>/speed`) across `rust-core` HAL and the React Interface Deck.
- **Interface Card Compact Network Details Matrix**: Upgraded Interface Deck cards to display a 2-column live addressing grid: IPv4 address, Gateway, Netmask, Link speed, Latency, RFC 3550 Jitter, Health Score, and SSID (for Wi-Fi), with explicit `—` fallbacks when disabled or offline.
- **OS-Disabled Wi-Fi Adapter State Reflection**: Resolved critical bug where Wi-Fi administratively disabled from the OS (`IFF_UP` cleared) continued to appear as `READY` with stale IP address, gateway, and hardcoded SSID (`www.d-rvc.com`). The platform HAL now monitors interface administrative flags (`/sys/class/net/<dev>/flags` bit 0x1) and carrier state on every evaluation tick via `query_dynamic_details()`, actively transitions OS-disabled adapters to authoritative `DISABLED` state, clears all stale IP addresses, gateway, and SSID, and resets metrics to zero. `PolicyEngine` strictly excludes `DISABLED` adapters from candidate selection and triggers immediate failover if an active interface is disabled. The frontend Interface Deck, normalizers, and startup sequences now strictly display authoritative `DISABLED` badges with blanked metrics (`-- ms`) and cleared SSIDs.
- **Physical Link Disconnect and Recovery State Propagation**: Fixed end-to-end pipeline where physical Ethernet disconnect (`carrier == 0` / `operstate == down`) was not updating the application state. Rust Core now actively polls platform link carrier at 5 Hz (`check_carrier` combining Linux `operstate` and `carrier` sysfs attributes), immediately transitions disconnected links to `OFFLINE` (100% packet loss), triggers instant policy-driven failover, and emits `StateUpdated` via Tauri IPC. The frontend normalizer maps `carrier_detected` and `is_admin_enabled` to adapter status, rendering a distinct crimson `OFFLINE` badge (distinct from administrative `DISABLED`). On cable reconnect, link recovery enters `RecoveryArbiter` anti-flap stabilization before transitioning to `READY` standby (never preempting the active route).
- **UnswitchingPlatform Test Mock**: Resolved field name mismatch (`active_route`) in `rust-core/src/failover/mod.rs` unit test, restoring 100% passing test suite across all 43 workspace tests.

- **Real Failover Runtime & Host Subsystem Verification**: Completed authoritative failover and recovery runtime in `rust-core` with platform-backed Layer-3 routing table operations, strict pre-flight state/carrier/IP/gateway validation, post-flight routing table verification, policy-driven recovery (`READY` first via `RecoveryArbiter` anti-flap cooldown before reclaim evaluation), and comprehensive Linux real-host subsystem verification (`PASS` on Discovery, Probe, Route, Failover, Recovery).
- **Bootstrap System Identification & Network Readiness Gate**: Implemented platform-agnostic `get_system_identity()` in `rust-core` HAL reading native hardware product name, OS release, CPU architecture, kernel, and active interface. Splash Screen now renders a compact Fastfetch-inspired native system summary card, dynamic interface discovery checklist, and enforces `SYSTEM READY` gating before revealing the Cockpit.
- **Bounded Queue Live-Test Policy**: Established sequential bounded job queue runner (`test_real_linux_live_discovery_and_probing`) in `rust-core/tests/runtime_scenarios.rs` for live network interface testing (`enp44s0` and `wlp0s20f3`) enforcing a 1500ms timeout limit per job with explicit result classification (`PASS`, `FAIL`, `TIMEOUT`, `CANCELLED`, `UNSUPPORTED`).
- **Digital Network Cockpit**: Minimal high-contrast automotive cluster dashboard UI with custom SVG dials and 60 FPS client-side lerping.
- **Score-Based Policy Engine**: Multi-metric candidate evaluation formula (`candidate_score >= active_score + takeover_margin`) factoring inverted latency, jitter (RFC 3550), packet loss, and stability.
- **Dynamic Interface Discovery**: Real-time hotplug detection displaying only connected hardware interfaces (zero phantom ports).
- **Workload Awareness Engine**: Passive background process detection for conferencing and streaming tools (Zoom, OBS, vMix, Teams, Meet, Webex) informing route QoS priority.
- **Tauri + Rust + React & TypeScript Architecture**: Baseline native desktop orchestrator with atomic typed components and zero runtime bloat.
- **UI / Core Authority Model Separation**: Strict boundary established where UI only renders state and observes engine events. Rust Core retains 100% authority over probing, scoring, routing, and failover execution.
- **Session Continuity & Active Workload Protection**: Core goal redefined to protect real-time active sessions (Zoom, Teams, OBS, vMix) with early degradation detection, anti-flap noise dampening, and the 7-step failure priority order.
- **Realistic Continuity Engineering Standard**: Replaced unmeasured absolute zero-drop claims with measured session disruption minimization.
- **Administrative Action Protocol & Atomic IPC**: Explicit administrative confirmation required for disabled adapters ("Enable it for automatic failover?"), with atomic `enable_interface()` commands that admit adapters into the candidate pool without forcing ONLINE. Never silently re-enables user-disabled links.
- **Intentional Splash Screen & Tuyul Sport Car Departure**: Decoupled network engine initialization (runs at maximum hardware speed) from the visual presentation delay (minimum duration: `max(actual_init_time, splash_min_duration)`). Features honest 100% "NETWORK READY" state readout, custom presets (Fast 1500ms, Normal 3000ms, Cinematic 5000ms, Custom slider 1–10s), `Hold Shift to skip`, and Tuyul mascot sports car departure animation with subtle headlight glow, twin exhaust jet fire, and high-speed acceleration transition into the Cockpit.
- **Manual Core Re-initialization Trigger**: Dedicated header action (`[ 🔄 Re-initialize Core ]`) enabling immediate hardware re-discovery, carrier probe synchronization, and policy table validation on-demand without playing the startup presentation.
- **Physical Monorepo Architecture**: Strict repository separation into `frontend/` (React+TS), `src-tauri/` (Desktop Shell), and `rust-core/` (Authoritative Engine) per Master Engineering Prompt Section 3.
- **Rust Core Authoritative Engine (`rust-core`)**: Standalone library crate with strict decoupled subsystems: `discovery`, `probe` (RFC 3550 standard Jitter estimator), `health` (EWMA composite 0–100 index), `policy` (score-based takeover margin arbiter), `failover` (lock-free async route transitions), `route` (Layer-3 metric management), `recovery` (anti-flap cooldown), `workload` (passive process detection), `qos` (DSCP traffic tagging), `events` (broadcast bus), and `reports`.
- **Platform Hardware Abstraction Layer**: OS-specific abstraction trait with Linux backend using `/sys/class/net` and `iproute2`, and architecture-ready Windows/macOS HAL stubs.
- **Modern Linux Desktop Compatibility**: Updated Tauri desktop shell layer to Tauri 2.0 with native WebKitGTK 4.1 and `libsoup3` integration.
- **Passive Telemetry Architecture**: Implemented non-blocking low-frequency (~1 Hz) passive CPU, RAM, and GPU sampling from procfs/sysfs, completely separated from high-frequency (5 Hz) network health probing and eliminating 60 FPS polling or IPC spam.
- **Speedtest Isolation & Session Protection Safeguard**: Fully decoupled speedtest into an isolated module (`rust-core/src/speedtest/`) with zero continuous execution, strict exclusion from failover scoring, and automatic deferral/inhibition when critical workloads (Zoom, OBS, vMix, Teams) are active.
- **Dedicated Device Health Subsystem**: Built standalone device resource monitoring domain (`DeviceHealth`, `DeviceCapabilities`, `GpuMetrics`) with passive 1 Hz sampling of CPU, RAM, and GPU. Strictly decoupled from Network Health scoring, ensuring device resource metrics never trigger network failover or mutate adapter states (`ONLINE`/`READY`/`ALERT`/`OFFLINE`/`DISABLED`).
- **Compact Device Health Indicators**: Integrated a minimal, clean 3-indicator widget (CPU, RAM, GPU) directly into the Cockpit Header with thin progress bars, percentage readouts, early-warning coloration, and explicit `N/A` fallback for unsupported GPU telemetry.
- **Dynamic Post-Startup Network Device Discovery**: Implemented non-blocking hotplug event detection (`EngineEvent::NewDeviceDetected`) in `rust-core` with a 0.5 Hz background topology monitoring ticker in Tauri desktop backend.
- **User-Directed Topology Refresh Flow**: Added lightweight non-blocking notification banner (`"New network device detected. Refresh to add it to the network interface list."`) with `[ Refresh ]` and `[ Dismiss ]` actions; `refresh_topology()` IPC command reconciles new hardware into candidate pool without preempting the active connection.
- **Initial Bootstrap Hidden-Until-Ready Discipline**: Guaranteed Cockpit remains hidden during startup splash until initial authoritative network discovery is fully validated, eliminating progressive card rendering artifacts and phantom interfaces.
- **Subtle GitHub Brand Icon**: Integrated tiny, crisp inline SVG GitHub mark beside `parikesitad-pm` in Cockpit Footer without introducing third-party icon libraries.
- **Hotplug Docking Simulation Scenario**: Added 5th scenario in Diagnostics Modal (`🔌 5. Hotplug USB-C Docking Station`) for interactive testing of dynamic detection and user-driven refresh flow.
- **Cockpit Footer Attribution**: Added subtle, low-contrast footer attribution linking `parikesitad-pm` directly to GitHub profile with native system browser delegation (`openUrl`).

### Changed

- Moved developer and scenario evaluation controls (`Policy Engine Simulation & Evaluation`) completely out of the default Home view into a dedicated `DiagnosticsModal` (accessible via header action or `Shift+D`), keeping the primary dashboard clean and focused.
- Migrated Device Health and Authoritative State consumption in React to the event-driven bridge (`network-engine-event` / `DeviceHealthUpdated`), eliminating continuous polling of `get_device_health()`.
- Shifted UI paradigm to ultra-calm network cockpit focusing strictly on active path, latency/jitter, throughput, and standby health.
- Separated auxiliary telemetry (hardware load, historical logs, deep packet diagnostics) to secondary on-demand views.
- Smoothed startup progress animation to naturally increment from 1% to 100% synchronized with actual engine hardware initialization speed and contextual sub-stage telemetry.
- Standardized all UI button controls, modal headers, and simulation actions to global technical English terminology.

### Fixed

- **Telemetry Collector Write-Lock Self-Deadlock**: Resolved a lock re-entrancy deadlock in `rust-core::AutoFailoverCore::bootstrap()` where chained `.write().await` calls within an `AuthoritativeState` struct literal held the temporary write guard across multiple field evaluations, ensuring instant, non-blocking bootstrap execution.
- **Vertical Accent Rail Layout Collision**: Fixed layout collision with technical label 'AUTOFAILOVER 3.0' by isolating segments with native CSS vertical writing mode, flex allocation, and gradient mask fades.
- Fixed gauge needle alignment mathematically across Download and Upload dials by unifying value normalization and driving both the SVG arc endpoint and needle rotation from the exact same angle formula (`angle = startAngle + normalized * sweepAngle`) with explicit center pivot `(100, 100)`.

---

## [2.6.0] - 2026-09

### Added

- Dual supercar cockpit tachometers (RPM Download & MPH Upload) with dynamic auto-scaling (`Kbps / Mbps / Gbps`).
- Center HUD readout for real-time Jitter (IETF RFC 3550) and active route gear indicators.
- Circular dial-based ICMP multi-target backbone indicators (`1.1.1.1`, `8.8.8.8`, `9.9.9.9` + optional 4th target).
- Dedicated 1-form modal for custom probing targets with IPv4 validation.
- Smart traffic throughput fallback resolving across active interfaces and system I/O.

---

## [2.5.0] - 2026-09

### Added

- SportsCarSpeedGauge speedtest gauge with 250° arc and peak hold indicators.
- Staged tactile refresh feedback sequence for adapter scanning and routing inspection.
- Canvas idle sleep optimization reducing CPU usage during constant network throughput.

---

## [2.4.0] - 2026-09

### Added

- Inline QoS monitor for one-click meeting and broadcast bandwidth reservation.
- Adaptive 1-to-8 port layout engine supporting single-NIC laptops through multi-port server workstations.
- Searchable log viewer with level filtering and export capability.

---

## [2.3.0] - 2026-09

### Added

- Frameless radial gradient splash screen with zero-delay startup transition.
- Global keyboard shortcut manager (F11, F5, Ctrl+M, Ctrl+T, Ctrl+Q, Ctrl+P).
- Synthesized audio alert chimes with high-load warning and master mute.

---

## [2.2.0] - 2026-09

### Added

- Multi-platform packaging support for Windows (`.zip`/`.exe`), macOS Apple Silicon (`.dmg`), and Linux (`.tar.gz`).
- 4-engine speedtest benchmark integration (Cloudflare, Fast.com, nPerf, Ookla).
- Floating toast notification banner system.

---

## [2.1.0] - 2026-09

### Changed

- Rebranding to MODULA with dual dark/light theme foundation.

---

## [2.0.0] - 2026-09

### Added

- Multi-port failover engine supporting simultaneous routing metric management across up to 3 physical adapters.
- Real-time Jitter calculation implemented using standard IETF RFC 3550 formula.

---

## [1.0.0] - 2026-09

### Added

- Initial release of software Layer-3 metric manipulation for zero-drop network failover without socket teardown.
