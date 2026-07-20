# MainAX25-Stack plugins

Packet Radio / AX.25 plugin registry. HyBBX connects to a **running** stack — it does not replace these layers.

**Unified operator workflow:** [docs/PLUGINS-DEVICE-MODEL.md](../docs/PLUGINS-DEVICE-MODEL.md) — TNC is the reference pattern; BayCom follows the same five steps and M25/1 session commands (`SET DEVICE` → `CONNECT` → `SEND`).

## Hierarchy

```
Operating mode (`betriebsform/`)
  └── Hardware (tncs, modems, soft-modems)
        └── Device (tnc2c, max25e0, baycom-kiss, soft-crdop, …)
```

| Layer | Directory | Purpose |
|-------|-----------|---------|
| Operating mode | `betriebsform/` | Standalone, service, HyBBX host |
| Hardware | `hardware/` | Device family — TNCs, BayCom, soft modems |
| Device | `devices/` | Concrete profile and HyBBX INI mapping |
| Optional plugins | `external/` | ARDOP-plugin (optional third-party ARDOP host registry) |

## Discovery

```bash
./scripts/discover-plugins.sh          # hardware + device
./scripts/discover-plugins.sh --json
```

Output types: `hardware`, `device` — **not** operating modes (`betriebsform/` is manifest-only).

Registry: `manifest.yaml`

## HyBBX mapping

| MAX25 hardware | HyBBX plugin | INI section |
|----------------|--------------|-------------|
| `hardware/tncs` | `packet_radio` | `[transport.packet_radioN]` |
| `hardware/modems` | `baycom` | `[transport.baycomN]` |
| `hardware/soft-modems` | `crdop` | `[transport.crdopN]` |

See [docs/HYBBX.md](../docs/HYBBX.md).

## Active devices

| Device | Hardware | Status |
|--------|----------|--------|
| `tnc2c` | `tncs` | active |
| `max25e0` | `modems` | active — BayCom/based SER12 via **bcpr** (`stacks/max25-bcpr/`) |
| `baycom-kiss` | `modems` | active — USB/async KISS serial |
| `soft-crdop` | `soft-modems` | active — MAX25-SoftModem (CRDOP) standard |

## ARDOP-plugin (optional)

| Plugin | Notes |
|--------|-------|
| **ARDOP-plugin** | Separate third-party ARDOP host registry — [external/README.md](external/README.md) |

## Deferred / removed

| Device | Hardware | Status | Notes |
|--------|----------|--------|-------|
| `pktnc2` | `tncs` | planned | Awaiting hardware delivery |
| `baycom-par96` | `modems` | removed | Kernel LPT path retired — use bcpr where applicable |
| `baycom-ser12` | `modems` | removed | Kernel SER12 path retired — use **`max25e0`** / bcpr |

Terminal client profiles: [share/clients/](../share/clients/README.md) · BayCom/based SER12: [docs/BAYCOM.md](../docs/BAYCOM.md) · `stacks/max25-bcpr/`.

## Operator quick reference (active)

| Device | Start / bring-up | Site config | Client YAML |
|--------|------------------|-------------|-------------|
| `tnc2c` | `max25-ctl start --hardware tncs --device tnc2c` | `share/max25/serial/tnc2c-serial.env.example` | `share/clients/tnc2c.yaml` |
| `max25e0` | max25d `[features] max25_bcpr=yes` · `max25e0 = max25-bcpr:bc0` | `stacks/max25-bcpr/share/max25-bcpr.ini.example` | none (device id `max25e0`) |
| `baycom-kiss` | max25d `[devices]` + `[serial.baycom-kiss]` | serial env / max25d.ini | `share/clients/baycom-kiss.yaml` |

BayCom/based default: **`max25e0`** via max25-bcpr (max 2: `max25e0:bc0` / `bc1`) — see [docs/BAYCOM.md](../docs/BAYCOM.md).
