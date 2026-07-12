# MainAX25-Stack (MAX25-Stack)

**Main AX.25 Stack** — unified Packet Radio / AX.25 standalone stack, fully **HyBBX-compatible**. HyBBX attaches as a plugin consumer; MainAX25 (MAX25) owns modem/TNC lifecycle, KISS, and AX.25 link preparation.

Merged from:

| Source | Location | Role |
|--------|----------|------|
| **TNCs-Stack** | `stacks/tncs/` | Serial TNC tools (TNC2C, PK-TNC2) |
| **baycom_pr-Stack** (`pc-com`) | `stacks/baycom-pr/` | BayCom kernel modems (SER12, PAR96, KISS) |
| **CRDOP** | `stacks/crdop/` | Sound-card ARDOP soft modem (`soft-crdrop`) |

## Quick start

```bash
make all
./scripts/discover-plugins.sh
./scripts/max25-ctl help
```

### TNC2C (Unit A)

```bash
./scripts/max25-ctl start --hardware tncs --device tnc2c   # boot-wait + power cycle
./scripts/max25-ctl test
# Then HyBBX Secondary with share/hybbx/tnc2c-edge.ini.example
```

### BayCom SER12

```bash
make -C stacks/baycom-pr all
sudo make -C stacks/baycom-pr install
./scripts/max25-ctl start --hardware modems --device baycom-ser12
```

### CRDOP soft modem (soft-crdrop)

```bash
make -C stacks/crdop all
./scripts/max25-ctl start --hardware soft-modems --device soft-crdrop
# HyBBX Secondary with share/hybbx/crdop-edge.ini.example
```

## Platform

**Linux-primary** development. *BSD support is planned later — see [docs/FREEBSD-AX25.md](docs/FREEBSD-AX25.md).

## Plugin architecture

```
plugins/
├── betriebsform/     Operating mode (Standalone, Service, HyBBX Edge)
├── hardware/         Hardware group (TNCs, Modems, Soft Modems)
└── devices/          Device-specific (tnc2c, pktnc2, baycom-ser12, soft-crdrop, …)
```

Registry: `plugins/manifest.yaml` · Discovery: `./scripts/discover-plugins.sh`

## HyBBX

| MainAX25 hardware | HyBBX plugin | Docs |
|----------------|--------------|------|
| TNCs | `packet_radio` | [docs/HYBBX.md](docs/HYBBX.md) |
| Modems | `baycom` | `stacks/baycom-pr/docs/PLUGIN.md` |
| Soft modems | `crdop` | [docs/HYBBX.md](docs/HYBBX.md#crdop) |

INI examples: `share/hybbx/`

## v1.0.0 roadmap

**Current version:** `1.0.0-rc1` (see `VERSION`)

MainAX25 ships **standalone-first**: one operator brings up TNC or modem without HyBBX; HyBBX attaches later via INI examples in `share/hybbx/`.

| v1.0.0 active | Standalone entry | HyBBX plugin |
|---------------|------------------|--------------|
| **TNC2C** (`tnc2c`) | `max25-ctl start --hardware tncs --device tnc2c` | `packet_radio` |
| **BayCom SER12** (`baycom-ser12`) | `baycom-pr-ctl start` | `baycom` |
| **CRDOP** (`soft-crdrop`) | `max25-ctl start --hardware soft-modems` | `crdop` |

**Default Betriebsform:** `standalone` · **Deferred:** `pktnc2`, `baycom-par96`, `baycom-kiss`, minicom fork, *BSD port.

```bash
make release-check    # v1.0.0 offline gates
```

Full scope, acceptance tests, and release checklist: [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md).

## Documentation

| Doc | Content |
|-----|---------|
| [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) | v1.0.0 MVP scope, workflows, acceptance |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Stack layers, plugin hierarchy |
| [docs/HYBBX.md](docs/HYBBX.md) | HyBBX integration contract |
| [docs/FREEBSD-AX25.md](docs/FREEBSD-AX25.md) | BSD platform stance and AX.25 limits |
| [docs/MERGE-REPORT.md](docs/MERGE-REPORT.md) | What was merged and how |

## For agents

[AGENTS.md](AGENTS.md)
