# Devices list · MAX25-Stack 1.5.0

Full device registry — active, deferred, and planned backends.

## Active device matrix

| Device id | Hardware stack | HyBBX plugin | Status |
|-----------|----------------|--------------|--------|
| `tnc2c` | `stacks/tncs` | `packet_radio` | active |
| `baycom-ser12` | `stacks/baycom-pr` | `baycom` | active |
| `soft-crdop` | `stacks/crdop` | `crdop` | active (dev/test) |

## Deferred matrix

| Device id | Notes |
|-----------|-------|
| `pktnc2` | PK-TNC2 variant — v1.1+ |
| `baycom-par96` | parallel port — v1.1+ |
| `baycom-kiss` | serial KISS BayCom — v1.1+ |

## Discovery matrix

| Command | Output |
|---------|--------|
| `./scripts/discover-plugins.sh` | hardware + device plugins |
| `./scripts/discover-plugins.sh --json` | machine-readable |

Registry: `plugins/manifest.yaml`

## Related

| Goal | Doc |
|------|-----|
| Device model | [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
