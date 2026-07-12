# max25d — Linux daemon

**max25d** supervises TNC/modem hardware, runs the KISS serial bridge, and exposes M25/1 to `max25-terminal`.

Linux only. Config: `share/max25/max25d.ini.example`.

## Components

| File | Role |
|------|------|
| `max25d` | Python 3 daemon — M25/1 server, stack lifecycle |
| `kiss_bridge.py` | Serial KISS bridge (one instance per `[devices]` id) |
| `test_proto.py` | M25/1 protocol smoke (no hardware) |
| `test_auth.py` | TCP auth smoke |
| `test_multi_device.py` | Multi-device routing smoke |

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
tnc2c = /dev/ttyUSB0
pktnc2 = /dev/ttyUSB1
```

M25/1: `devices=` in `STATUS`, `SET DEVICE <id>`, `GET DEVICES`, `RX device=<id> …`.

## Install

```bash
./scripts/install-max25.sh --deps
# Installs: /usr/local/bin/max25d, kiss_bridge.py, max25-terminal
```

Edge guide: [docs/LINUX-EDGE-SETUP.md](../../docs/LINUX-EDGE-SETUP.md). Protocol: [include/max25/protocol.md](../../include/max25/protocol.md). Client: [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md).
