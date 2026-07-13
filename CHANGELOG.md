# Changelog

All notable changes to MainAX25-Stack (MAX25-Stack) are documented here.

## [MAX25-Stack-v1.0.0] — 2026-07-13

Version file `1.0.0`. Product label **MAX25-Stack-v1.0.0**.

**First production release** — standalone Packet Radio / AX.25 hardware lifecycle.

### Active devices

- **tnc2c** — Landolt TNC2C serial KISS (boot-wait, HyBBX `packet_radio`)
- **baycom-ser12** — kernel BayCom SER12 / PC-COM (single-modem default; dual opt-in)
- **soft-crdop** — MAX25-SoftModem (CRDOP), CB profile (`crdop.ini.example`); native M25/KISS host via `CrdopTcpBackend` (KISS default, `[CRDOP AX25 UI …]` display)

### Architecture

- **AX.25** — in-tree `ax25_codec.py` via `kiss_bridge.py`; `MAX25_BUNDLE_AX25` OFF; `third_party/ax25/` tarballs reference-only
- **CRDOP** — in-house MAX25-SoftModem scaffold; `MAX25_BUILD_CRDOP` **ON** by default; no vendored ardopcf in release
- **ARDOP-plugin** — optional MAX25-Stack plugin (`ardop_compat=true`)

### Stack

- `max25d` — Linux supervisor, M25/1 protocol, multi-device KISS bridge
- `max25-terminal` / `max25-client` — sole official operator client (text + F10 menu)
- Heterogeneous device backends: TNC serial, BayCom KISS PTY, CRDOP TCP
- AX.25 source ban list (`banlist.py`) — `bans_file`, M25/1 `BAN`/`UNBAN`/`BANS`, silent RX drop
- Plugin registry (`plugins/manifest.yaml`) and client profiles (`share/clients/`)

### Operator / docs

- Unified five-step device workflow — [docs/PLUGINS-DEVICE-MODEL.md](docs/PLUGINS-DEVICE-MODEL.md)
- BayCom single PC-COM default — [docs/BAYCOM.md](docs/BAYCOM.md)
- HyBBX attach INI examples in `share/hybbx/`
- Offline release gates: `./scripts/build.sh`, `./scripts/test.sh`, `./scripts/release-check.sh`

### Deferred to v1.1+

- `pktnc2`, `baycom-par96`, `baycom-kiss`
- CRDOP amateur and dual operator workflows (INI templates ship)

### Upstream stack versions

- BayCom PR-Stack `1.0.0`
- CRDOP dev track `CUR999` (`$SRC/stacks/crdop/VERSION`) — ships with MAX25-Stack v1.0.0
