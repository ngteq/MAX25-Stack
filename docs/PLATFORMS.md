# Platforms

**Policy:** `max25d` is developed for **mainstream OS distributions only**. **DEV-Level 1 (*ca.* current):** modular TCP/IP integration + **Linux/KLinux and FreeBSD** compat together. **DEV-Level 3:** WebSocket; **DEV-Level 4:** CRDOP expansion — see [V2.0.0-SCOPE.md](V2.0.0-SCOPE.md#dev-levels-roadmap-stack-wide).

**Clients** (`max25-terminal`, third-party M25/1) also target **smaller systems** (e.g. AmigaOS) as **remote TCP clients** — they never host `max25d`. Legacy DOS clients (MS-DOS, FreeDOS, …) are **not** a target.

## `max25d` development priority (mandatory order)

| Priority | Platform | Minimum version | Status |
|----------|----------|-----------------|--------|
| **1** | **Linux / KLinux** | **KLinux 5.10.260+** or **KLinux 5.15.211+** | **DEV-Level 1 — full stack + Secondary role** |
| **1** | **FreeBSD** (*BSD first) | 15.1+ | **DEV-Level 1 — Main/TCP/IP hub + minimal CRDOP/OSS** |
| 3 | macOS | X+ (10.9+) | planned — after DEV-Level 1 |
| 4 | Windows | 10+ | planned |

**\*BSD family (after DEV-Level 1):** **FreeBSD first** (in DEV-Level 1) → when stable → **OpenBSD** → then **NetBSD**. No parallel *BSD ports beyond FreeBSD in DEV-Level 1.

**Rule:** finish **DEV-Level 1** (modular TCP/IP + Linux + FreeBSD base) before **DEV-Level 3** WebSocket or **DEV-Level 4** CRDOP expansion. Do not dilute DEV-Level 1 with parallel feature pushes.

### Linux / KLinux (priority 1)

Supported kernel floors (either line):

| Kernel line | Minimum |
|-------------|---------|
| KLinux **5.10** LTS | **5.10.260+** |
| KLinux **5.15** LTS | **5.15.211+** |

Target **mainstream distributions** on `x86_64` and `aarch64` (Debian, Ubuntu, Raspberry Pi OS, Fedora, openSUSE, etc.) with a kernel at or above one of these floors. BayCom kernel modules require headers matching the running kernel.

**ARM Linux** (`armhf`, `aarch64`): native build supported on priority-1 kernels.

Host setup: [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md).

### FreeBSD (priority 1 — DEV-Level 1, with Linux)

**FreeBSD 15.1+** — `max25d` port **in DEV-Level 1** alongside Linux hardening. **Server role** with modular TCP/IP hub and **minimal CRDOP/OSS** — not a full CRDOP expansion push (that is **DEV-Level 4**).

| Topic | Rule |
|-------|------|
| **Scope (DEV-Level 1)** | `max25d` server · modular TCP/IP Main · **minimal CRDOP** (`soft-crdop`) via **FreeBSD/OSS** · M25/1 |
| **Scope (DEV-Level 4)** | CRDOP OSS polish, modulation milestones, deeper integration |
| **Audio** | **OSS** on FreeBSD — **not** Linux/ALSA on BSD |
| **Deferred on FreeBSD (for now)** | Kernel **BayCom** · TNC boot-wait · ALSA |
| **Not in first BSD wave** | OpenBSD, NetBSD — only after FreeBSD is covered and working |
| **Operators** | `max25-terminal` local or remote; RF via CRDOP on BSD server or remote Linux/KLinux Secondary |

Background and AX.25 limits: [FREEBSD-AX25.md](FREEBSD-AX25.md). Build: `./scripts/build-freebsd.sh` · Service model: [MODULAR-TCPIP-SERVER.md](MODULAR-TCPIP-SERVER.md).

### Platform roles — split deployment (example)

**Not the only layout** — a supported pattern when FreeBSD owns TCP/IP integration and Linux keeps hardware radios.

| Host | `max25d` role | RF / devices | Notes |
|------|---------------|--------------|-------|
| **FreeBSD** | **Main** (+ optional local Secondary) | CRDOP/OSS (`soft-crdop`) | Modular TCP/IP Servers Service hub · M25/1 `:7325` |
| **Linux** | **Secondary only** | TNC · BayCom (`bcsf0`) · KISS PTY | Extends RF capacity; optional `max25d0` TUN on Linux host |

Architecture: [ARCHITECTURE.md](ARCHITECTURE.md#example-deployment--freebsd-primary-linux-secondary).

### *BSD family order (mandatory)

| Step | OS | When |
|------|-----|------|
| 1 | **Linux/KLinux + FreeBSD 15.1+** | **DEV-Level 1** — modular TCP/IP + platform compat |
| 2 | **OpenBSD** | After DEV-Level 1 complete |
| 3 | **NetBSD** | After OpenBSD covered |

Do not start OpenBSD or NetBSD `max25d` work while FreeBSD is still open.

### macOS (priority 3)

**macOS X+** — `max25d` port after FreeBSD tier. Until then: `max25-terminal` via Homebrew → remote Linux `max25d`.

### Windows (priority 4)

**Windows 10+** — `max25d` port last. Until then: `max25-terminal` console client → Linux host (or WSL2 Linux host for RF hardware).

---

## Architecture (today vs target)

| Component | Today (v1) | Target (ordered port) |
|-----------|------------|------------------------|
| **`max25d`** | **Linux / KLinux only** (full stack) | **DEV-Level 1:** Linux + FreeBSD (TCP/IP hub) → **DEV-Level 3:** WebSocket → **DEV-Level 4:** CRDOP → macOS X+ → Windows 10+ |
| **`max25-terminal`** | Linux, *BSD, macOS, Windows, AmigaOS (reduced) | unchanged — remote M25/1 client |

**Single-host (today):**

```
  Windows / macOS / *BSD / Amiga          Linux host (priority 1 today)
  ┌─────────────────────┐              ┌──────────────────┐
  │  max25-terminal     │   TCP :7325  │  max25d          │
  │  F10 · CALLERID     │ ──────────►  │  BayCom · TNC    │
  └─────────────────────┘              └──────────────────┘
```

**Split deployment (example — FreeBSD primary, Linux secondary):**

```
  Clients                    FreeBSD (Main + CRDOP)          Linux (Secondary)
  ┌──────────────┐          ┌─────────────────────┐        ┌──────────────────┐
  │ max25-terminal│  :7325  │ Main max25d         │ :7327  │ Secondary max25d │
  │              │ ───────► │ CRDOP/OSS Secondary │ ─────► │ TNC · BayCom     │
  └──────────────┘          └─────────────────────┘        └──────────────────┘
```

---

## Linux — daemon + terminal (priority 1)

Full MAX25 stack.

```bash
./scripts/install-max25.sh --deps
# or: ./scripts/build.sh && cmake --install build
```

| Dependency | Role |
|------------|------|
| GCC/Clang, CMake 3.16+ | Build |
| `python3` | `max25d` |
| `libncurses-dev` | `max25-terminal` |
| `libasound2-dev` | CRDOP |
| `linux-headers-$(uname -r)` | BayCom kernel modules |

| Stack | Linux (`max25d`) |
|-------|------------------|
| `hardware/tncs` | Serial KISS, boot-wait |
| `hardware/modems` | Kernel BayCom, KISS PTY |
| `hardware/soft-modems` | CRDOP + **ALSA** (Linux) · **OSS** (FreeBSD when ported) |
| HyBBX attach | After MAX25 prep — [HYBBX.md](HYBBX.md) |

CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Clients — mainstream and smaller systems

`max25-terminal` runs where the operator sits. RF hardware may sit on Linux/KLinux Secondaries, on a FreeBSD CRDOP host, or on a single Linux `max25d` (today’s default).

| Class | Examples | `max25-terminal` | Local `max25d` + RF |
|-------|----------|------------------|---------------------|
| **Mainstream desktop** | Linux, Windows 10+, macOS X+ | full or console | Linux/KLinux (today) |
| **Smaller / retro** | AmigaOS 3.9+ | reduced TCP client | **no** — remote M25/1 only |

**Not a target:** MS-DOS, FreeDOS, and similar legacy DOS — no client port planned.

**AmigaOS:** `stacks/terminal/amiga/` — TCP/M25/1 only. Build: `scripts/build-amiga-terminal.sh`.

Third-party GUI clients: [MAX25-CLIENT.md](MAX25-CLIENT.md).

---

## Other platforms — terminal only (until `max25d` port)

No local `max25d` on these platforms **today**. Connect to a priority-1 Linux host over TCP (port **7325**).

| Platform | Terminal | `max25d` |
|----------|----------|----------|
| Linux / KLinux | `max25-terminal` | **yes** — full stack (priority 1) |
| FreeBSD | `max25-terminal` | planned — server + **CRDOP**, light port (15.1+) |
| OpenBSD / NetBSD | `max25-terminal` | after FreeBSD works |
| macOS | `max25-terminal` | planned (X+, priority 3) |
| Windows | `max25-terminal` | planned (10+, priority 4) |
| AmigaOS 3.9+ | `max25-terminal` (reduced) | not planned — TCP client only |

Amiga build: `scripts/build-amiga-terminal.sh` (SDK: `/opt/amiga`).

## Out of scope for `max25d`

| Item | Reason |
|------|--------|
| Non-mainstream or embedded RTOS | mainstream OS/dist policy |
| Skipping priority order | DEV-Level 1 (TCP/IP + Linux + FreeBSD) before DEV-Level 3/4 |
| BayCom kernel drivers on non-Linux | Linux Secondary role; not in initial FreeBSD port |
| OpenBSD / NetBSD `max25d` before DEV-Level 1 done | *BSD family order — FreeBSD in DEV-Level 1 first |
| Large BSD port (all devices day one) | light port — minimal CRDOP/OSS in DEV-Level 1 |
| ALSA as FreeBSD CRDOP audio path | use **OSS** on FreeBSD |

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [MAX25-TERMINAL.md](MAX25-TERMINAL.md)
- [MAX25-CLIENT.md](MAX25-CLIENT.md)
- [FREEBSD-AX25.md](FREEBSD-AX25.md)
