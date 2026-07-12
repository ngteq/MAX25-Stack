# Changelog

All notable changes to MainAX25-Stack (MAX25-Stack) are documented here.

## [1.0.0] — 2026-07-12

**First production release** — standalone Packet Radio / AX.25 hardware lifecycle.

### Active devices

- **tnc2c** — Landolt TNC2C serial KISS (boot-wait, HyBBX `packet_radio`)
- **baycom-ser12** — kernel BayCom SER12 / PC-COM (single-modem default; dual opt-in)
- **soft-crdop** — CRDOP sound-card modem, CB profile (`crdop.ini.example`); wraps upstream `crdopc` (original ARDOP-compatible, no fork)

### Stack

- `max25d` — Linux supervisor, M25/1 protocol, multi-device KISS bridge
- `max25-terminal` / `max25-client` — sole official operator client (text + F10 menu)
- Heterogeneous device backends: TNC serial, BayCom KISS PTY, CRDOP TCP
- AX.25 source ban list (`banlist.py`) — `bans_file`, M25/1 `BAN`/`UNBAN`/`BANS`, silent RX drop
- Plugin registry (`plugins/manifest.yaml`) and client profiles (`share/clients/`)

### Operator / docs

- Unified five-step device workflow — [docs/PLUGINS-DEVICE-MODEL.md](docs/PLUGINS-DEVICE-MODEL.md)
- BayCom single PC-COM default for AX25SRV — [docs/BAYCOM.md](docs/BAYCOM.md)
- HyBBX attach INI examples in `share/hybbx/`
- Offline release gates: `./scripts/build.sh`, `./scripts/test.sh`, `./scripts/release-check.sh`

### Deferred to v1.1+

- `pktnc2`, `baycom-par96`, `baycom-kiss`
- CRDOP amateur and dual operator workflows (INI templates ship)

### Upstream stack versions

- BayCom PR-Stack `1.0.0`
- CRDOP `0.5.0` (embedded ardopcf)
