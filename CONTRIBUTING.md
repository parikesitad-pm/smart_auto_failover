# Contributing to AutoFailover by Modula

> **Enterprise Developer & Systems Engineering Contribution Guidelines**  
> **Official License**: MIT License, Copyright (c) 2026 `parikesitad-pm`  
> **Repository**: [https://github.com/parikesitad-pm/smart_auto_failover](https://github.com/parikesitad-pm/smart_auto_failover)

Thank you for your interest in contributing to **AutoFailover by Modula**. This document outlines the architectural standards, code ethics, cross-platform HAL invariants, and contribution workflow required to maintain broadcast-grade reliability across physical enterprise workstations.

---

## 1. Core Mission & Design Principles

AutoFailover is an autonomous, ultra-light Layer-3 network route orchestrator engineered to protect real-time workloads (Zoom, Microsoft Teams, Google Meet, OBS Studio, vMix, Wirecast, Streamlabs) from path failure and transient packet degradation.

### Architectural Invariants (Non-Negotiable)

1. **UI is NOT the Network Controller**:
   - The presentation layer (`desktop/ui/` and `website/`) is strictly responsible for displaying state, visualizing metrics, and dispatching user-authorized administrative requests.
   - The UI must **NEVER** initiate network probing, score path candidates, make failover decisions, mutate route tables, or enforce QoS rules.
   - The Python Core (`desktop/core/`) retains 100% autonomous runtime authority.

2. **Presentation Pipeline Separation**:
   Card sorting in the cockpit deck is **presentation-only**. Dynamic sorting must never cause hidden or disconnected interfaces to reappear:
   $$\text{Core Registry} \longrightarrow \text{Visibility Filter} \longrightarrow \text{Sort Visible Only} \longrightarrow \text{Dynamic Render}$$

3. **Active Workload Continuity**:
   - Never switch network routes for microscopic latency differences.
   - Protect active streaming broadcasts: when a secondary Ethernet cable (`eth1`) is active during a broadcast, the engine holds and preserves that path unless it experiences genuine packet loss, RTO, or disconnection.

4. **Kernel TCP/IP Safety**:
   - Socket probing must use `SO_REUSEADDR` and zero-linger `SO_LINGER(1, 0)` abortive resets to prevent `TIME_WAIT` socket buildup in `tcpip.sys`.
   - Never introduce proprietary kernel filter drivers that risk blue screens (BSOD) or kernel panics.

---

## 2. 5-Case Deterministic Arbitration Hierarchy

All routing policy enhancements must strictly conform to the 5-case arbitration hierarchy implemented in `desktop/core/policy/engine.py`:

| Case | Network Topology Condition | Authoritative Routing Action | Rationale |
|---|---|---|---|
| **Case 1** | Active workload on `eth1` (healthy) | **HOLD & PRESERVE `eth1`** | Eliminates route oscillation; guarantees uninterrupted Zoom/vMix/OBS sessions. |
| **Case 2** | `eth0` and `Wi-Fi` connected | **PRIORITIZE `eth0`** | Physical wire takes precedence over wireless carrier. |
| **Case 3** | `eth0`, `eth1`, and `Wi-Fi`; `eth0` degraded | **FAILOVER TO `eth1`** | Immediate transition to secondary wired standby. |
| **Case 4** | `eth0` & `eth1` in ALERT/RTO; `Wi-Fi` ready | **EMERGENCY FAILOVER TO `Wi-Fi`** | Salvages Internet connectivity when all wired infrastructure fails. |
| **Case 5** | `eth0`, `eth1`, and `Wi-Fi` all healthy | **PRIORITIZE `eth0`** | Primary physical cable serves as the baseline default route. |

---

## 3. Repository Structure

```
smart_auto_failover/
├── desktop/                  # Surface A: Native Desktop Application (Python 3)
│   ├── core/                 # Autonomous Failover Engine
│   │   ├── discovery/        # Dynamic Interface Prober (sysfs / NetTCPIP / networksetup)
│   │   ├── probe/            # RFC 3550 Statistical Jitter & Socket Probing
│   │   ├── health/           # EWMA Composite Health Index (0–100)
│   │   ├── policy/           # 5-Case Policy Engine & Takeover Arbiter
│   │   ├── failover/         # Layer-3 Route Table Orchestrator
│   │   ├── platform/         # Cross-Platform HALs (Linux, Windows, macOS)
│   │   └── speedtest/        # 4-Provider Benchmark Engine (Cloudflare, Fast, Ookla, nPerf)
│   ├── ui/                   # CustomTkinter Automotive Cockpit
│   └── tests/                # Autonomous Unit & Regression Test Suite
├── website/                  # Surface B: Public Marketing & Download Hub (React 18 + TS)
│   ├── src/components/       # UI Components (DownloadHub, DesktopAdvantages, ChangelogTimeline)
│   └── src/services/         # GitHub Releases Dynamic API Client
├── packaging/                # Native PyInstaller Entrypoints & Binary Specs
└── assets/                   # Official Modula Brand Assets & Screenshots
```

---

## 4. Local Development Workflow

### Prerequisites

- **Python 3.10+** (with `pip`, `venv`, and `tk` headers where applicable)
- **Node.js 18+** & **npm 9+**
- **Git**

### Setting Up Desktop Engine

```bash
# Clone the repository
git clone https://github.com/parikesitad-pm/smart_auto_failover.git
cd smart_auto_failover

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run full test suite (54 unit tests)
python3 -m unittest discover -s desktop/tests

# Launch the desktop cockpit in development mode
python3 -m desktop.main
```

### Setting Up Public Website & Download Hub

```bash
cd website
npm install
npm run dev      # Local Vite dev server (http://localhost:5173)
npm run build    # TypeScript type-check and Vite production build
```

---

## 5. Anti-Snowballing Engineering Discipline

To prevent unintended side effects and cascade regressions, every contributor must uphold our **Anti-Snowballing** rules:

1. **Scope Lock**:
   - Before writing code, identify and lock the exact files to be touched.
   - If a file outside the approved scope requires modification, stop immediately and re-evaluate.
2. **No Drive-By Refactors**:
   - Do not fix unrelated formatting, rename unrelated symbols, or re-architect adjacent modules in the same pull request.
   - Log tangential findings as separate issues.
3. **Tests as a Circuit Breaker**:
   - All existing regression tests in `desktop/tests/` must pass without modifications to expected baselines.
   - Any new feature or bug fix must include dedicated unit tests covering edge cases.
4. **Minimal Diff, Maximum Impact**:
   - Touch as few lines as necessary to reach a correct, verified outcome.
   - Never reformat entire files when a 5-line diff achieves the solution.

---

## 6. Mandatory Attribution & Fork Guidelines

AutoFailover is distributed under the **MIT License, Copyright (c) 2026 parikesitad-pm**.

### Requirements for Forks and Derivative Works

1. **Copyright Retention**:
   - All copies, forks, distributions, and substantial portions of the software must preserve the copyright notice:
     ```text
     Copyright (c) 2026 parikesitad-pm
     ```
2. **Upstream Attribution**:
   - Any fork, redistribution, or integrated module must provide prominent public attribution in its primary `README.md` linking back to the authoritative upstream repository:
     ```markdown
     Based on [AutoFailover by Modula](https://github.com/parikesitad-pm/smart_auto_failover), 
     originally engineered by `parikesitad-pm`.
     ```
3. **Author Identity**:
   - The canonical author alias is strictly `parikesitad-pm`. Real personal names must not be introduced into commit logs, documentation, or codebase headers.

---

## 7. Submitting a Pull Request

1. **Branch Naming**:
   - `feat/feature-name`
   - `fix/bug-description`
   - `docs/documentation-update`
2. **Commit Message Format**:
   - Keep commit messages short, concise, and casual in Bahasa Indonesia or standard Conventional Commits:
     ```text
     feat: tambah provider speedtest baru
     fix: perbaiki race condition di platform hal
     test: tambah pengujian 5-case failover
     docs: perbarui spesifikasi teknis
     ```
3. **CI/CD Gating Checklist (Definition of Done)**:
   - [ ] All unit tests pass (`python3 -m unittest discover -s desktop/tests`).
   - [ ] Frontend builds without errors (`npm --prefix website run build`).
   - [ ] No regression in socket teardown or kernel socket counts.
   - [ ] `CHANGELOG.md` is updated under `[Unreleased]` or target release section adhering to [Keep a Changelog](https://keepachangelog.com/).
   - [ ] PR description specifies exact problem, changes made, and verification steps.

---

## 8. License

By contributing to AutoFailover, you agree that your contributions will be licensed under the project's [MIT License](LICENSE) under `parikesitad-pm`.
