# Operating mode: Service

Continuous operation with one or two radios. HyBBX Secondary, digipeater, or unattended packet service.

## Requirements

- Unique IRQ per UART (BayCom kernel path)
- Staged modem start — see `stacks/baycom-pr/docs/GUIDE.md`
- No minicom on raw UART while kernel driver loaded

## Templates

| Stack | Config |
|-------|--------|
| BayCom dual | `stacks/baycom-pr/config/examples/baycom-pr.dual.ini` |
| HyBBX dual | `share/hybbx/service-dual.ini.example` |

One `[transport.*N]` per radio channel on HyBBX Secondary.
