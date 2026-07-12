# Device: soft-crdop (CRDOP)

**Status:** Scaffold — built, not live RF verified.

Sound-card ARDOP modem from merged [CRDOP](https://github.com/ngteq/CRDOP) stack (`stacks/crdop/`). Plugin id `soft-crdop`; upstream project and binary remain **CRDOP** / `crdopc`.

## What it does

```
Radio ↔ audio (ALSA) ↔ crdopc ↔ TCP :8515/:8516 ↔ HyBBX crdop plugin
```

ARDOP over CB — separate from AX.25/KISS. Use alongside TNC or BayCom stacks for dual-protocol stations.

## Quick start

```bash
make -C stacks/crdop all
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
# HyBBX Secondary: share/hybbx/crdop-edge.ini.example
```

CB profile (default INI):

```bash
CRDOP_INI=stacks/crdop/share/crdop.ini.example ./stacks/crdop/scripts/crdopc
```

## Profiles

| Profile | INI example | Use |
|---------|-------------|-----|
| `cb` | `crdop.ini.example` | CB radio (default) |
| `dual` | `crdop-dual.ini.example` | CB ↔ amateur |
| `amateur` | `crdop-amateur.ini.example` | Ham (secondary) |

## Platform

CRDOP builds on Linux and *BSD (GCC/Clang). MainAX25 development targets **Linux first**; BSD support is planned later — see [docs/FREEBSD-AX25.md](../../docs/FREEBSD-AX25.md).

## Licensing

CRDOP/crdopc: MIT (ngteq). HyBBX `crdop` plugin: GPL-3.0 (external).
