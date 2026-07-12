# max25d — Linux daemon

**max25d** supervises TNC/modem hardware, runs per-device RX/TX backends, and exposes M25/1 to `max25-terminal`.

Linux only. Config: `share/max25/max25d.ini.example`.

## Components

| File | Role |
|------|------|
| `max25d` | Python 3 daemon — M25/1 server, stack lifecycle |
| `device_backends.py` | Backend abstraction (TNC, BayCom, CRDOP) |
| `kiss_bridge.py` | Serial KISS for command-mode TNCs (TNC2C/PK-TNC2) |
| `test_multi_device.py` | Multi-device routing smoke |

## Backends

| Device id | Backend | Notes |
|-----------|---------|-------|
| `tnc2c`, `pktnc2` | `KissSerialBackend` | CI-tested |
| `baycom-ser12`, `baycom-par96` | `BayComKissBackend` | KISS PTY after `baycom-pr-ctl start` |
| `baycom-kiss` | `KissRawSerialBackend` | USB/async KISS |
| `soft-crdop` | `CrdopTcpBackend` | ARDOP TCP host interface |

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

## Install

```bash
./scripts/install-max25.sh --deps
# Installs: /usr/local/bin/max25d, kiss_bridge.py, device_backends.py, max25-terminal
```

Edge guide: [docs/LINUX-EDGE-SETUP.md](../../docs/LINUX-EDGE-SETUP.md). Protocol: [include/max25/protocol.md](../../include/max25/protocol.md). Client: [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md).
