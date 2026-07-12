# Platforms

## Best solution (architecture)

| Component | Platforms | Scope |
|-----------|-----------|--------|
| **`max25d`** (daemon) | **Linux only** | Full stack — TNCs, **BayCom**, CRDOP, plugins, config, hardware |
| **`max25-terminal`** (`max25-client`) | Linux, *BSD, macOS, Windows, AmigaOS (reduced) | Operator UI only — modem session to a running `max25d` |

The **daemon side is Linux-only** today and for the foreseeable future. That is intentional: kernel BayCom, AX.25, serial lifecycle, and HyBBX prep require Linux.

Other systems get **only the terminal** — they connect to `max25d` on a Linux host over the network. No local BayCom port, no local `max25d` on BSD/macOS/Windows/Amiga.

```
  Windows / macOS / *BSD / Amiga          Linux host
  ┌─────────────────────┐              ┌──────────────────┐
  │  max25-terminal     │   TCP/TLS?   │  max25d          │
  │  F10 · CALLERID     │ ──────────►  │  BayCom · TNC    │
  │  --ax25-ui          │              │  CRDOP · plugins │
  └─────────────────────┘              └──────────────────┘
```

See [MAX25-TERMINAL.md](MAX25-TERMINAL.md).

---

## Linux — daemon + terminal (supported now)

**Only platform where `max25d` runs.** Full MainAX25 stack. Example edge settings: **[LINUX-EDGE-SETUP.md](LINUX-EDGE-SETUP.md)**.

```bash
# Debian / Ubuntu
./scripts/install-max25.sh --deps
# or: make all && sudo make install
```

| Need | Role |
|------|------|
| GCC or Clang, make | Build merged stacks |
| `libncurses-dev` | `max25-terminal` |
| `python3` | `max25d` |
| `libasound2-dev` | CRDOP |
| `linux-headers-$(uname -r)` | BayCom kernel modules (when building in-tree) |
| Root / `sudo` | BayCom kernel modules (`stacks/baycom-pr`) |

**ARM Linux** (`armhf`, `aarch64`): native on-device build supported.

Serial: `/dev/ttyS*`, `/dev/ttyUSB*`, `/dev/ttyACM*`.

| Plugin / stack | Linux (`max25d`) |
|----------------|------------------|
| `hardware/tncs` | Serial KISS, boot-wait |
| `hardware/modems` (**BayCom**) | Kernel `baycom_ser_fdx`, `hdlcdrv`, KISS PTY |
| `hardware/soft-modems` (`soft-crdop`) | CRDOP + ALSA |
| HyBBX attach | After MAX25 prep — [HYBBX.md](HYBBX.md) |

Current control: `max25d` + `scripts/max25-ctl`. Example edge setup: [LINUX-EDGE-SETUP.md](LINUX-EDGE-SETUP.md).

CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

---

## Other platforms — terminal client only (planned)

No local `max25d`. Connect to **Linux `max25d`** remotely.

| Platform | Terminal | Notes |
|----------|----------|--------|
| **Linux** | `max25-terminal` | Local or remote daemon |
| ***BSD** | `max25-terminal` | ncurses; no local BayCom |
| **macOS** | `max25-terminal` | ncurses via Homebrew |
| **Windows** | `max25-terminal` | Console / PDCurses; daemon on Linux or WSL2 Linux |
| **AmigaOS 3.9+** | `max25-terminal` (reduced) | HyBBX-style thin client; no ncurses menu parity; RF on Linux host |

**BayCom** stays on the **Linux daemon** — not ported to other OS. Remote operators use the terminal to speak to the modem **through** Linux `max25d`.

### AmigaOS (niche, reduced)

- Build: `make amiga-terminal` or `scripts/build-amiga-terminal.sh` (SDK: `/opt/amiga`, NDKs under `/opt/amiga/NDKs`)
- Binary: `stacks/terminal/amiga/max25-terminal` (m68k, clib2, TCP-only)
- HyBBX-style thin client — no F10/ncurses menu; slash commands (`/status`, `/callerid`, …)
- CALLERID / CALLID / `--ax25-ui` / `-P` TCP auth
- Linux station runs `max25d` + BayCom/TNC

---

## What we do not port

| Item | Reason |
|------|--------|
| `max25d` to *BSD / macOS / Windows / Amiga | BayCom + kernel AX.25 + device lifecycle = Linux |
| BayCom kernel drivers | Linux-only by design (hard-won stack — stays) |
| `max25-ctl` device prep on non-Linux | Daemon responsibility on Linux only |

---

## Summary

- **Now:** Linux `max25d` + cross-platform **MAX25 Terminal** (AmigaOS reduced client cross-builds with `/opt/amiga`).
- **BayCom:** First-class on Linux daemon — not deprecated, not replaced on Linux.

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [MAX25-TERMINAL.md](MAX25-TERMINAL.md)
- [HYBBX.md](HYBBX.md)
- [LINUX-EDGE-SETUP.md](LINUX-EDGE-SETUP.md) — example edge install & `max25d.ini`
