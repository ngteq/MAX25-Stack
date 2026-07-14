# Operator runbook · MAX25-Stack 1.5.0

Day-to-day operator procedures for max25d and RF backends.

## Daily workflow matrix

| Step | Action |
|------|--------|
| 1 | Verify INI — `./local/` or `/etc/max25/max25d.ini` |
| 2 | Start max25d | `max25d -c <ini>` |
| 3 | Verify M25/1 | `ss -ltn | grep 7325` |
| 4 | Operator UI | `max25-terminal` |
| 5 | HyBBX (if used) | after MAX25 prep — see [HYBBX.md](HYBBX.md) |

## Device start matrix

| Device | Command |
|--------|---------|
| TNC2C | `max25-ctl start --hardware tncs --device tnc2c` |
| BayCom | `max25-ctl start --hardware modems --device baycom-ser12` |
| CRDOP | `max25-ctl start --hardware soft-modems --device soft-crdop` |

## Recovery matrix

| Situation | First action |
|-----------|--------------|
| Echo-only TNC | `tnc2c-host-reset.sh` or serial watch |
| After crash | boot-wait escalate if enabled |
| Cold boot no `cmd:` | `tnc2c-boot-wait.sh` with DTR before power-on |
| Power cycle | rescue fallback only |

## Status matrix

| Check | Command |
|-------|---------|
| Daemon | `max25-ctl status` |
| Ports | `ss -ltn | grep -E '7325|8515'` |
| Logs | max25d stdout / site log path |

## Related

| Goal | Doc |
|------|-----|
| Linux setup | [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md) |
| TNC recovery | `stacks/tncs/docs/TNC-RECOVERY.md` |
