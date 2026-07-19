# Plugins & device model · MAX25-Stack 1.8.5-fallback_untested-upcoming#1

Unified five-step device workflow for all RF backends.

## Workflow matrix

| Step | Action |
|------|--------|
| 1 | Select operating mode (`standalone`, `hybbx-host`, `service`) |
| 2 | Select hardware class (`tncs`, `modems`, `soft-modems`) |
| 3 | Select device id from registry |
| 4 | Run prep (`max25-ctl start …`) |
| 5 | Verify M25/1 + optional HyBBX attach |

## Registry matrix

| Layer | Source |
|-------|--------|
| Manifest | `plugins/manifest.yaml` |
| Discovery | `./scripts/discover-plugins.sh` |
| HyBBX mode | `plugins/betriebsform/hybbx-host/` |

## Device class matrix

| Hardware | Devices | Protocol |
|----------|---------|----------|
| `tncs` | `tnc2c`, (deferred `pktnc2`) | KISS serial |
| `modems` | `max25e0` / `baycom-kiss` | bcpr SER12 / USB KISS |
| `soft-modems` | `soft-crdop` | M25 host TCP + ALSA |

## Related

| Goal | Doc |
|------|-----|
| Full device list | [DEVICES-LIST-FULL.md](DEVICES-LIST-FULL.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
