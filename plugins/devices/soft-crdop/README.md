# Device: soft-crdop (CRDOP)

**Status:** Active — builds and smokes offline; live RF acceptance manual.

Sound-card ARDOP modem from `stacks/crdop/`. Plugin id `soft-crdop`; upstream **CRDOP** / `crdopc`.

## Flow

```
Radio ↔ ALSA ↔ crdopc ↔ TCP :8515/:8516 ↔ HyBBX crdop plugin
```

ARDOP — parallel to AX.25/KISS, not a replacement.

## Quick start

```bash
./scripts/build.sh
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
```

HyBBX: `share/hybbx/crdop-edge.ini.example`

## Platform

Linux primary; CRDOP also builds on *BSD — [docs/PLATFORMS.md](../../docs/PLATFORMS.md).
