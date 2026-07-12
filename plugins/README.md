# MainAX25-Stack plugins

Packet Radio / AX.25 plugin registry. HyBBX connects to a **running** stack — it does not replace these layers.

## Hierarchy

```
Operating mode (`betriebsform/`)
  └── Hardware (tncs, modems, soft-modems)
        └── Device (tnc2c, baycom-ser12, soft-crdop, …)
```

| Layer | Directory | Purpose |
|-------|-----------|---------|
| Operating mode | `betriebsform/` | Standalone, service, HyBBX edge |
| Hardware | `hardware/` | Device family — TNCs, BayCom, soft modems |
| Device | `devices/` | Concrete profile and HyBBX INI mapping |

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

## v1 active devices

| Device | Hardware | Status |
|--------|----------|--------|
| `tnc2c` | `tncs` | active |
| `baycom-ser12` | `modems` | active |
| `soft-crdop` | `soft-modems` | active |
