# MainAX25-Stack (MAX25-Stack) Plugins

Packet Radio / AX.25 plugins for the standalone **Main AX.25 Stack**. HyBBX connects to a **running** stack — it does not replace these layers.

## Hierarchy

```
Betriebsform (operating mode)
  └── Hardware group (TNCs, Modems)
        └── Device (TNC2C, PK-TNC2, BayCom SER12, …)
```

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Betriebsform** | `betriebsform/` | How the station runs (standalone, service, HyBBX edge) |
| **Hardware** | `hardware/` | Device family — serial TNCs, BayCom modems, soft modems |
| **Device** | `devices/` | Concrete hardware profile and HyBBX INI mapping |

## Discovery

```bash
./scripts/discover-plugins.sh          # list all plugins
./scripts/discover-plugins.sh --json   # machine-readable
```

Registry: `manifest.yaml`

## HyBBX mapping

| MainAX25 hardware | HyBBX plugin | INI section |
|----------------|--------------|-------------|
| `hardware/tncs` | `packet_radio` | `[transport.packet_radioN]` |
| `hardware/modems` | `baycom` | `[transport.baycomN]` |
| `hardware/soft-modems` | `crdop` | `[transport.crdopN]` |

See [docs/HYBBX.md](../docs/HYBBX.md).
