# Betriebsform: Service

Continuous operation with one or two radios. Intended for HyBBX Secondary, digipeater, or unattended packet service.

## Requirements

- Unique IRQ per UART (BayCom kernel path)
- Staged modem start (see BayCom PR-Stack GUIDE §11)
- Stable power — no ad-hoc minicom on raw UART while driver loaded

## Templates

| Stack | Config |
|-------|--------|
| BayCom dual | `stacks/baycom-pr/config/examples/baycom-pr.dual.ini` |
| TNC dual | `stacks/tncs/hybbx-dual.ini` |

## HyBBX

Map one `[transport.packet_radioN]` or `[transport.baycomN]` per radio channel.

See `share/hybbx/service-dual.ini.example`.
