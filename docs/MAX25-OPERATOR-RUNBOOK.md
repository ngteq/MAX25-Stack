# Operator runbook · MAX25-Stack

Day-to-day operator procedures for max25d and RF backends.

Public mark for SER12/PC-COM class: **BayCom/based**. Internal workstream: **bcpr**. Never **Konverter** / **converter**.

## Canonical paths

| Component | Path / command |
|-----------|----------------|
| Daemon | **`./scripts/run-max25d.sh`** · `stacks/daemon/max25d` · `/usr/local/bin/max25d` |
| Terminal | **`./scripts/run-max25-terminal.sh`** · `/usr/local/bin/max25-terminal` · `build*/bin/…` |
| bcpr ctl | `stacks/bcpr/tools/bcpr-ctl` or `/usr/local/sbin/bcpr-ctl` |
| TX/RX test | `scripts/tx-rx-test.sh` |
| Site INI | `/etc/max25/max25d.ini` · `/etc/max25/bcpr.ini` |
| Tree INI | `local/max25d.ini` (gitignored) |
| KISS PTY | `/tmp/bcpr/kiss-bc0` (from bcpr.ini `kiss_link`) |
| Unix sock | `/run/max25/modem.sock` |

**Never** `stacks/daemon/max25-terminal` (does not exist).  
**Never** trust a leftover ELF at `stacks/terminal/max25-terminal` — use the launcher or PATH (`--help` must list `-d, --device`).

## Daily workflow (BayCom/based · bcpr)

```bash
cd /home/akb/Code/10-PROJECTS/MAX25-Stack   # or your clone

# 1) daemon (owns bcprd when auto_start=yes) — needs socket dir
sudo mkdir -p /run/max25
sudo ./scripts/run-max25d.sh                 # uses local/max25d.ini or /etc/max25/max25d.ini
# wait for: raw KISS open /tmp/bcpr/kiss-bc0

# 2) terminal (checks socket; picks binary with -d)
./scripts/run-max25-terminal.sh -U /run/max25/modem.sock
# CONNECT (F10→6) → SEND …
```

`connect failed` ⇒ max25d not running (no `/run/max25/modem.sock`). Start step 1 first.

Manual bcpr (only when debugging without max25d):

```bash
sudo ./stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini preflight
sudo ./stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini start
sudo ./stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini status
```

## Device start matrix

| Device | Command |
|--------|---------|
| TNC2C | `max25-ctl start --hardware tncs --device tnc2c` |
| BayCom/based | max25d `[features] bcpr=yes` · device `max25e0` — see [BAYCOM.md](BAYCOM.md) |
| CRDOP | `max25-ctl start --hardware soft-modems --device soft-crdop` |

## TX prove-out

| Path | Command |
|------|---------|
| Unified | `sudo ./scripts/tx-rx-test.sh --device modem --live --tx --tx-seconds 3 -c /etc/max25/bcpr.ini` |
| bcpr smoke | `sudo ./stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini smoke --live --tx --tx-seconds 3` |
| Terminal | `./scripts/run-max25-terminal.sh -U /run/max25/modem.sock` → CONNECT → SEND |

Details: [TX-RX-TEST.md](TX-RX-TEST.md).

### TX path matrix (Zentralnerv)

| Trigger | Host MCR (~3s) | Notes |
|---------|----------------|-------|
| Long KISS → `/tmp/bcpr/kiss-bc0` (info ≈376B, slave held open) | Yes | Proven RF when LED/wattmeter watched |
| `bcpr-rxtx-smoke` / `tx-rx-test` L4 `--tx --tx-seconds 3` | Yes | Requires MCR `0xe`/`0xf` for PASS |
| max25d unix/terminal `SEND` | Yes (shorter if payload ≤256B ≈2.2s) | Keep PTY open (max25d); do not recycle bcprd outside max25d |
| open/write/**close** KISS without hold | No / intermittent | POLLHUP race — fixed in bcprd (POLLIN before HUP) |
| Stale max25d FD after external bcprd restart | No | Restart **max25d** only |

Operator RF evidence (optional, not CI): radio **TX/PTT LED** + **external** wattmeter needle.

**2026-07-19:** Operator confirmed RF on AX25WRK1 (TX LED / external wattmeter) during live prove-out.

## Recovery matrix

| Situation | First action |
|-----------|--------------|
| Echo-only TNC | `tnc2c-host-reset.sh` or serial watch |
| After crash | boot-wait escalate if enabled |
| Cold boot no `cmd:` | `tnc2c-boot-wait.sh` with DTR before power-on |
| Power cycle | rescue fallback only |
| Stale bcpr KISS | restart **max25d** only (do not recycle bcprd outside max25d) |

## Status matrix

| Check | Command |
|-------|---------|
| Daemon | `max25-ctl status` / `ss -ltn \| grep 7325` |
| bcpr | `sudo bcpr-ctl -c /etc/max25/bcpr.ini status` |
| Logs | max25d stdout / site log path |

## Related

| Goal | Doc |
|------|-----|
| Linux setup | [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md) |
| Terminal | [MAX25-TERMINAL.md](MAX25-TERMINAL.md) |
| BayCom/based | [BAYCOM.md](BAYCOM.md) |
| TNC recovery | `stacks/tncs/docs/TNC-RECOVERY.md` |
