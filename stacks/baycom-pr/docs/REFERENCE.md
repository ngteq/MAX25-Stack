# Technical reference

## Backends

| Backend | Driver | Device | Interface | Module |
|---------|--------|--------|-----------|--------|
| **kernel-ser12** | `baycom_ser_fdx` | `/dev/ttyS*` | `bcsf0`..`bcsf3` | `baycom_ser_fdx`, `ax25` |
| **kernel-par96** | `baycom_par` | LPT iobase | `bcp0`..`bcp3` | `baycom_par`, `parport_pc` |
| **kiss-serial** | `kiss_serial` | `/dev/ttyUSB*`, `/dev/ttyACM*` | — (PTY only) | none |

Mixed profiles load ser12 and par96 as **separate** kernel modules. Max four ports per driver type.

**Not supported:** ser12 bit-bang via USB-UART adapter only (`unsupported-ser12-usb-adapter` in catalog).

---

## Install paths

| Path | Content |
|------|---------|
| `/etc/baycom/baycom-pr.ini` | Site profile |
| `/etc/baycom/modems.ini` | Hardware catalog |
| `/etc/baycom/minicom/` | Minicom profiles |
| `/etc/baycom/axports/` | AX.25 snippets + local `axports` |
| `/etc/baycom/examples/` | Profile templates |
| `/etc/baycom/legacy/` | Deprecated `pccom.env*` |
| `/usr/local/sbin/baycom_*` | Binaries + Python tools |
| `/var/run/baycom-pr/` | Runtime (`state_dir`, KISS links, `active.env`) |

---

## Site INI schema

### `[stack]`

| Key | Default | Description |
|-----|---------|-------------|
| `state_dir` | `/var/run/baycom-pr` | Runtime directory |
| `kiss_bridge` | `yes` | Start KISS bridge per kernel modem |
| `catalog` | `/etc/baycom/modems.ini` | Modem database |
| `bindir` | `/usr/local/sbin` | Tool search path |

### `[profile]`

| Key | Description |
|-----|-------------|
| `name` | Profile label |
| `modems` | Comma-separated modem IDs (`a`, `b`, …) |

### `[modem.<id>]`

| Key | Required | Description |
|-----|----------|-------------|
| `catalog` | yes | ID from `modems.ini` (without `modem.` prefix) |
| `serial` | ser12/kiss | Device path |
| `iobase` | ser12* | Hex port address; auto from setserial if omitted |
| `irq` | ser12* | UART IRQ; auto from setserial if omitted |
| `iface` | kernel | `bcsfN` or `bcpN`; auto from catalog if omitted |
| `mode` | par96 | `par96` or `picpar` |
| `options` | par96 | `softdcd` for par96 software DCD |
| `kiss_link` | yes | KISS PTY symlink path |
| `kiss_baud` | kiss | Default 9600 |
| `txdelay` | no | ×10 ms; catalog default if omitted |
| `ax25_port` | no | Name in `axports` |
| `callsign` | no | Your station ID (CB or amateur); must match `axports` |

\* ser12: `iobase`/`irq` optional if `setserial` works; required at runtime via preflight.

---

## Catalog highlights

Full list: `config/modems.ini` · 25 entries.

| ID | Product | Backend | Speed |
|----|---------|---------|-------|
| `albrecht-pc-com` | PC-COM / AE8000 | ser12 | 1200 |
| `albrecht-pc-com-4500` | PC-COM 4500 CB | ser12 | 1200 |
| `cb-ser12-generic` | Generic CB ser12 | ser12 | 1200 |
| `baycom-ser12` | DIY BayCom | ser12 | 1200 |
| `baypac-bp2` / `bp2m` | Tigertronics BayPac | ser12 | 1200/300 |
| `kiss-serial-usb` | USB KISS TNC | kiss | 9600 |
| `kiss-serial-rs232` | RS-232 KISS | kiss | 9600 |
| `baycom-par96` | LPT G3RUH 9600 | par96 | 9600 |
| `baycom-picpar` | DF9IC picpar | par96 | 9600 |

`stack = unsupported`: SCC cards, LPT ser12 bit-bang, ser12-on-USB-only.

---

## ser12 DE-9 pinout (PC side)

| Pin | Signal | Function |
|-----|--------|----------|
| 3 | TXD | Modem power (+12 V pump) |
| 4 | DTR | TX data |
| 5 | GND | Ground |
| 7 | RTS | PTT (high = TX) |
| 8 | CTS | RX data |

Kernel modes: `ser12*` (1200 FDX), `ser3*` (300 HF). Driver: `baycom_ser_fdx` (preferred) or `baycom_ser_hdx` (fallback, `bcsh*`).

---

## LPT addresses (par96)

| Port | iobase |
|------|--------|
| LPT1 | `0x378` |
| LPT2 | `0x278` |
| LPT3 | `0x3bc` |

`modprobe baycom_par mode=par96 iobase=0x378` — no `irq` param (parport subsystem).

---

## Environment variables

| Variable | Default | Effect |
|----------|---------|--------|
| `BAYCOM_INI` | `/etc/baycom/baycom-pr.ini` | selftest INI path |
| `BAYCOM_SKIP_PREFLIGHT` | unset | `1` = skip preflight on start |
| `BAYCOM_STAGED_START` | `auto` | `0` = skip dual staged probe |
| `BAYCOM_MAX_IRQ_PER_SEC` | `80000` | IRQ storm abort threshold |
| `BAYCOM_SELFTEST_FULL` | `no` | `yes` = PTT/calibrate in selftest |
| `BAYCOM_TEST_FULL` | unset | `1` = full test on dual |
| `BAYCOM_EXPECT_IOBASE` | — | `baycom_test` expected iobase |
| `BAYCOM_EXPECT_IRQ` | — | `-1` skips IRQ check (par96) |
| `BAYCOM_SKIP_SERIAL` | — | `1` = skip UART test (par96) |

Legacy aliases: `PCCOM_*` still read by tools.

---

## Python tools

| Script | Purpose |
|--------|---------|
| `baycom_ini_load.py` | INI → shell vars for `baycom-pr-ctl` |
| `baycom_validate_config.py` | Schema validation |
| `baycom_preflight.py` | Pre-start hardware safety |
| `baycom_probe.py` | Hardware scan + `--apply` |
| `baycom_doctor.py` | Unified health (`--offline` for CI) |

---

## Glossary

| Term | Meaning |
|------|---------|
| **catalog** | Hardware template in `modems.ini` |
| **kiss_link** | Symlink to KISS PTY for clients |
| **staged probe** | Dual start: one port at a time |
| **offline verified** | Stack tests pass without RF |

Kernel deep-dive: [kernel/BAYCOM-DRIVER-ANALYSIS.md](kernel/BAYCOM-DRIVER-ANALYSIS.md)
