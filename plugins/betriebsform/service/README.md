# Operating mode: Service

Continuous operation with one or two radios. HyBBX Secondary, digipeater, or unattended packet service.

## Requirements

- Unique IRQ per UART (BayCom kernel path)
- Staged modem start — see `stacks/baycom-pr/docs/GUIDE.md`
- No userspace serial client on raw UART while driver loaded

## Templates

| Stack | Config |
|-------|--------|
| BayCom dual | `stacks/baycom-pr/config/examples/baycom-pr.dual.ini` |
| HyBBX dual BayCom | `share/hybbx/service-dual.ini.example` |
| HyBBX dual TNC | `stacks/tncs/hybbx-dual.ini` |

One `[transport.*N]` per radio channel on HyBBX Secondary.
