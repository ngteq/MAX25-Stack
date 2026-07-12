# MainAX25-Stack (MAX25-Stack)

**Main AX.25 Stack** — standalone Packet Radio / AX.25 hardware lifecycle. HyBBX attaches as an external consumer (`packet_radio`, `baycom`, `crdop`). MAX25 owns modem/TNC prep, KISS bridge, and M25/1 operator IPC.

**Version:** `1.0.0-rc1` (see `VERSION`) · Full doc map: [docs/README.md](docs/README.md)

## Architecture

```
Operator                    Linux host (max25d)
┌─────────────────┐        ┌──────────────────────────────┐
│ max25-terminal  │ M25/1  │ max25d · KISS bridge         │
│ F10 · CALLERID  │ ─────► │ TNCs · BayCom · CRDOP        │
└─────────────────┘ :7325  └──────────────▲───────────────┘
                                           │ serial / kernel / TCP
                              HyBBX Secondary (external)
                              packet_radio · baycom · crdop
```

| Layer | Location | Role |
|-------|----------|------|
| Operator client | `stacks/terminal/` | Text + F10 menu — **only** official client |
| Daemon | `stacks/daemon/` | Linux-only supervisor, M25/1, multi-device KISS |
| Merged stacks | `stacks/tncs/`, `baycom-pr/`, `crdop/` | Device-specific tools and lifecycle |
| Plugins | `plugins/` | Operating mode → hardware → device registry |
| HyBBX attach | `share/hybbx/` | INI examples — HyBBX repo is external |

## Quick start

```bash
./scripts/build.sh
./scripts/discover-plugins.sh --json
./scripts/release-check.sh
```

Build output: `build/bin/` (`max25-terminal`, `tnc2c-probe`, `crdopc`, …).

### Linux edge (max25d + terminal)

```bash
./scripts/install-max25.sh --deps
sudo cp share/max25/max25d.ini.edge.example /etc/max25/max25d.ini
sudo max25d -c /etc/max25/max25d.ini
max25-terminal -U /run/max25/modem.sock --ax25-ui
```

Guide: [docs/LINUX-EDGE-SETUP.md](docs/LINUX-EDGE-SETUP.md).

### Active devices (v1)

| Device | Standalone | HyBBX plugin |
|--------|------------|--------------|
| **TNC2C** (`tnc2c`) | `max25-ctl start --hardware tncs --device tnc2c` | `packet_radio` |
| **BayCom SER12** (`baycom-ser12`) | `baycom-pr-ctl start` | `baycom` |
| **CRDOP** (`soft-crdop`) | `max25-ctl start --hardware soft-modems` | `crdop` |

Default operating mode: `standalone`. Deferred: `pktnc2`, `baycom-par96`, `baycom-kiss`.

## Platform

| Component | Platforms |
|-----------|-----------|
| **`max25d`** | **Linux only** — BayCom kernel, TNC boot-wait, CRDOP, multi-device KISS |
| **`max25-terminal`** | Linux, *BSD, macOS, Windows, AmigaOS (reduced) — remote TCP to Linux `max25d` |

Details: [docs/PLATFORMS.md](docs/PLATFORMS.md).

## Documentation

| Audience | Doc |
|----------|-----|
| **Index** | [docs/README.md](docs/README.md) |
| Edge setup | [LINUX-EDGE-SETUP.md](docs/LINUX-EDGE-SETUP.md) |
| Terminal operator | [MAX25-TERMINAL.md](docs/MAX25-TERMINAL.md) |
| Client / M25/1 | [MAX25-CLIENT.md](docs/MAX25-CLIENT.md) |
| Packet radio facts | [PACKET-RADIO.md](docs/PACKET-RADIO.md) |
| HyBBX attach | [HYBBX.md](docs/HYBBX.md) |
| Architecture | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Development | [DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| v1 scope | [V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) |

Agents: [AGENTS.md](AGENTS.md) · Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
