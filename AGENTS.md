# AGENTS.md — MainAX25-Stack (MAX25-Stack)

Map for AI agents. Humans: [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md).

## Purpose

**Main AX.25 Stack** — unified Packet Radio / AX.25 standalone stack. HyBBX plugs in as application layer; MainAX25 prepares TNC/modem hardware and exposes KISS/AX.25 (or CRDOP TCP).

**Standalone-first:** operator brings up radio path without HyBBX. HyBBX attaches via `share/hybbx/*.ini.example`.

## Upstream stacks (merged)

| Upstream | Path | HyBBX plugin |
|----------|------|--------------|
| [TNCs-Stack](https://github.com/ngteq/TNCs-Stack) | `stacks/tncs/` | `packet_radio` |
| [BayCom_PR-Stack](https://github.com/ngteq/BayCom_PR-Stack) | `stacks/baycom-pr/` | `baycom` |
| [CRDOP](https://github.com/ngteq/CRDOP) | `stacks/crdop/` | `crdop` |
| [hyBBX](https://github.com/ngteq/hyBBX) | external | consumer |

## Plugin hierarchy

```
Betriebsform → Hardware → Device
```

Registry: `plugins/manifest.yaml`

## Rules

1. **Standalone-first** — MAX25 prepares hardware; HyBBX never replaces boot-wait or kernel modem lifecycle.
2. **No personal/local paths** in docs or examples — use placeholders (`/dev/ttyUSB0`, `main.example.com`).
3. **Linux-primary** — [docs/PLATFORMS.md](docs/PLATFORMS.md).
4. **Minimal diffs** — link `stacks/*/` READMEs.
5. **HyBBX external** — INI in `share/hybbx/` only.
6. **Git** — only `ngteq <info@un1t.me>`; push via `~/.ssh/id_ed25519_ngteq`; commit/push when user asks.

## Commands

```bash
make all | test | release-check
./scripts/max25-ctl help
./scripts/discover-plugins.sh --json
```

## Doc map

| File | Use |
|------|-----|
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Code rules, testing |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layers, plugins |
| [docs/HYBBX.md](docs/HYBBX.md) | HyBBX contract |
| [docs/PLATFORMS.md](docs/PLATFORMS.md) | Linux / *BSD |
| [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) | v1 scope |
| [docs/MAX25-TERMINAL.md](docs/MAX25-TERMINAL.md) | max25d + MAX25 Terminal (planned) |

## Pitfalls

- TNC2C: DTR during power-on — echo mode otherwise
- BayCom: no minicom on raw UART while kernel driver loaded
- One process per serial port
