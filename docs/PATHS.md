# Repository paths · MAX25-Stack 1.5.0

Canonical directory map for contributors.

## Top-level matrix

| Path | Role |
|------|------|
| `stacks/daemon/` | max25d supervisor |
| `stacks/terminal/` | operator client |
| `stacks/tncs/` | TNC boot-wait, recovery |
| `stacks/baycom-pr/` | kernel BayCom |
| `stacks/crdop/` | MAX25-SoftModem |
| `plugins/` | hardware/device registry |
| `share/max25/` | max25d INI examples |
| `share/hybbx/` | HyBBX attach fragments |
| `docs/` | shipped documentation |
| `scripts/` | build, test, install |

## Config matrix

| Live config | Path |
|-------------|------|
| Operator secrets | `./local/` (gitignored) |
| System INI example | `share/max25/max25d.ini.example` |
| HyBBX fragments | `share/hybbx/*-host.ini.example` |

## Related

| Goal | Doc |
|------|-----|
| Development | [DEVELOPMENT.md](DEVELOPMENT.md) |
| Doc index | [README.md](README.md) |
