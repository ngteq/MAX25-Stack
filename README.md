# MainAX25-Stack (MAX25-Stack)

**Main AX.25 Stack** — unified Packet Radio / AX.25 standalone stack, fully **HyBBX-compatible**. HyBBX attaches as a plugin consumer; MainAX25 (MAX25) owns modem/TNC lifecycle, KISS, and AX.25 link preparation.

Merged from:

| Source | Location | Role |
|--------|----------|------|
| **TNCs-Stack** | `stacks/tncs/` | Serial TNC tools (TNC2C, PK-TNC2) |
| **baycom_pr-Stack** (`pc-com`) | `stacks/baycom-pr/` | BayCom kernel modems (SER12, PAR96, KISS) |

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

## Plugin architecture

```
plugins/
├── betriebsform/     Operating mode (Standalone, Service, HyBBX Edge)
├── hardware/         Hardware group (TNCs, Modems)
└── devices/          Device-specific (tnc2c, pktnc2, baycom-ser12, …)
```

Registry: `plugins/manifest.yaml` · Discovery: `./scripts/discover-plugins.sh`

## HyBBX

| MainAX25 hardware | HyBBX plugin | Docs |
|----------------|--------------|------|
| TNCs | `packet_radio` | [docs/HYBBX.md](docs/HYBBX.md) |
| Modems | `baycom` | `stacks/baycom-pr/docs/PLUGIN.md` |

INI examples: `share/hybbx/`

## Documentation

| Doc | Content |
|-----|---------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Stack layers, plugin hierarchy |
| [docs/HYBBX.md](docs/HYBBX.md) | HyBBX integration contract |
| [docs/MERGE-REPORT.md](docs/MERGE-REPORT.md) | What was merged and how |

## For agents

[AGENTS.md](AGENTS.md)
