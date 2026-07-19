# Repository paths · MAX25-Stack

Canonical directory map for contributors and operators.

## Top-level matrix

| Path | Role |
|------|------|
| `stacks/daemon/` | max25d supervisor (`max25d` / `max25d.py`) — **not** the terminal |
| `stacks/terminal/` | operator client (`max25-terminal`) |
| `stacks/tncs/` | TNC boot-wait, recovery |
| `stacks/bcpr/` | BayCom/based SER12 (bcpr) · `bcprd` / `bcpr-ctl` |
| `stacks/crdop/` | MAX25-SoftModem |
| `plugins/` | hardware/device registry |
| `share/max25/` | max25d INI examples |
| `share/hybbx/` | HyBBX attach fragments |
| `docs/` | shipped documentation |
| `scripts/` | build, test, install · `tx-rx-test.sh` |

## Operator binaries (do not invent paths)

| Binary | Canonical |
|--------|-----------|
| max25d | `stacks/daemon/max25d` · install `/usr/local/bin/max25d` |
| max25-terminal | **`scripts/run-max25-terminal.sh`** · `/usr/local/bin/max25-terminal` · `build*/bin/max25-terminal` |
| bcpr-ctl | `stacks/bcpr/tools/bcpr-ctl` · install `/usr/local/sbin/bcpr-ctl` |
| bcprd | `build*/bin/bcprd` · install `/usr/local/bin/bcprd` |
| max25d (start) | **`scripts/run-max25d.sh`** · `stacks/daemon/max25d` |

Wrong: `stacks/daemon/max25-terminal` (does not exist).  
Wrong: relying on leftover ELF `stacks/terminal/max25-terminal` (gitignored; often stale, missing `-d`).

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
