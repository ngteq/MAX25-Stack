# AGENTS.md — MainAX25-Stack (MAX25-Stack)

Map for AI agents. Humans: [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md).

## Purpose

**Main AX.25 Stack** — unified Packet Radio / AX.25 standalone stack. HyBBX plugs in as application layer; MAX25 prepares TNC/modem hardware and exposes KISS/AX.25 (or CRDOP TCP).

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

Registry: `plugins/manifest.yaml`. Discovery CLI lists hardware + device only.

## Rules

1. **Standalone-first** — MAX25 prepares hardware; HyBBX never replaces boot-wait or kernel modem lifecycle.
2. **No personal/local paths** in docs or examples — use placeholders (`/dev/ttyUSB0`, `main.example.com`).
3. **Linux daemon only** — `max25d` + BayCom + full stack on Linux; host setup — [docs/LINUX-HOST-SETUP.md](docs/LINUX-HOST-SETUP.md); terminal — [docs/PLATFORMS.md](docs/PLATFORMS.md).
4. **One official client** — `max25-terminal` / `max25-client` only; text + F10 menu; binding in [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md).
5. **BayCom stays** — first-class on Linux daemon; not deprecated.
6. **Minimal diffs** — link `stacks/*/` READMEs.
7. **HyBBX external** — INI in `share/hybbx/` only.
8. **Git** — only `ngteq <info@un1t.me>`; push via `~/.ssh/id_ed25519_ngteq`; commit/push when user asks.
9. **English-only repo** — all shipped docs, UI, examples, and user-facing text in English.
10. **CRDOP = CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio) — sound-card subproject **MAX25-SoftModem** at `stacks/crdop/`; **GNU GPLv3**; kernel ALSA only (MAX25 sound-proxy, no PulseAudio); full AX.25/KISS/TNC/modem compatibility goal; hardware-solution-first + pure-software deployment. **Static rule:** [docs/CRDOP.md](docs/CRDOP.md) — read before changing CRDOP code or docs.
11. **ARDOP external-only** — MAX25 never ships ARDOP code or binaries. ARDOP is optional third-party attach via `ardop_compat=true` on `soft-crdop`; native CRDOP/M25 host is the default.

## Commands

```bash
./scripts/build.sh | ./scripts/test.sh | ./scripts/release-check.sh
./scripts/max25-ctl help
./scripts/discover-plugins.sh --json
```

## Doc map

| File | Use |
|------|-----|
| [docs/README.md](docs/README.md) | **Doc index** |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Code rules, testing |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layers, plugins |
| [docs/PLUGINS-DEVICE-MODEL.md](docs/PLUGINS-DEVICE-MODEL.md) | Unified device workflow (TNC reference) |
| [docs/HYBBX.md](docs/HYBBX.md) | HyBBX contract |
| [docs/PACKET-RADIO.md](docs/PACKET-RADIO.md) | AX.25, KISS, TNC, BayCom |
| [docs/BAYCOM.md](docs/BAYCOM.md) | BayCom operator guide (single default, dual opt-in) |
| [docs/CRDOP.md](docs/CRDOP.md) | **CRDOP** = CB/AR Digital Open Protocol — MAX25-SoftModem subproject (GPLv3) |
| [stacks/crdop/docs/INDEX.md](stacks/crdop/docs/INDEX.md) | CRDOP doc index — operators, developers, AI agents |
| [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) | v1 scope |
| [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md) | Client dev & M25/1 binding |
| [docs/MAX25-TERMINAL.md](docs/MAX25-TERMINAL.md) | Operator UI (F10 menu) |
| [include/max25/protocol.md](include/max25/protocol.md) | M25/1 protocol reference |

## Next work

- `max25d` real modem RX as `RX …` (KISS bridge matures)
- PK-TNC2 device activation when hardware delivered

## Pitfalls

- TNC2C: DTR during power-on — echo mode otherwise
- BayCom: no userspace serial client on raw UART while kernel driver loaded
- One process per serial port
