# Changelog

All notable changes to **AutoFailover by Modula** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - 3.0.0

### Added

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

### Changed

- Shifted UI paradigm to ultra-calm network cockpit focusing strictly on active path, latency/jitter, throughput, and standby health.
- Separated auxiliary telemetry (hardware load, historical logs, deep packet diagnostics) to secondary on-demand views.
- Smoothed startup progress animation to naturally increment from 1% to 100% synchronized with actual engine hardware initialization speed and contextual sub-stage telemetry.
- Standardized all UI button controls, modal headers, and simulation actions to global technical English terminology.

### Fixed

- Fixed vertical accent rail layout collision with technical label 'AUTOFAILOVER 3.0' by isolating segments with native CSS vertical writing mode, flex allocation, and gradient mask fades.
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
