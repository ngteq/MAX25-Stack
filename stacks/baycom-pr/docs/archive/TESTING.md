# Testing guide

**v0.5.0** — all commands below run **without a transceiver**. On-air tests are separate.

## Which test when?

| Situation | Command | Time | Proves |
|-----------|---------|------|--------|
| First install | `sudo baycom-pr-ctl selftest` | 1–2 min | Deps, config, stack, KISS |
| After INI edit | `baycom-pr-ctl check` | ~10 s | INI + quick per-modem |
| Before radio | `sudo baycom-pr-ctl test` | ~30 s/modem | Full offline incl. PTT |
| Config only | `make test-config` | instant | INI + catalog refs |
| Repo QA | `make test` | ~5 s | Build, scripts, layout |
| After crash | `sudo bash scripts/check-freeze.sh` | instant | Kernel log hints |
| Stability | `sudo baycom-pr-ctl preflight` | instant | IRQ/UART/config before start |
| After freeze/reboot | `sudo baycom-pr-ctl recover` | instant | Clean teardown |

## selftest (recommended)

```bash
sudo baycom-pr-ctl selftest
# or: sudo bash scripts/baycom-pr-selftest.sh
```

Steps: validate INI → **preflight** → check deps → build if needed → start stack → `check` → (optional full test) → verify KISS symlinks.

Default: **quick tests only**. Full PTT/calibrate: `BAYCOM_SELFTEST_FULL=yes sudo baycom-pr-ctl selftest`

See [STABILITY.md](STABILITY.md) for freeze prevention.

Pass = safe to attach KISS/max25-terminal/AX.25 clients. **Does not** prove on-air decodes.

## baycom-pr-ctl

```bash
baycom-pr-ctl check      # INI + quick test (stack up for modem part)
baycom-pr-ctl test       # full offline suite per modem
baycom-pr-ctl selftest   # everything + dependencies
baycom-pr-ctl status     # snapshot only
```

## baycom_test (per modem)

```bash
sudo baycom_test -i bcsf0 -s /dev/ttyS0 all
sudo baycom_test -i bcsf0 quick       # ~3 s, no PTT
sudo baycom_test irq 2
sudo baycom_test monitor 5
sudo baycom_test calibrate 2          # keys PTT — no RF
```

Environment (optional):

```bash
export BAYCOM_EXPECT_IOBASE=0x3f8 BAYCOM_EXPECT_IRQ=4 BAYCOM_SERIAL=/dev/ttyS0
```

## Expected results (no radio)

| Test | Normal |
|------|--------|
| Interface | `UP` |
| IRQ delta | > 0 (often 200–800/s total) |
| Monitor | `dcd=0`, `rx=0` |
| Calibrate | `during_ptt=1` |
| KISS | symlink → `/dev/pts/N` |

## Pre-flight (stack stopped)

```bash
/sbin/setserial -g /dev/ttyS0
python3 tools/baycom_validate_config.py /etc/baycom/baycom-pr.ini
```

## On-air (later — not v0.5.0 sign-off)

1. `listen -a -c cb0` — watch decodes
2. `call cb0 DEST` — connect test
3. Compare IRQ/RX during traffic

## Troubleshooting

| Failure | Likely fix |
|---------|------------|
| INI validation | Fix `serial`, `iobase`, `irq`, `catalog` |
| `modprobe` EBUSY | `setserial … uart none` |
| IRQ delta 0 | Wrong IRQ — `setserial -g` |
| PTT fail | Cable, TXD power — [HARDWARE.md](HARDWARE.md) |
| KISS missing | `kiss_bridge=yes`; check `kissbridge-*.log` |
| USB KISS garbled | Wrong `kiss_baud`; power — [HARDWARE.md](HARDWARE.md) |
| ser12 on USB | Use hardware UART or `kiss-serial-usb` |

Run `selftest` before pointing external clients at `kiss_link` paths.
