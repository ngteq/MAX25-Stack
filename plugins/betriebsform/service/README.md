# Operating mode: Service

Continuous operation with one or two radios. HyBBX Secondary, digipeater, or unattended packet service.

## Requirements

- BayCom/based (PC-COM): **bcpr** — real IRQ, exclusive COM lock, max 2 devices ([docs/BAYCOM.md](../../../docs/BAYCOM.md))
- TNC path: unique serial device / no shared UART with bcpr
- No second process on the same UART while `bcprd` holds the lock

## Templates

| Stack | Config |
|-------|--------|
| BayCom/based (bcpr) | `stacks/bcpr/share/bcpr.ini.example` |
| HyBBX dual BayCom | `share/hybbx/service-dual.ini.example` |
| HyBBX dual TNC | `stacks/tncs/hybbx-dual.ini` |

One `[transport.*N]` per radio channel on HyBBX Secondary.
