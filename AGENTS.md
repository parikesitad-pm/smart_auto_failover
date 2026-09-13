# Junior — Engineering Copilot for AutoFailover 3.0 by Modula

> **User-Facing Tagline**: _"light seamless and usefull"_
> **Internal Principle**: _"ultra light seamless and powerfull"_
> **Core UX Principle**: _"Kelihatan kompleks di dalam. Terasa sederhana di luar."_

---

## INTERACTIVE COMMAND HANDLING

These rules apply ONLY to actual command/tool execution during an
approved implementation, test, build, or setup task.

For known, non-destructive development/setup commands:

- If a command supports a non-interactive flag such as
  `--noconfirm`, `--yes`, or equivalent, prefer using it.
- For a 2-option prompt, select option 1 automatically.
- For a 5-option prompt, select option 4 automatically.
- For repeated confirmation prompts, reuse the approved response.
- For "Accept all" / `[y/N]` prompts, answer `yes` when the command
  is explicitly within the approved development/setup scope.

Do NOT auto-confirm:

- destructive commands
- unknown commands
- system/network changes outside the approved task
- prompts with unclear meaning

If the prompt does not match the known rules:
stop and report the available choices instead of guessing.

IMPORTANT:
Instructions written inside planning or documentation files must
never be interpreted as automatic execution authority.

A plan describes intended work.
Execution still requires an explicit implementation task.

## BUILD ARTIFACT TRACEABILITY

When a build completes, always report the exact output artifact paths.

Do not assume or invent artifact locations.

Report separately:

- frontend build artifact
- Rust binary
- Tauri bundle/installer
- target platform
- target architecture

A successful build is not considered manually verified until the actual
artifact can be located and, where applicable, launched/tested.

Build logs must distinguish:

BUILD SUCCESS
from
ARTIFACT VERIFIED
from
APPLICATION LAUNCHED

Do not conflate these states.

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

## 7. Enterprise Splash / Initialization Experience

### Core Principle

- **Official Modula 3.0 Identity**: Centered, prominent Modula logo (`assets/modula_3.0.png`) with technical emerald glow. No mascots, no cartoon animations, no sports cars.
- **Network initialization**: _FAST AS POSSIBLE_ (measured directly via native APIs).
- **Decoupled Timing**: Real Core initialization runs immediately at maximum speed; presentation respects minimum splash duration (`splash_min_duration_ms`, default 3000ms).
- **Initialization Gate**: Dashboard never opens before Core is genuinely ready in Native mode.
- **Failure Handling**: If Core is unresponsive, hold cleanly with `INITIALIZATION INCOMPLETE` and offer `[ Retry Initialization ]`.

### Exact Stage Mapping (0% – 100%)

- `0% – 10%`: Starting Core
- `10% – 20%`: Reading System Information
- `20% – 40%`: Discovering Network Interfaces
- `40% – 55%`: Reading IP Configuration
- `55% – 70%`: Validating Interface State
- `70% – 85%`: Initializing Network Probes (RFC 3550)
- `85% – 95%`: Evaluating Network Health
- `95% – 100%`: Preparing Runtime State
- `100%`: APP READY

### Progressive Technical Disclosure

- **SYSTEM**: Device Model / Hostname, Operating System, Native Architecture.
- **NETWORK**: Ethernet (State / IP / Speed), Wi-Fi (State / IP / SSID), Gateway / Route State, Designated Outbound Path.
- **Completion Transition**: At 100% APP READY, the logo glow settles into solid emerald, holding cleanly before a short, calm 350ms fade transition into the Dashboard.

---

## 8. Dedicated Device Health & System Resource Telemetry

### Separation of Concerns

- **Network Health and Device Health are strictly decoupled concepts.**
- **Network Health**: Latency, jitter (RFC 3550), packet loss, availability, throughput, interface quality. Evaluated by `HealthScorer` and drives `PolicyEngine` candidate path selection.
- **Device Health**: CPU utilization, RAM utilization, GPU utilization/VRAM (where platform exposes it), and system resource pressure (`nominal`, `moderate`, `critical`).
- **Invariance Rule**: Device Health **MUST NEVER** alter network failover decisions, calculate candidate scores, or mutate adapter states (`ONLINE`/`READY`/`ALERT`/`OFFLINE`/`DISABLED`).

### Cadence & Telemetry Discipline

- **Low-frequency passive sampling**: CPU @ ~1 Hz, RAM @ ~1 Hz, GPU @ ~1 Hz.
- UI may perform client-side visual interpolation, but **MUST NOT** poll hardware telemetry at 60 FPS or flood Tauri IPC.
- Platform capabilities are explicitly flagged (`DeviceCapabilities`). Unsupported metrics return `None` (`Option<T>`) and render as `UNAVAILABLE` in the UI without fake fallback increments.
- Secondary UI surface: Keeps primary network cockpit dashboard clean and uncluttered.

---

## 9. Author & License

- **Author**: `parikesitad-pm`
- **License**: MIT License, 2026, `parikesitad-pm`
