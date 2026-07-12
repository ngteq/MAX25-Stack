# Platforms

## Architecture

| Component | Platforms | Scope |
|-----------|-----------|--------|
| **`max25d`** | **Linux only** | TNCs, BayCom, CRDOP, KISS bridge, multi-device |
| **`max25-terminal`** | Linux, *BSD, macOS, Windows, AmigaOS (reduced) | Operator UI → remote Linux `max25d` |

```
  Windows / macOS / *BSD / Amiga          Linux host
  ┌─────────────────────┐              ┌──────────────────┐
  │  max25-terminal     │   TCP :7325  │  max25d          │
  │  F10 · CALLERID     │ ──────────►  │  BayCom · TNC    │
  └─────────────────────┘              └──────────────────┘
```

## Linux — daemon + terminal

Full MAX25 stack. Edge setup: [LINUX-EDGE-SETUP.md](LINUX-EDGE-SETUP.md).

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

**ARM Linux** (`armhf`, `aarch64`): native build supported.

| Stack | Linux (`max25d`) |
|-------|------------------|
| `hardware/tncs` | Serial KISS, boot-wait |
| `hardware/modems` | Kernel BayCom, KISS PTY |
| `hardware/soft-modems` | CRDOP + ALSA |
| HyBBX attach | After MAX25 prep — [HYBBX.md](HYBBX.md) |

CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Other platforms — terminal only

No local `max25d`. Connect to Linux host over TCP (port **7325**).

| Platform | Terminal | Notes |
|----------|----------|-------|
| Linux | `max25-terminal` | Local Unix socket or TCP |
| *BSD | `max25-terminal` | ncurses; no local BayCom |
| macOS | `max25-terminal` | ncurses via Homebrew |
| Windows | `max25-terminal` | Console; daemon on Linux or WSL2 |
| AmigaOS 3.9+ | `max25-terminal` (reduced) | TCP-only; no F10 menu parity |

Amiga build: `scripts/build-amiga-terminal.sh` (SDK: `/opt/amiga`).

## Not ported

| Item | Reason |
|------|--------|
| `max25d` to non-Linux | BayCom kernel + device lifecycle = Linux |
| BayCom kernel drivers | Linux-only by design |

*BSD AX.25 background: [FREEBSD-AX25.md](FREEBSD-AX25.md).

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [MAX25-TERMINAL.md](MAX25-TERMINAL.md)
- [MAX25-CLIENT.md](MAX25-CLIENT.md)
