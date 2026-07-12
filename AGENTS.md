# AGENTS.md — MainAX25-Stack (MAX25-Stack)

Map for AI agents. Humans: [README.md](README.md).

## Purpose

**Main AX.25 Stack** — unified Packet Radio / AX.25 standalone stack. HyBBX plugs in as application layer — MainAX25 (MAX25) prepares TNC/modem hardware and exposes KISS/AX.25.

## Merged sources

| Repo path (original) | MainAX25 path | Notes |
|----------------------|------------|-------|
| `/home/akb/Code/TNCs-Stack` | `stacks/tncs/` | TNC2C tools, HyBBX INI, docs |
| `/home/akb/Code/pc-com` (baycom_pr-Stack) | `stacks/baycom-pr/` | `baycom-pr-ctl`, config, tools |
| `/home/akb/Code/hyBBX` | external | Consumer — `packet_radio` + `baycom` plugins |

`baycom_pr-Stack` is **`pc-com`** on disk (GitHub: ngteq/BayCom_PR-Stack).

## Plugin hierarchy

```
Betriebsform → Hardware → Device
```

- **Betriebsform:** `standalone`, `service`, `hybbx-edge`
- **Hardware:** `tncs` (→ HyBBX `packet_radio`), `modems` (→ HyBBX `baycom`)
- **Device:** `tnc2c`, `pktnc2`, `baycom-ser12`, …

Registry: `plugins/manifest.yaml` · Each plugin dir has `plugin.yaml` + `README.md`.

## Commands

```bash
make all | test | discover | plugins
./scripts/max25-ctl discover | build | start | stop | status | test
./scripts/discover-plugins.sh [--json] [--type TYPE]
```

## Conventions

- German terms in docs where operator-facing: **Betriebsform**, **Betrieb**
- Code, plugin IDs, scripts: English
- Minimal diffs; do not duplicate stack READMEs — link to `stacks/*/`
- Do not commit `stacks/tncs/research/` secrets or local paths in new files
- HyBBX is external — reference `share/hybbx/*.ini.example` only

## Pitfalls

- TNC2C: DTR during power-on (boot-wait) — echo mode otherwise
- BayCom SER12: never minicom on raw UART while kernel driver loaded
- One process per serial port (HyBBX **or** tnc2c-tools, not both)
- PK-TNC2 (Unit B): planned — do not assume `/dev/ttyUSB0` until probed

## Next work

- Flesh out `baycom-par96`, `baycom-kiss` device plugins after hardware test
- Auto-generate device plugins from `stacks/baycom-pr/config/modems.ini` catalog
- CI: `make test` + `scripts/discover-plugins.sh --json`
