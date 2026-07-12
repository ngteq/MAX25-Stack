# Platforms

MainAX25-Stack (MAX25-Stack) is developed **primarily on Linux**. Operator docs, scripts, and HyBBX INI examples assume Linux paths (`/dev/ttyS*`, `systemctl`, kernel BayCom drivers).

**Portable stance:** the *BSD family (FreeBSD, NetBSD, OpenBSD) is **supported in principle**; dedicated porting and validation come **much later** (*deutlich später*). See [BSD family (later)](#bsd-family-later).

## Linux

Primary target for v1.0.0. Full stack: serial TNCs, BayCom kernel modems, CRDOP soft modem, HyBBX attach.

```bash
make all
make test
make release-check
```

| Need | Role |
|------|------|
| GCC or Clang, make | Build merged stacks |
| `libasound2-dev` | CRDOP (`stacks/crdop`) |
| Root / `sudo` | BayCom kernel module load (`stacks/baycom-pr`) |

Serial TNC paths: `/dev/ttyS*`, `/dev/ttyUSB*`, `/dev/ttyACM*`.

| Stack / plugin | Linux |
|----------------|-------|
| `hardware/tncs` (TNC2C, PK-TNC2) | Serial KISS, boot-wait, kernel/userspace AX.25 |
| `hardware/modems` (BayCom) | Kernel `baycom_ser_fdx`, `hdlcdrv`, KISS PTY |
| `hardware/soft-modems` (`soft-crdrop`) | CRDOP + ALSA, TCP :8515 |
| HyBBX `packet_radio` / `baycom` / `crdop` | After MAX25 prep — see [HYBBX.md](HYBBX.md) |

CI: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## BSD family (later)

Research summary for FreeBSD 15.x (applies broadly to *BSD for AX.25 limits):

| Area | Linux (primary) | *BSD (later) |
|------|-----------------|--------------|
| Kernel AX.25 | `ax25`, `mkiss` in tree (distro-dependent) | **No in-kernel AX.25 stack** |
| `ax25-tools` | Packages / distro builds | **Not in ports** — build from source or skip |
| KISS TNC path | Serial + kernel or userspace | Serial prep OK; no kernel AX.25 bind |
| BayCom kernel modems | `baycom_ser_fdx`, `hdlcdrv` | **Not available** on BSD |
| Sound-card packet | Direwolf, fldigi, etc. | **Direwolf** — practical KISS/AX.25-over-audio path |
| CRDOP soft modem | ALSA, tested | Builds with `alsa-lib` + Clang/GCC |

### Plugin viability on BSD

| Plugin / stack | BSD (future) |
|----------------|--------------|
| `hardware/tncs` | Serial prep OK; AX.25 needs userspace (e.g. Direwolf bridge) |
| `hardware/modems` (BayCom) | **Not viable** — no BayCom kernel driver |
| `hardware/soft-modems` (`soft-crdrop`) | CRDOP builds; HyBBX `crdop` over TCP — no kernel dependency |
| HyBBX `packet_radio` | Needs alternate AX.25 (not kernel) |
| HyBBX `baycom` | **Unsupported on BSD** |

### Recommended BSD path (when pursued)

1. **Direwolf** — sound-card TNC, KISS TCP/PTY.
2. **HyBBX** — attach to Direwolf KISS endpoint instead of kernel `ax25` or BayCom.
3. **CRDOP** (`soft-crdrop`) — ARDOP side channel; BSD-buildable, TCP host unchanged.

BayCom SER12/PAR96 and `axports` workflows from `stacks/baycom-pr/` remain **Linux-only**.

### CRDOP on FreeBSD

```bash
pkg install cmake alsa-lib pkgconf
make -C stacks/crdop all
```

ARDOP only — not AX.25. See `stacks/crdop/docs/BUILD.md`.

### Platform stance (summary)

- **Now:** Linux — kernel AX.25, BayCom, serial TNCs, CRDOP.
- **Later:** *BSD — userspace AX.25 (Direwolf), CRDOP; no BayCom kernel path.
- **Out of scope (BSD):** `ax25-tools` packaging, kernel `mkiss`, BayCom `hdlcdrv` parity.

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md) — plugin layers
- [HYBBX.md](HYBBX.md) — transport contracts
- [FREEBSD-AX25.md](FREEBSD-AX25.md) — alias / pointer (same content)
