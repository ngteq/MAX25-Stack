# Linux host setup · MAX25-Stack 1.8.5-fallback_untested-upcoming#1

Example settings for running `max25d` on a Linux host with USB TNC, BayCom, or sound-card modem.

## Component matrix

| Component | On Linux | Notes |
|-----------|----------|-------|
| `max25d` | yes | Python 3 |
| `max25-terminal` | yes | Unix socket or `127.0.0.1:7325` |
| TNC2C / USB TNC | yes | `/dev/ttyUSB*` |
| BayCom SER12 | yes | kernel modules + headers |
| CRDOP | yes | ALSA sound device |
| HyBBX attach | yes | after MAX25 prep |

## Dependency matrix (Debian/Ubuntu)

| Package group | Packages |
|---------------|----------|
| Build | `build-essential`, `cmake`, `pkg-config`, `git` |
| Runtime | `python3`, `libncurses-dev` |
| CRDOP | `libasound2-dev` |
| BayCom optional | kernel headers matching running kernel |

## Install matrix

| Step | Command |
|------|---------|
| Build | `./scripts/build.sh` |
| INI deploy | copy `share/max25/max25d.ini.host.example` → site config |
| Run daemon | `max25d -c /etc/max25/max25d.ini` |
| Terminal | `max25-terminal -U /run/max25/modem.sock --ax25-ui` |
| Serial access | `usermod -aG dialout $USER` |

## Config matrix

| Item | Value |
|------|-------|
| Live INI | site path or `./local/max25d.ini` |
| M25/1 port | `7325` |
| Secrets | `./local/` only |

## Related

| Goal | Doc |
|------|-----|
| Operator runbook | [MAX25-OPERATOR-RUNBOOK.md](MAX25-OPERATOR-RUNBOOK.md) |
| HyBBX | [HYBBX.md](HYBBX.md) |
