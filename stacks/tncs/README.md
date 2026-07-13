# stacks/tncs — Serial TNC tools

Operator tools and docs for **Landolt TNC2C** and **PK-TNC2** (planned). HyBBX attaches via `packet_radio` after MAX25 boot-wait.

## Quick start

```bash
./scripts/build.sh
./scripts/max25-ctl start --hardware tncs --device tnc2c
```

Adjust serial port in `tnc2c-serial.env` before first use.

## Documentation

| Doc | Content |
|-----|---------|
| [docs/TNC2C-OPERATIONS.md](docs/TNC2C-OPERATIONS.md) | Boot-wait, health, HyBBX handoff |
| [docs/TNC2C-REFERENCE.md](docs/TNC2C-REFERENCE.md) | Parameters, tools, example profile |
| [docs/HYBBX-TNC2C.md](docs/HYBBX-TNC2C.md) | HyBBX Secondary attach |

HyBBX INI: [`hybbx-tnc2c.ini`](hybbx-tnc2c.ini) (onboard ttyS4 example) · shipped copy: `../../share/hybbx/tnc2c-host.ini.example` · dual TNC: [`hybbx-dual.ini`](hybbx-dual.ini)

## Tools

| Tool | Purpose |
|------|---------|
| `tnc2c-boot-wait.sh` | Power-on with DTR — host mode |
| `tnc2c-integration-test.sh` | HyBBX-ready check |
| `tnc2c-health.sh` | Serial/TNC check (no TX) |
| `tnc2c-probe` | Scan serial ports for TNC response |
| `pktnc2-boot-wait.sh` | PK-TNC2 (planned) |

## Safety

KISS and TX tests can key the radio. Use a dummy load for transmit tests.
