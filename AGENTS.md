# AGENTS.md — MainAX25-Stack (MAX25-Stack)

Map for AI agents. Humans: [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md).

**Agent workflow:** [AGENT-INDEX.md](AGENT-INDEX.md) → this file. **SLAVE repo** — MASTER: [0-RESEARCHES §0.6](../0-RESEARCHES/AGENT-INDEX.md#06-master-repository-static-rule). Documentation only in `projects/max25-stack/`.

## Purpose

**Main AX.25 Stack** — unified Packet Radio / AX.25 standalone stack. HyBBX plugs in as application layer; MAX25 prepares TNC/modem hardware and exposes KISS/AX.25 (or CRDOP TCP).

**Standalone-first:** operator brings up radio path without HyBBX. HyBBX attaches via `share/hybbx/*.ini.example`.

## Upstream stacks (merged)

| Upstream | Path | HyBBX plugin |
|----------|------|--------------|
| [TNCs-Stack](https://github.com/ngteq/TNCs-Stack) | `stacks/tncs/` | `packet_radio` |
| [BayCom/based](docs/BAYCOM.md) (ex BayCom_PR-Stack) | `stacks/bcpr/` | via MAX25 |
| [CRDOP](https://github.com/ngteq/CRDOP) | `stacks/crdop/` | `crdop` |
| [hyBBX](https://github.com/ngteq/hyBBX) | external | consumer |

## Plugin hierarchy

```
Operating mode (`betriebsform/`) → Hardware → Device
```

Registry: `plugins/manifest.yaml`. Discovery CLI lists hardware + device only.

## Rules

1. **Standalone-first** — MAX25 prepares hardware; HyBBX never replaces boot-wait or kernel modem lifecycle.
2. **No personal/local paths** in docs or examples — use `$SRC`, `$PREFIX` ([docs/PATHS.md](docs/PATHS.md)) or placeholders (`/dev/ttyUSB0`, `main.example.com`).
3. **Linux daemon only** — `max25d` + BayCom + full stack on Linux; host setup — [docs/LINUX-HOST-SETUP.md](docs/LINUX-HOST-SETUP.md); terminal — [docs/PLATFORMS.md](docs/PLATFORMS.md).
4. **One official client** — `max25-terminal` / `max25-client` only; text + F10 menu; binding in [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md).
5. **BayCom stays** — first-class on Linux daemon; not deprecated.
6. **Minimal diffs** — link `stacks/*/` READMEs.
7. **HyBBX external** — INI in `share/hybbx/` only.
8. **Git** — only `ngteq <info@un1t.me>`; push via `~/.ssh/id_ed25519_ngteq`; commit/push when user asks.
9. **English-only repo** — all shipped docs, UI, examples, and user-facing text in English.
10. **CRDOP = MAX25-SoftModem** — stack acronym for the in-house sound-card AX.25 modem at `$SRC/stacks/crdop/` (device id `soft-crdop`); **GNU GPLv3**; kernel ALSA only (MAX25 sound-proxy, no PulseAudio); full AX.25/KISS/TNC/modem compatibility goal; hardware-solution-first + pure-software deployment. CB/amateur bands are use cases, not an acronym expansion. **Static rule:** [docs/CRDOP.md](docs/CRDOP.md) — read before changing CRDOP code or docs.
11. **ARDOP-plugin** — Optional MAX25-Stack plugin for third-party ARDOP host wire — **separate from CRDOP**. Registry: [plugins/external/ardop/plugin.yaml](plugins/external/ardop/plugin.yaml).
12. **Repo boundary (static)** — **Code + publication** in this repo. **100 % of documentation** in `0-RESEARCHES/projects/max25-stack/` — agents do not edit `docs/` unless operator explicitly requests release-tied sync ([vault §0.5](../0-RESEARCHES/AGENT-INDEX.md#05-documentation-sole-workspace-static-rule)).
13. **Publication standard** — complete, compact, English, AI/human-readable, generic — [AGENT-INDEX.md §0](AGENT-INDEX.md#0-publication-standard-all-projects).

## Commands

```bash
./scripts/build.sh | ./scripts/test.sh | ./scripts/release-check.sh
./scripts/max25-ctl help
./scripts/discover-plugins.sh --json
```

## Doc map

| File | Use |
|------|-----|
| **[AGENT-INDEX.md](AGENT-INDEX.md)** | **Agent workflow, publication standard, repo boundaries** |
| [docs/README.md](docs/README.md) | **Doc index** |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Code rules, testing |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layers, plugins |
| [docs/PLUGINS-DEVICE-MODEL.md](docs/PLUGINS-DEVICE-MODEL.md) | Unified device workflow (TNC reference) |
| [docs/HYBBX.md](docs/HYBBX.md) | HyBBX contract |
| [docs/PACKET-RADIO.md](docs/PACKET-RADIO.md) | AX.25, KISS, TNC, BayCom |
| [docs/BAYCOM.md](docs/BAYCOM.md) | BayCom operator guide (single default, dual opt-in) |
| [docs/CRDOP.md](docs/CRDOP.md) | **CRDOP** = MAX25-SoftModem (GPLv3) |
| [docs/PATHS.md](docs/PATHS.md) | Doc path variables (`$SRC`, `$PREFIX`, …) |
| [stacks/crdop/docs/INDEX.md](stacks/crdop/docs/INDEX.md) | CRDOP doc index — operators, developers, AI agents |
| [stacks/crdop/docs/HOST-PROTOCOL-SPEC.md](stacks/crdop/docs/HOST-PROTOCOL-SPEC.md) | CRDOP M25 host wire (frozen v1.0.0) |
| [docs/MAX25-OPERATOR-RUNBOOK.md](docs/MAX25-OPERATOR-RUNBOOK.md) | End-to-end operator workflow |
| [docs/HARDWARE-ACCEPTANCE.md](docs/HARDWARE-ACCEPTANCE.md) | Manual device smoke protocol |
| [docs/DEVICES-LIST-FULL.md](docs/DEVICES-LIST-FULL.md) | Full device compatibility list |
| [docs/NETDEV.md](docs/NETDEV.md) | Virtual TUN **`max25d0`** — IPv4/IPv6 defaults |
| [docs/AX25-NATIVE-CODEC.md](docs/AX25-NATIVE-CODEC.md) | ax25_codec.py spec |
| [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) | v1 scope |
| [docs/V2.0.0-SCOPE.md](docs/V2.0.0-SCOPE.md) | v2 goals + **DEV-Levels roadmap** |
| [docs/MODULAR-TCPIP-SERVER.md](docs/MODULAR-TCPIP-SERVER.md) | Main + Secondary TCP/IP service |
| [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md) | Client dev & M25/1 binding |
| [docs/MAX25-TERMINAL.md](docs/MAX25-TERMINAL.md) | Operator UI (F10 menu) |
| [docs/WEBSOCKET.md](docs/WEBSOCKET.md) | Browser terminal — **DEV-Level 3** (planned) |
| [stacks/web/README.md](stacks/web/README.md) | Web UI dev / deploy detail |
| [include/max25/protocol.md](include/max25/protocol.md) | M25/1 protocol reference |

## Next work (DEV-Level 1)

- Modular TCP/IP Servers Service — Main + Secondary topology
- Linux + FreeBSD platform compat (`max25d`, `max25d0`, build/install)
- Platform detection, INI examples, tests, rootless foundation

**DEV-Level 2 (*ca.*):** Main + Secondary supervision · cross-host wiring · `max25-tun` sidecar.

**DEV-Level 3 (*ca.*):** WebSocket gateway · other mid-tier items (not CRDOP).

**DEV-Level 4 (*ca.*):** CRDOP expansion — OSS polish, G3RUH, deeper integration.

**Later:** AI / assistant · like-features — deferred. See [docs/V2.0.0-SCOPE.md](docs/V2.0.0-SCOPE.md#dev-levels-roadmap-stack-wide).

## Pitfalls

- TNC2C: DTR during power-on — echo mode otherwise
- BayCom/based: exclusive UART lock under bcprd; do not open raw COM alongside
- One process per serial port
