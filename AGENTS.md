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
Operating mode (`betriebsform/`) → Hardware → Device
```

Registry: `plugins/manifest.yaml`

## Rules

1. **Standalone-first** — MAX25 prepares hardware; HyBBX never replaces boot-wait or kernel modem lifecycle.
2. **No personal/local paths** in docs or examples — use placeholders (`/dev/ttyUSB0`, `main.example.com`).
3. **Linux daemon only** — `max25d` + BayCom + full stack on Linux; **Raspberry Pi primary edge** — [docs/RASPBERRY-PI.md](docs/RASPBERRY-PI.md); terminal cross-platform — [docs/PLATFORMS.md](docs/PLATFORMS.md).
4. **One official client** — `max25-terminal` / `max25-client` only; text + F10 menu; binding in [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md).
5. **BayCom stays** — first-class on Linux daemon; not deprecated.
6. **Minimal diffs** — link `stacks/*/` READMEs.
7. **HyBBX external** — INI in `share/hybbx/` only.
8. **Git** — only `ngteq <info@un1t.me>`; push via `~/.ssh/id_ed25519_ngteq`; commit/push when user asks.

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
| [docs/PACKET-RADIO.md](docs/PACKET-RADIO.md) | AX.25, KISS, TNC, BayCom (MAX25 technical) |
| [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) | v1 scope |
| [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md) | **Client dev & M25/1 binding** (sole client) |
| [docs/MAX25-TERMINAL.md](docs/MAX25-TERMINAL.md) | Operator UI (F10 menu) |
| [include/max25/protocol.md](include/max25/protocol.md) | M25/1 protocol reference |

## Next work

- `max25-terminal` — finish in-progress official client (`stacks/terminal/`) — [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md)
- `max25d` hardware TX/RX bridge (KISS/serial) — server-side; M25/1 client contract stays stable
- Remote TCP auth for `max25d` (optional, daemon-side)

## Pitfalls

- TNC2C: DTR during power-on — echo mode otherwise
- BayCom: no minicom on raw UART while kernel driver loaded
- One process per serial port
