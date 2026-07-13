# Device: soft-crdop (MAX25-SoftModem / CRDOP — CB/AR Digital Open Protocol)

**CRDOP** = **CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio).

**Status:** `active` — MAX25-Stack **standard subproject** (`stacks/crdop/`).

**Canonical rule:** [docs/CRDOP.md](../../../docs/CRDOP.md) · **License:** GNU GPL v3

## Summary

| Topic | Policy |
|-------|--------|
| Type | Sound-card software modem subproject |
| Compatibility | **AX.25 / KISS / TNC / modem** (software-modem domain) |
| Mission | **Hardware solutions** (primary) + pure **software** on computers |
| Audio | Kernel ALSA + MAX25 sound-proxy — **no PulseAudio** |
| Build | Default ON — `-DMAX25_BUILD_CRDOP=OFF` to skip |

## Quick start

```bash
./scripts/build.sh
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
```

See [docs/CRDOP.md](../../../docs/CRDOP.md) for full project rules.
