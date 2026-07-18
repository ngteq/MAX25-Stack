# Stability and freeze prevention

**v0.5.0** · [TESTING.md](TESTING.md) · [HARDWARE.md](HARDWARE.md) · shipped warning: [BAYCOM-FREEZES.md](../../../../docs/BAYCOM-FREEZES.md)

Kernel-ser12 (`baycom_ser_fdx`) bit-bangs UART control lines under interrupt load. **Wrong IRQ, UART conflicts, dual-modem misconfiguration, SER12 TX/calibrate, or RF EMI near the host can freeze the machine.** This document describes safeguards built into the stack and safe operating procedure.

## Built-in safeguards

| Layer | What it does |
|-------|----------------|
| `baycom_preflight.py` | Before `start`: INI validation, IRQ/iobase vs `setserial`, duplicate IRQ, serial not open in userspace |
| `post_start_irq_watch` | After driver load: samples IRQ rate; auto-**stop** if storm (>80k/s default) |
| `staged dual start` | Dual kernel-ser12: probes **one UART at a time** before combined modprobe |
| `baycom_validate_config.py` | Duplicate iobase/irq → **error** (not warning) |
| `baycom_test` | Caps test duration; detects extreme IRQ rates |
| `selftest` | Default **quick** tests only (`BAYCOM_SELFTEST_FULL=yes` for PTT/calibrate) |
| `test` on dual-modem | Uses **quick** unless `BAYCOM_TEST_FULL=1` |
| `recover` | Post-crash cleanup: stop bridges, unload driver, restore UARTs |

## Safe workflow

### Single modem (recommended first)

```bash
sudo baycom-pr-ctl preflight
sudo baycom-pr-ctl start
sudo baycom-pr-ctl check          # quick — no PTT
sudo baycom-pr-ctl status
```

### Dual modem (after single is stable)

```bash
sudo cp config/examples/baycom-pr.dual.ini /etc/baycom/baycom-pr.ini
# Verify EACH port (reference station PC-COM: ttyS0 IRQ4, ttyS5 IRQ30):
/sbin/setserial -g /dev/ttyS0 /dev/ttyS5
sudo baycom-pr-ctl preflight     # must pass with zero errors
sudo baycom-pr-ctl start         # staged probe per UART, then full load
sudo baycom-pr-ctl check
```

### After unexpected reboot / freeze

```bash
sudo baycom-pr-ctl recover
sudo bash scripts/check-freeze.sh   # save report
sudo baycom-pr-ctl preflight
# fix INI / IRQ if preflight failed
sudo baycom-pr-ctl start
```

## Rules (do not skip)

1. **Never** open `/dev/ttyS*` with a userspace serial client while `baycom_ser_fdx` owns the UART — use `kiss_link` only.
2. **Always** run `setserial … uart none` before start (done by `baycom-pr-ctl start`).
3. **Always** run `baycom-pr-ctl stop` before shutdown/reboot when possible.
4. **Verify IRQ** in INI matches `setserial -g` — mismatch is the #1 freeze cause.
5. **Dual-modem:** each UART needs a **unique** IRQ and correct iobase.
6. Start with **single-modem** profile until stable; then enable dual.

## Commands

```bash
baycom-pr-ctl preflight    # read-only safety check (no driver load)
baycom-pr-ctl recover      # teardown after crash or before retry
baycom-pr-ctl check        # quick health (preferred over test)
baycom-pr-ctl test         # full suite — use BAYCOM_TEST_FULL=1 only when stable
```

## Environment overrides

| Variable | Default | Effect |
|----------|---------|--------|
| `BAYCOM_SKIP_PREFLIGHT` | unset | `1` = skip preflight on start (not recommended) |
| `BAYCOM_STAGED_START` | `auto` | `0` = skip per-UART probe on dual start; `auto`/`1` = enabled for 2+ kernel modems |
| `BAYCOM_MAX_IRQ_PER_SEC` | `80000` | Abort start if IRQ rate exceeds this |
| `BAYCOM_SELFTEST_FULL` | `no` | `yes` = selftest runs PTT/calibrate |
| `BAYCOM_TEST_FULL` | unset | `1` = full `test` on dual-modem |
| `BAYCOM_TEST_SAFE` | unset | `1` = force quick tests |

## Typical freeze causes

| Cause | Prevention |
|-------|------------|
| Wrong IRQ in INI | `preflight` + `setserial -g` |
| Duplicate IRQ (dual) | `preflight` / validator |
| Userspace serial on raw UART while driver loaded | Use KISS PTY only |
| IRQ storm (bad hardware/address) | Auto rollback on `start` |
| Skipping `stop` before reboot | `recover` after boot |
| Full PTT test on unstable dual setup | Default quick selftest |

## Diagnostics

```bash
sudo bash scripts/check-freeze.sh
grep -E 'baycom|bcsf|lockup|hung' ~/baycom-pr-freeze-report.txt
watch -n1 'grep -E "ttyS|baycom" /proc/interrupts'   # while stack runs
```

## Related

- [QUICKSTART.md](QUICKSTART.md) — single-modem default
- [config/examples/baycom-pr.dual.ini](../config/examples/baycom-pr.dual.ini) — optional dual profile
- [MANUAL.md — Troubleshooting](MANUAL.md#troubleshooting)
