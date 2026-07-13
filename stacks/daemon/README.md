# max25d — Linux daemon

**max25d** supervises TNC/modem hardware, runs per-device RX/TX backends, and exposes M25/1 to `max25-terminal`.

Linux only. Config: `share/max25/max25d.ini.example`.

## Components

| File | Role |
|------|------|
| `max25d` | Python 3 daemon — M25/1 server, stack lifecycle |
| `device_backends.py` | Backend abstraction (TNC, BayCom, CRDOP) |
| `kiss_bridge.py` | Serial KISS for command-mode TNCs (TNC2C/PK-TNC2) |
| `banlist.py` | AX.25 source ban list (silent RX drop) |
| `test_multi_device.py` | Multi-device routing smoke |

## Backends

| Device id | Backend | Notes |
|-----------|---------|-------|
| `tnc2c`, `pktnc2` | `KissSerialBackend` | CI-tested |
| `baycom-ser12`, `baycom-par96` | `BayComKissBackend` | KISS PTY after `max25-ctl` / `baycom-pr-ctl -c` — [docs/BAYCOM.md](../../docs/BAYCOM.md) |
| `baycom-kiss` | `KissRawSerialBackend` | USB/async KISS |
| `soft-crdop` | `CrdopTcpBackend` | CI-tested (offline TCP stub); live ARDOP via `crdopc` |

Untested backends log a startup warning; SEND/RX return `ERR link not ready` when the stack path is unavailable.

## Quick start

```bash
# Protocol only (no hardware):
./max25d --no-stack -c ../../share/max25/max25d.ini.example

# With stack auto-start:
sudo ./max25d -c /etc/max25/max25d.ini
```

## Multi-device

```ini
[devices]
default = tnc2c
tnc2c = /dev/ttyS4
pktnc2 = /dev/ttyS5
baycom-ser12 = baycom:a
soft-crdop = crdop:default
```

Full heterogeneous example: `share/max25/max25d.full-station.ini.example`.

M25/1: `devices=` in `STATUS`, `SET DEVICE <id>`, `GET DEVICES`, `RX device=<id> …`.

## Source ban list

Block unwanted AX.25 callers (source address on incoming UI frames). Banned traffic is dropped silently — no terminal display, no daemon log line.

```ini
[modem]
bans_file = /etc/max25/bans.txt
```

File format: one callsign per line (`#` comments allowed). Ban without SSID blocks all SSIDs of that call (`DG1ABC` blocks `DG1ABC-7`). Ban with SSID (`DK0WC-7`) matches only that SSID.

M25/1: `BAN <callsign>`, `UNBAN <callsign>`, `BANS`. Changes persist to `bans_file` immediately.

## Install

```bash
./scripts/install-max25.sh --deps
# Installs: /usr/local/bin/max25d, kiss_bridge.py, device_backends.py, max25-terminal
```

Host setup guide: [docs/LINUX-HOST-SETUP.md](../../docs/LINUX-HOST-SETUP.md). Protocol: [include/max25/protocol.md](../../include/max25/protocol.md). Client: [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md).
