# FreeBSD and AX.25 — Platform Notes

MainAX25-Stack (MAX25-Stack) **develops primarily for Linux** today. The *BSD family (FreeBSD, OpenBSD, NetBSD) is **supported in principle** but dedicated porting and validation come **much later** (*deutlich später*).

## Research conclusions (FreeBSD)

| Area | Linux (primary) | FreeBSD / *BSD (later) |
|------|-----------------|------------------------|
| Kernel AX.25 | `ax25`, `mkiss`, `6pack` in tree | **No in-kernel AX.25 stack** |
| `ax25-tools` | Packages / distro builds | **Not in ports** — must build from source or skip |
| KISS TNC path | Serial + kernel or userspace | Serial TNC tools work; no kernel AX.25 bind |
| BayCom kernel modems | `baycom_ser_fdx`, `hdlcdrv` | **BayCom driver not available** on BSD |
| Sound-card packet | Direwolf, fldigi, etc. | **Direwolf** is the practical BSD path for KISS/AX.25-over-audio |
| CRDOP soft modem | ALSA, tested | Builds with `alsa-lib` + Clang/GCC — tested upstream |

### Implications for MainAX25 plugins

| Plugin / stack | Linux | BSD (future) |
|----------------|-------|--------------|
| `hardware/tncs` (TNC2C, PK-TNC2) | Serial KISS → kernel/userspace AX.25 | Serial prep OK; AX.25 layer needs userspace (Direwolf bridge or similar) |
| `hardware/modems` (BayCom) | Kernel `baycom_ser_fdx` + KISS PTY | **Not viable** — no BayCom kernel driver |
| `hardware/soft-modems` (`soft-crdrop`) | `stacks/crdop` + ALSA | CRDOP builds on FreeBSD; HyBBX `crdop` plugin over TCP — no kernel dependency |
| HyBBX `packet_radio` | KISS → AX.25 | Requires alternate AX.25 implementation (not kernel) |
| HyBBX `baycom` | Kernel backend | **Unsupported on BSD** |

## Recommended BSD path (when pursued)

For AX.25-style packet on FreeBSD without kernel support:

1. **Direwolf** — sound-card TNC, KISS TCP/PTY, widely used on BSD ham setups.
2. **HyBBX** — attach to Direwolf KISS endpoint instead of kernel `ax25` or BayCom.
3. **CRDOP** (`soft-crdrop`) — ARDOP side channel; already BSD-buildable, TCP host interface unchanged.

BayCom SER12/PAR96 and kernel `axports` workflows from `stacks/baycom-pr/` remain **Linux-only** until an equivalent userspace modem exists.

## CRDOP on FreeBSD

Merged stack `stacks/crdop/` (plugin `soft-crdrop`) documents BSD build in upstream `stacks/crdop/docs/BUILD.md`:

```bash
pkg install cmake alsa-lib pkgconf
make -C stacks/crdop all
```

This does not provide AX.25 — it provides ARDOP for CB/digital links parallel to packet radio.

## Platform stance (summary)

- **Now:** Linux — kernel AX.25, BayCom, serial TNCs, CRDOP soft modem.
- **Later:** *BSD — userspace AX.25 (Direwolf), CRDOP; no BayCom kernel path.
- **Out of scope (BSD):** `ax25-tools` packaging, kernel `mkiss`, BayCom `hdlcdrv` parity.

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md) — plugin layers
- [HYBBX.md](HYBBX.md) — transport contracts
- `stacks/crdop/docs/BUILD.md` — CRDOP platform matrix
- `plugins/devices/soft-crdrop/README.md` — soft-crdrop device
