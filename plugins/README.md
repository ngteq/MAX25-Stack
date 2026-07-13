# MainAX25-Stack plugins

Packet Radio / AX.25 plugin registry. HyBBX connects to a **running** stack — it does not replace these layers.

**Unified operator workflow:** [docs/PLUGINS-DEVICE-MODEL.md](../docs/PLUGINS-DEVICE-MODEL.md) — TNC is the reference pattern; BayCom and CRDOP follow the same five steps and M25/1 session commands (`SET DEVICE` → `CONNECT` → `SEND`).

## Hierarchy

```
Operating mode (`betriebsform/`)
  └── Hardware (tncs, modems, soft-modems)
        └── Device (tnc2c, baycom-ser12, soft-crdop, …)
```

| Layer | Directory | Purpose |
|-------|-----------|---------|
| Operating mode | `betriebsform/` | Standalone, service, HyBBX host |
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
| `soft-crdop` | `soft-modems` | active (CB profile only) |

## Deferred (v1.1+)

| Device | Hardware | Status | Notes |
|--------|----------|--------|-------|
| `pktnc2` | `tncs` | planned | Awaiting hardware delivery |
| `baycom-par96` | `modems` | scaffold | LPT 9600 — kernel `CONFIG_BAYCOM_PAR` |
| `baycom-kiss` | `modems` | scaffold | USB/async KISS serial |

CRDOP amateur and dual profiles: INI templates ship; operator workflow deferred to v1.1+. See [docs/V1.0.0-SCOPE.md](../docs/V1.0.0-SCOPE.md).

Terminal client profiles: [share/clients/](../share/clients/README.md) · BayCom hardware via `baycom-pr.ini` ([share/baycom/](../share/baycom/README.md)); client YAML is operator reference.

## Operator quick reference (v1 active)

| Device | `max25-ctl start` | Site config | Client YAML |
|--------|-------------------|-------------|-------------|
| `tnc2c` | `--hardware tncs --device tnc2c` | `share/max25/serial/tnc2c-serial.env.example` | `share/clients/tnc2c.yaml` |
| `baycom-ser12` | `--hardware modems --device baycom-ser12` | `share/baycom/baycom-pr.pccom-ttyS0-only.ini.example` | `share/clients/baycom-ser12.yaml` (reference) |
| `soft-crdop` | `--hardware soft-modems --device soft-crdop` | `stacks/crdop/share/crdop.ini.example` | `share/clients/soft-crdop.yaml` |

BayCom default: **single PC-COM** (shipped template). Dual kernel-ser12 is **global opt-in** via `--baycom-profile dual` — see [docs/BAYCOM.md](../docs/BAYCOM.md).
