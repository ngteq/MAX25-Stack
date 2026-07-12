# Configuration reference

**v0.5.0** · INI details: [MANUAL.md](MANUAL.md) · Templates: [config/README.md](../config/README.md)

Canonical paths, file names, and environment variables for BayCom PR-Stack.

## Install layout (`/etc/baycom/`)

All BayCom PR-Stack configuration lives under **`/etc/baycom/`**:

| Path | Source template | Purpose |
|------|-----------------|---------|
| `/etc/baycom/baycom-pr.ini` | `config/baycom-pr.ini` | Site profile (modems, KISS links, AX.25 ports) |
| `/etc/baycom/modems.ini` | `config/modems.ini` | Hardware catalog (`catalog = <id>` in site INI) |
| `/etc/baycom/axports/*.snippet` | `config/axports/` | AX.25 port examples (merge into `/etc/baycom/axports/axports`) |
| `/etc/baycom/rc.d/rc.baycom-pr` | `scripts/rc.baycom-pr` | Optional rc-style init wrapper |
| `/etc/baycom/legacy/pccom.env*` | `config/legacy/pccom.env*` | Deprecated env profiles |

Binaries and runtime:

| Path | Purpose |
|------|---------|
| `/usr/local/sbin/baycom_*` | Binaries and Python tools |
| `/usr/local/sbin/baycom-pr-ctl` | Control script |
| `/var/run/baycom-pr/` | Runtime state (from `state_dir` in INI) |

### Migration from flat `/etc/` paths

If upgrading from an older install, move files into `/etc/baycom/`:

| Old path | New path |
|----------|----------|
| `/etc/baycom-pr.ini` | `/etc/baycom/baycom-pr.ini` |
| `/etc/baycom-modems.ini` | `/etc/baycom/modems.ini` |
| `/etc/pccom.env*` | `/etc/baycom/legacy/pccom.env*` |
| `/etc/ax25/axports` (merged snippets) | `/etc/baycom/axports/axports` |
| `/etc/rc.d/rc.baycom-pr` | `/etc/baycom/rc.d/rc.baycom-pr` |

Update `catalog =` in `baycom-pr.ini` if it still points at the old modems path.

## Site INI (`baycom-pr.ini`)

Default single-modem sections:

```ini
[stack]
state_dir = /var/run/baycom-pr
kiss_bridge = yes
catalog = /etc/baycom/modems.ini
bindir = /usr/local/sbin

[profile]
name = single
modems = a

[modem.a]
catalog = baycom-ser12
serial = /dev/ttyS0
iobase = 0x3f8
irq = 4
iface = bcsf0
kiss_link = /var/run/baycom-pr/kiss
ax25_port = radio
```

Dual-modem template: `config/examples/baycom-pr.dual.ini`.

Parallel port (par96/picpar): `config/examples/baycom-pr.par96.ini` — see [PARPORT.md](PARPORT.md).

Override path: `baycom-pr-ctl -c /path/to/baycom-pr.ini start`.

## Environment variables

| Variable | Used by | Default / notes |
|----------|---------|-----------------|
| `BAYCOM_INI` | `baycom-pr-selftest.sh` | `/etc/baycom/baycom-pr.ini` |
| `BAYCOM_CTL` | selftest | `/usr/local/sbin/baycom-pr-ctl` |
| `BAYCOM_VALIDATE` | selftest | `/usr/local/sbin/baycom_validate_config.py` |
| `BAYCOM_SELFTEST_START` | selftest | `yes` — start stack if down |
| `BAYCOM_SELFTEST_FULL` | selftest | `no` — set `yes` for full PTT/calibrate |
| `BAYCOM_TEST_FULL` | `baycom-pr-ctl test` | unset — set `1` for full tests on dual-modem |
| `BAYCOM_EXPECT_DRIVER` | `baycom_test` | Optional expected driver (`baycom_par`, …) |
| `BAYCOM_SKIP_SERIAL` | `baycom_test` | Set `1` for parport (no `/dev/ttyS*`) |
| `BAYCOM_EXPECT_IRQ` | `baycom_test` | Optional expected IRQ |
| `BAYCOM_SERIAL` | `baycom_test` | Optional serial device |
| `PCCOM_BINDIR` | loaded from INI `[stack] bindir` | Tool search path |

Shell variables emitted by `baycom_ini_load.py` use the `BP_*` prefix (e.g. `BP_MODEM_COUNT`, `BP_M0_SERIAL`).

## Terminology

| Term | Meaning |
|------|---------|
| **BayCom / ser12** | Bell 202 host bit-bang on UART control lines |
| **kernel-ser12** | Backend using `baycom_ser_fdx` on hardware UART |
| **kernel-par96** | Backend using `baycom_par` on parallel port (par96/picpar) |
| **kiss-serial** | Backend using `baycom_kiss_serial` on async KISS |
| **catalog** | Entry in `modems.ini` referenced by `catalog = <id>` |
| **kiss_link** | PTY symlink for KISS clients |
| **ax25_port** | Port name in `/etc/baycom/axports/axports` |

## Quick commands

```bash
python3 tools/baycom_validate_config.py config/baycom-pr.ini
sudo baycom-pr-ctl preflight
sudo cp config/examples/baycom-pr.dual.ini /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl selftest
make test
```
