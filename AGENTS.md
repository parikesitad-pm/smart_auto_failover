# Junior — Engineering Copilot for AutoFailover 3.0 by Modula

> **User-Facing Tagline**: _"light seamless and usefull"_
> **Internal Principle**: _"ultra light seamless and powerfull"_
> **Core UX Principle**: _"Kelihatan kompleks di dalam. Terasa sederhana di luar."_

---

## 1. Product & Visual Direction

### Digital Network Cockpit

The dashboard is inspired by modern automotive digital instrument clusters (high-end performance-car dashboards), not a router administration panel.

- Dark cockpit interface (`#080b10` / stealth slate)
- High contrast, precision typography, custom SVG gauges
- Smooth needle & indicator lerp animation (60 FPS interpolated client-side)
- Subtle glow, thin technical geometry, strong visual hierarchy
- **Minimal information density** (40–60% reduction in primary dashboard clutter)
- **AutoFailover 3.0 Vertical Accent**: Hairline vertical accent stripe (light blue → blue → red) on the bezel edge, purely decorative, never a status indicator. Never label as M/M3/BMW; this visual identity belongs entirely to AutoFailover 3.0 by Modula.

### Primary Dashboard Priority (Answer in < 2s)

1. **What connection am I using?** (Active path / ONLINE)
2. **Is it healthy?** (Network health status)
3. **What is the current latency / jitter?** (RFC 3550 ms readout)
4. **What are download / upload conditions?** (Dual speed gauges)
5. **Which interfaces are ready if the active path fails?** (READY / ALERT / OFFLINE)
6. **Did MODULA switch paths?** (Clear transition toast/badge)

_Auxiliary telemetry (CPU/GPU/RAM monitoring, detailed workload sliders, deep logs, raw diagnostics) belong exclusively in secondary views._

---

## 2. Session Continuity & Active Workload Protection

### Primary Objective

MODULA exists to protect active real-time workloads (Zoom, Microsoft Teams, Google Meet, OBS Studio, vMix, Wirecast, Streamlabs) from connectivity degradation and path failure.
$$\text{DETECT EARLY} \longrightarrow \text{SELECT BETTER PATH} \longrightarrow \text{SWITCH FAST} \longrightarrow \text{MINIMIZE SESSION DISRUPTION}$$

### Realistic Continuity Discipline (No False Guarantees)

- **MODULA must NEVER claim guaranteed "zero socket drop"** solely from route/interface switching.
- Changing the network path can change the source IP/interface; existing TCP/UDP sessions may not survive across all protocols.
- **Engineering Objective**: _"Minimize disruption and maximize the probability of session continuity"_, never unconditional "zero-drop".
- Seamless behavior claims must be backed by measured, platform- and workload-specific testing.

### No Unnecessary Switching

Session continuity has higher priority than chasing small performance differences.

- **Do NOT switch** for tiny latency differences, momentary noise, single jitter spikes, or newly recovered preferred interfaces.
- The anti-flap takeover margin (`candidate_score >= active_score + takeover_margin`) absorbs noise without artificial delay.
- Switch only when the active path becomes degraded/unusable OR an alternative path is meaningfully better according to Policy Engine rules.

### Failure Priority Order

1. Preserve a healthy active path.
2. Detect degradation early.
3. Avoid unnecessary switching.
4. If active path becomes unusable, fail over immediately.
5. Select the best eligible path.
6. Continue background monitoring of the previous path.
7. Recover and re-evaluate without unnecessary preemption.

---

## 3. UI / Core Ownership & Authority Model

### The UI is NOT the network controller.

**React + TypeScript UI is responsible for:**

- Rendering dashboard state
- User interaction & administrative confirmations
- Configuration requests
- Displaying Failover Engine events and decisions

**The UI must NEVER own:**

- Network probing
- Health evaluation
- Path scoring
- Failover decisions
- Route switching
- Adapter state management
- Recovery / failback logic
- QoS enforcement

The **Rust Core** is responsible for all network control and runtime decisions.

### Authority Hierarchy

- **Policy Engine**: Decides which path **SHOULD** be active (`candidate_score >= active_score + takeover_margin`).
- **Failover Engine**: Executes and orchestrates the decision.
- **Platform Backend**: Performs OS-specific network operations (IPHLPAPI / SystemConfiguration / NetLink).
- **Workload Engine**: Informs Policy scoring with context (Video Conference vs Live Production); **never** switches interfaces directly.
- **UI**: Only displays state and requests user-authorized actions. UI never makes independent failover decisions.

```text
React / TypeScript UI
        ↓ (Tauri IPC commands: enable_interface, disable_interface, etc.)
     Tauri IPC
        ↓ (Events & State Streams)
      Rust Core
        ↓
┌───────────────────────────────┐
│ Discovery                     │
│ Probe (RFC 3550 Jitter)       │
│ Health Scoring                │
│ Policy Engine                 │
│ Failover Engine               │
│ Route Manager (Layer-3 Metric)│
│ Recovery & Anti-Flap Arbiter  │
│ Workload Awareness (Passive)  │
│ QoS Orchestrator              │
└───────────────┬───────────────┘
                ↓
        Native OS APIs
```

---

## 4. Administrative Actions vs Policy Decisions

Administrative actions are fundamentally different from policy decisions:

- When a disabled adapter is detected as physically healthy via background socket probing, the UI prompts:
  > _"Ethernet 1 is disabled but appears healthy. Enable it for automatic failover?"_
  > `[ Enable ]` `[ Keep Disabled ]`
- If user chooses **Enable**:
  `UI` → `Tauri IPC (enable_interface)` → `Rust Core` → `Platform Backend enables adapter` → `verify operational state` → `health validation` → `Policy Engine evaluates it` → `Failover Engine decides whether promotion is justified`.
- **"Enable" MUST NOT mean "force ONLINE"**. The Policy Engine always retains absolute authority over path selection.
- If user chooses **Keep Disabled**:
  The adapter remains disabled, excluded from eligible failover candidates.
- **NEVER silently re-enable** an adapter that the user explicitly disabled at the OS level.

---

## 5. Atomic IPC Commands & Process Independence

### Atomic Commands

IPC commands must represent atomic intentions:

- `enable_interface(id)`
- `disable_interface(id)`
- `request_policy_update(config)`
- `get_interface_state()`

**Prohibited Anti-Patterns**: Never create combined commands such as `enable_and_promote_interface()` or `switch_and_reconfigure_everything()`.

### Process Independence

- The network engine must not depend on the UI lifecycle.
- Failover Engine must continue operating when the UI is minimized, hidden, temporarily unresponsive, or closed.
- Core emits state/events; UI consumes them. Never reverse this dependency.

---

## 6. Technology Baseline

- **UI**: React + TypeScript + custom SVG-based visualization
- **Desktop Shell**: Tauri
- **Native / Core Engine**: Rust
- **Platform Integration**: Native OS APIs (Routing Table, NetLink, IPHLPAPI, SystemConfiguration)
- **IPC**: Tauri IPC / event-based communication
- **Cadence**: Probing @ 5–20 Hz, UI State @ 5–10 Hz, Visual Animation @ 60 FPS (interpolated client-side).

---

## 7. Splash Minimum Display Delay & Tuyul Sport Car Departure

### Core Principle

- **Network initialization**: _FAST AS POSSIBLE_
- **Visual startup**: _INTENTIONAL_
- _"Engine boleh ngebut. Cockpit masuk dengan gaya."_

### Architecture Flow

Initialization completion and visual completion are decoupled:

```text
initialize network immediately
        +
measure actual initialization (start_time -> core_ready_at)
        +
minimum visual duration: max(actual_initialization_time, splash_min_duration)
        ↓
Core reaches 100% (honest progress, no fake increments)
        ↓
Status: "NETWORK READY"
        ↓
Tuyul Mascot enters Sport Car departure animation during remaining splash window
        ↓
Cockpit transition
```

### Delay Mechanics & Configuration

- **Config**: `splash_min_duration_ms` (Default: `3000ms`).
- **Presets**: `Fast` (1500ms), `Normal` (3000ms), `Cinematic` (5000ms).
- **Custom Range**: `1000ms – 10000ms`.
- **Skip Delay**: `Hold Shift to skip startup presentation` or setting `Skip startup presentation` (Default: OFF).
- **UI Clarification**: _"Controls minimum splash display time. Does not affect network initialization."_
- **Absolute Rule**: NEVER use `setTimeout` before or during network initialization. The Core starts and finishes at maximum hardware speed.

### Tuyul Sport Car Animation Concept

- **During Initialization**: Tuyul mascot displays subtle idle suspension bobbing / movement.
- **At 100% Core Ready**: Tuyul jumps into mini sleek performance sport car, engine lights ignite with subtle glow, and accelerates off-screen into the cockpit.
- **Aesthetic**: Premium dark cockpit styling, thin vector geometry, subtle motion blur, never exaggerated slapstick.

---

## 8. Author & License

- **Author**: `parikesitad-pm`
- **License**: MIT License, 2026, `parikesitad-pm`
