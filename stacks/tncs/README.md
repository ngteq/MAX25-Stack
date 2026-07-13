# stacks/tncs — Serial TNC tools

Operator tools and docs for **Landolt TNC2C** and **PK-TNC2** (TheFirmware TNC-2 class). HyBBX attaches via `packet_radio` after MAX25 prep.

**Recovery:** software-first (no power cycle in normal ops). Power-cycle boot-wait is rescue only. See [docs/TNC-RECOVERY.md](docs/TNC-RECOVERY.md).

## Quick start

```bash
./scripts/build.sh
./scripts/max25-ctl start --hardware tncs --device tnc2c
```

Adjust serial port in `tnc2c-serial.env` before first use.

## Documentation

| Doc | Content |
|-----|---------|
| [docs/TNC-RECOVERY.md](docs/TNC-RECOVERY.md) | Software ladder, rescue power-cycle |
| [docs/TNC2C-OPERATIONS.md](docs/TNC2C-OPERATIONS.md) | Boot-wait, health, HyBBX handoff |
| [docs/TNC2C-REFERENCE.md](docs/TNC2C-REFERENCE.md) | Parameters, tools, example profile |
| [docs/HYBBX-TNC2C.md](docs/HYBBX-TNC2C.md) | HyBBX Secondary attach |

HyBBX INI: [`hybbx-tnc2c.ini`](hybbx-tnc2c.ini) (onboard ttyS4 example) · shipped copy: `../../share/hybbx/tnc2c-host.ini.example` · dual TNC: [`hybbx-dual.ini`](hybbx-dual.ini)

## Tools

| Tool | Purpose |
|------|---------|
| `tnc2c-host-reset.sh` | Software recovery (no power cycle) |
| `tnc2c-boot-wait.sh` | DTR during power-on — **rescue**; `--recover-only` for ladder only |
| `pktnc2-boot-wait.sh` | PK-TNC2 wrapper (9600 8N1); supports `--recover-only` |
| `tnc2c-integration-test.sh` | HyBBX-ready check |
| `tnc2c-health.sh` | Serial/TNC check (no TX) |
| `tnc2c-probe` | Scan serial ports for TNC response |

## Safety

KISS and TX tests can key the radio. Use a dummy load for transmit tests.
