# Operator manual

**v0.5.0** · Templates: `config/baycom-pr.ini`, `config/modems.ini` · Booleans: `yes` / `no`

## Offline operation (no RF)

| Check | How |
|-------|-----|
| Interface | `baycom-pr-ctl status` → `bcsfX: UP` |
| IRQ | `baycom_test irq 2` → delta > 0 |
| Monitor | `dcd=0`, `rx=0` without traffic |
| PTT | `baycom_test calibrate 2` → `during_ptt=1` optional |
| KISS | `ls -l /var/run/baycom-pr/kiss-*` |

On-air validation is separate; not required for v0.5.0 offline sign-off.

## Topology

### Single modem (default)

Standard install — one radio, one KISS link, one AX.25 port:

```
KISS client → kiss (PTY) → baycom_kissbridge → bcsf0 → baycom_ser_fdx → UART → ser12 modem
```

Template: [config/baycom-pr.ini](../config/baycom-pr.ini) · axports: [single.snippet](../config/axports/single.snippet).

### Dual modem (optional)

Two modems on one host — separate UART, IRQ, KISS link, and `ax25_port` each:

```
kiss-a → bcsf0 → ttyS0 / IRQ 4   (modem a)
kiss-b → bcsf1 → ttyS5 / IRQ 30  (modem b)
```

Template: [config/examples/baycom-pr.dual.ini](../config/examples/baycom-pr.dual.ini) · axports: [dual.snippet](../config/axports/dual.snippet).

One `modprobe baycom_ser_fdx` with comma-separated `mode`, `iobase`, `irq`, `baud`. Max four ports (`bcsf0`–`bcsf3`).

**Recommendation:** validate single-modem operation first, then enable dual profile.

**Rule:** Do not use async tools on `/dev/ttySx` while kernel-ser12 owns the UART. Use `kiss_link`, `baycom-pr-ctl minicom`, or AX.25 `axports` names.

## Connection backends

| Backend | Catalog `driver` | Device | Bring-up |
|---------|------------------|--------|----------|
| **kernel-ser12** | `baycom_ser_fdx` | `/dev/ttyS*` | `setserial uart none`, `modprobe`, `bcsf*` |
| **kiss-serial** | `kiss_serial` | `/dev/ttyUSB*`, `/dev/ttyACM*` | `baycom_kiss_serial` → `kiss_link` |

Mixed profile example: modem **a** = ser12 on `ttyS0`, modem **b** = USB KISS on `ttyUSB0`.

**Not supported:** ser12 bit-bang via USB UART only (`unsupported-ser12-usb-adapter`) — use hardware UART or native KISS USB.

USB adapter requirements: [HARDWARE.md](HARDWARE.md).

## baycom-pr-ctl

```bash
baycom-pr-ctl [-c /etc/baycom/baycom-pr.ini] {start|stop|restart|status|test|check|selftest}
baycom-pr-ctl minicom [id] [--kiss|--serial]
```

| Command | Description |
|---------|-------------|
| `start` | `setserial uart none`, `modprobe`, `ip link up`, `baycom_sethdlc`, KISS bridges |
| `stop` | Reads `active.env`, stops bridges, `modprobe -r`, restores UART |
| `status` | Per-modem summary |
| `test` | Full `baycom_test all` per modem |
| `check` | INI + quick test (~3 s, no PTT) |
| `selftest` | Full host checklist — [TESTING.md](TESTING.md) |
| `minicom` | KISS PTY (stack up) or raw UART (stack stopped) |

State: `/var/run/baycom-pr/active.env`.

## minicom

Profiles installed to `/etc/baycom/minicom/minirc.baycom-kiss` and `minirc.baycom-serial`.

| Mode | When | Command |
|------|------|---------|
| KISS | Stack running | `baycom-pr-ctl minicom a` |
| Serial | Stack stopped | `baycom-pr-ctl stop` then `baycom-pr-ctl minicom a --serial` |

**picocom** and **socat:** [TERMINALS.md](TERMINALS.md) · examples in [config/examples/terminals/](../config/examples/terminals/).

## INI: baycom-pr.ini

### `[stack]`

| Key | Default | Description |
|-----|---------|-------------|
| `state_dir` | `/var/run/baycom-pr` | PIDs, KISS symlinks, `active.env` |
| `kiss_bridge` | `yes` | Start `baycom_kissbridge` per kernel-ser12 modem |
| `catalog` | `/etc/baycom/modems.ini` | Modem database path |
| `bindir` | `/usr/local/sbin` | Tool search path |

### `[profile]`

| Key | Description |
|-----|-------------|
| `name` | Profile label |
| `modems` | Comma-separated ids → `[modem.<id>]` |

### `[modem.<id>]`

| Key | Required | Description |
|-----|----------|-------------|
| `catalog` | yes | Id from `modems.ini` |
| `serial` | yes | e.g. `/dev/ttyS0` or `/dev/ttyUSB0` |
| `iface` | yes* | `bcsf0`…`bcsf3` (*kiss-serial may omit) |
| `kiss_link` | no | PTY symlink (default: `state_dir/kiss-<id>`) |
| `ax25_port` | no | AX.25 port name for `axports` |
| `callsign` | no | Operator callsign reference |
| `txdelay` | no | Override catalog (units: 10 ms) |
| `iobase`, `irq` | no* | UART addressing (*kernel-ser12) |
| `kiss_baud` | no | KISS serial speed (default from catalog) |
| `label` | no | Status display name |

Instance keys override catalog `mode`, `baud`, `txdelay`, `driver`.

## INI: modems.ini

| Key | Description |
|-----|-------------|
| `name` | Display name |
| `kind` | `ser12`, `kiss`, `par96`, … |
| `stack` | `supported` \| `planned` \| `unsupported` |
| `driver` | `baycom_ser_fdx`, `kiss_serial`, `baycom_par`, … |
| `mode` | Kernel modprobe mode (`ser12*`, `ser3*`, …) |
| `baud` | Module baud parameter |
| `txdelay` | Default TX delay (×10 ms) |
| `chip`, `pinout`, `dcd`, `notes`, `ref` | Reference fields |

Full list: [MODEMS.md](MODEMS.md). Defaults: [MODEM-SETUP.md](MODEM-SETUP.md).

## Kernel driver (manual equivalent)

```bash
setserial /dev/ttyS0 uart none
modprobe baycom_ser_fdx mode='ser12*' iobase=0x3f8 irq=4 baud=1200
ip link set bcsf0 up
baycom_sethdlc bcsf0 35
baycom_kissbridge -i bcsf0 -l /var/run/baycom-pr/kiss-a
```

Mode suffix: `*` = software DCD (recommended); `+` = hardware DCD inverted.

## Tools

| Tool | Usage |
|------|-------|
| `baycom_sethdlc` | `baycom_sethdlc bcsf0 35` — TX delay in 10 ms units |
| `baycom_test` | `baycom_test -i bcsf0 -s /dev/ttyS0 all` — [TESTING.md](TESTING.md) |
| `baycom_validate_config.py` | INI validation (no root) |
| `baycom_kissbridge` | `baycom_kissbridge -i bcsf0 -l /var/run/baycom-pr/kiss-a` |

Env (optional): `BAYCOM_EXPECT_IOBASE`, `BAYCOM_EXPECT_IRQ`, `BAYCOM_SERIAL`.

## AX.25

**Single modem** — merge [config/axports/single.snippet](../config/axports/single.snippet):

```
radio    N0CALL-0   1200   255   2   BayCom ser12
```

**Dual modem** — merge [config/axports/dual.snippet](../config/axports/dual.snippet):

```
cb0    N0CALL-0   1200   255   2   Modem A
cb1    N0CALL-1   1200   255   2   Modem B
```

Apps use **axports name**, not `bcsfX` directly.

## External clients

Stable attachment points for downstream software (no application layer in this repo):

| Client | Attach via |
|--------|------------|
| KISS programs | `kiss_link` path |
| `listen`, `call` | `ax25_port` in `axports` |
| minicom, picocom, socat | [TERMINALS.md](TERMINALS.md) |

## Boot-time start (optional)

`scripts/rc.baycom-pr` is a small **rc-style** wrapper (`start` / `stop` / `restart` / `status`). Install it wherever your Linux init layout expects local scripts, or call `baycom-pr-ctl` from your own unit/cron.

Example (rc-style layout):

```bash
install -m 755 scripts/rc.baycom-pr /etc/baycom/rc.d/rc.baycom-pr
/etc/baycom/rc.d/rc.baycom-pr start
```

Or run manually after boot: `baycom-pr-ctl start`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `modprobe` EBUSY | `setserial /dev/ttySx uart none` |
| `sethdlc` EINVAL | Use `baycom_sethdlc` only |
| IRQ test 0 | Wrong IRQ; shared IRQ — use current `baycom_test` |
| KISS bridge exits | `state_dir/kissbridge-<iface>.log` |
| PTT fail | Cable, TXD power — [HARDWARE.md](HARDWARE.md) |
| Post-reboot freeze | `baycom-pr-ctl recover` then [STABILITY.md](STABILITY.md) |
