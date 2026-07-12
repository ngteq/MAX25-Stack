# AGENTS.md — MainAX25-Stack (MAX25-Stack)

Map for AI agents. Humans: [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md).

## Purpose

**Main AX.25 Stack** — unified Packet Radio / AX.25 standalone stack. HyBBX plugs in as application layer — MainAX25 (MAX25) prepares TNC/modem hardware and exposes KISS/AX.25 (or CRDOP TCP).

**Standalone-first:** operator brings up radio path without HyBBX. HyBBX attaches later via `share/hybbx/*.ini.example`.

## Product boundary

| MainAX25 owns | HyBBX owns (external) |
|---------------|----------------------|
| TNC boot-wait, serial prep | Sessions, users, telnet/SSH |
| BayCom kernel load, KISS PTY | HBX circuit, BBS, commands |
| `crdopc` lifecycle (TCP :8515) | `packet_radio`, `baycom`, `crdop` plugins |
| Plugin registry, `max25-ctl` | INI consumer only |

## Merged sources

| Repo path (original) | MainAX25 path | Notes |
|----------------------|---------------|-------|
| `/home/akb/Code/TNCs-Stack` | `stacks/tncs/` | TNC2C tools, HyBBX INI, docs |
| `/home/akb/Code/pc-com` (baycom_pr-Stack) | `stacks/baycom-pr/` | `baycom-pr-ctl`, config, tools |
| `/home/akb/Code/hyBBX` | external | Consumer — `packet_radio` + `baycom` + `crdop` |
| `/home/akb/Code/CRDOP` | `stacks/crdop/` | CRDOP soft modem (plugin `soft-crdrop`) |

`baycom_pr-Stack` is **`pc-com`** on disk (GitHub: ngteq/BayCom_PR-Stack).

## Plugin hierarchy

```
Betriebsform → Hardware → Device
```

- **Betriebsform:** `standalone`, `service`, `hybbx-edge`
- **Hardware:** `tncs` (→ HyBBX `packet_radio`), `modems` (→ HyBBX `baycom`), `soft-modems` (→ HyBBX `crdop`)
- **Device:** `tnc2c`, `pktnc2`, `baycom-ser12`, `soft-crdrop`, …

Registry: `plugins/manifest.yaml` · Each plugin dir has `plugin.yaml` + `README.md`.

## Rules

1. **Standalone-first** — MAX25 prepares hardware; HyBBX never replaces boot-wait or kernel modem lifecycle.
2. **Plugin registry** — new device → `plugin.yaml` + `manifest.yaml` + `discover-plugins.sh` validation.
3. **Linux-primary** — operator docs assume Linux; *BSD later — [docs/PLATFORMS.md](docs/PLATFORMS.md).
4. **Minimal diffs** — link `stacks/*/` READMEs; do not duplicate stack docs.
5. **No HyBBX vendoring** — INI examples in `share/hybbx/` only.
6. **Planning docs OK here** — `docs/V1.0.0-SCOPE.md` is intentional (unlike HyBBX core).
7. **Version** — `VERSION` file + `plugins/manifest.yaml` version field; release gates in `scripts/release-check.sh`.
8. **Git** — no commit/push unless the user asks.

Aligned with HyBBX agent rules where applicable: [hyBBX/AGENTS.md](/home/akb/Code/hyBBX/AGENTS.md), [hyBBX/docs/DEVELOPMENT.md](/home/akb/Code/hyBBX/docs/DEVELOPMENT.md).

## Commands

```bash
make all | test | release-check | discover | plugins
./scripts/max25-ctl discover | build | start | stop | status | test
./scripts/discover-plugins.sh [--json] [--type TYPE]
```

## Doc map

| File | Use |
|------|-----|
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Code rules, testing, doc duty |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Stack layers, plugin hierarchy |
| [docs/HYBBX.md](docs/HYBBX.md) | HyBBX integration contract |
| [docs/PLATFORMS.md](docs/PLATFORMS.md) | Linux primary, *BSD later |
| [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) | v1 MVP scope, acceptance, release |
| [docs/MERGE-REPORT.md](docs/MERGE-REPORT.md) | One-time merge archive — do not extend |

## Pitfalls

- TNC2C: DTR during power-on (boot-wait) — echo mode otherwise
- BayCom SER12: never minicom on raw UART while kernel driver loaded
- One process per serial port (HyBBX **or** tnc2c-tools, not both)
- PK-TNC2 (Unit B): planned — do not assume `/dev/ttyUSB0` until probed

## Next work

- Flesh out `baycom-par96`, `baycom-kiss` device plugins after hardware test
- Live RF verify `soft-crdrop` (CRDOP) with HyBBX `crdop` plugin
- Auto-generate device plugins from `stacks/baycom-pr/config/modems.ini` catalog
- BSD porting (*deutlich später*) — see `docs/PLATFORMS.md`
- CI: `.github/workflows/ci.yml` (`make test` + `release-check`)
