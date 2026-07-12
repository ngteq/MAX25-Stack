# Getting started

BayCom PR-Stack brings a **BayCom-compatible modem** online on Linux: kernel driver or USB KISS, KISS port, and AX.25 for connects. The stack was developed primarily for **HyBBX** (plugin attachment) and works equally with **standard terminal tools** (`listen`, `call`, and other AX.25 clients).

**Your station ID** is always `callsign` in `/etc/baycom/baycom-pr.ini` — edit it once per modem.

**Default:** one modem. Two modems are for **continuous service** (HyBBX, digipeater, automation) — see [GUIDE — Service mode](GUIDE.md#11-service-mode-dual-modem).

New here? Read [GLOSSARY.md](GLOSSARY.md) for terms. Connect examples: [CONNECTS.md](CONNECTS.md).

---

## What you need

| Item | Notes |
|------|-------|
| Linux PC | Generic x86; kernel 6.x typical |
| BayCom-compatible modem | PC-COM, ser12 DIY, USB KISS TNC, or LPT par96 |
| Radio + cable | Operator responsibility |
| Build tools | `gcc`, `make`, `python3` |
| Runtime tools | `setserial` (ser12), `ip`, root for `start` |
| Kernel (ser12) | `CONFIG_AX25`, `CONFIG_BAYCOM_SER_FDX` |
| AX.25 tools (on-air) | `listen`, `call` from ax25-tools package |

---

## Path A — CB single (27 MHz, ser12)

Typical hardware: Albrecht PC-COM / AE8000 on a serial port.

### 1. Install stack

```bash
git clone https://github.com/ngteq/BayCom_PR-Stack.git && cd BayCom_PR-Stack
make all && make test
sudo make install
```

### 2. Use CB profile

```bash
sudo cp config/examples/baycom-pr.cb.ini /etc/baycom/baycom-pr.ini
```

Edit your callsign (station ID):

```bash
sudo nano /etc/baycom/baycom-pr.ini
# [modem.a] callsign = CB0CALL-0   ← your CB ID
```

### 3. Detect hardware and start

```bash
sudo baycom-pr-ctl probe
sudo baycom-pr-ctl setup
sudo baycom-pr-ctl doctor
sudo baycom-pr-ctl start
sudo baycom-pr-ctl selftest
```

### 4. AX.25 port (for listen / call)

`setup` and `start` write `/etc/baycom/axports/axports` from your INI (`ax25_port`, `callsign`) and link `/etc/ax25/axports` automatically:

```bash
sudo baycom-pr-ctl axports show    # preview managed block
sudo baycom-pr-ctl axports apply   # write file + symlink (also runs on start)
sudo baycom-pr-ctl axports check   # verify vs INI
```

Manual merge is optional — snippets remain in `config/axports/` for reference.

### 5. Connect

See [CONNECTS.md](CONNECTS.md) — e.g. `baycom-pr-ctl listen cb0` or `baycom-pr-ctl call cb0 DEST-0`.

---

## Path B — Amateur (HAM) single (1200 bd ser12)

Typical hardware: BayCom ser12, PC-COM, BayPac on UART.

### 1–2. Install and profile

```bash
sudo make install
sudo cp config/examples/baycom-pr.ham.ini /etc/baycom/baycom-pr.ini
sudo nano /etc/baycom/baycom-pr.ini
# [modem.a] callsign = N0CALL-0   ← your amateur callsign + SSID
```

### 3. Start (same as CB)

```bash
sudo baycom-pr-ctl probe && sudo baycom-pr-ctl setup
sudo baycom-pr-ctl doctor && sudo baycom-pr-ctl start
sudo baycom-pr-ctl selftest
```

### 4. AX.25 port

`baycom-pr-ctl start` applies axports from INI. Verify with `baycom-pr-ctl axports check`.

### 5. Connect

`baycom-pr-ctl listen radio` · `baycom-pr-ctl call radio DL1ABC` — or use `listen`/`call` directly. Details in [CONNECTS.md](CONNECTS.md).

---

## Path C — USB KISS (no kernel BayCom driver)

Typical hardware: USB TNC with KISS firmware (FTDI `/dev/ttyUSB0`).

### 1. Install stack

```bash
sudo make install
```

### 2. Minimal INI

Edit `/etc/baycom/baycom-pr.ini` (or copy from default and replace `[modem.a]`):

```ini
[stack]
state_dir = /var/run/baycom-pr
kiss_bridge = yes
catalog = /etc/baycom/modems.ini
bindir = /usr/local/sbin

[profile]
name = usb-kiss
modems = a

[modem.a]
catalog = kiss-serial-usb
label = USB TNC
serial = /dev/ttyUSB0
kiss_baud = 9600
kiss_link = /var/run/baycom-pr/kiss
ax25_port = radio
callsign = N0CALL-0
txdelay = 25
```

No `iobase` / `irq` / `serial` on kernel-ser12 path — the stack uses `baycom_kiss_serial` only.

### 3. Start

```bash
sudo baycom-pr-ctl doctor
sudo baycom-pr-ctl start
sudo baycom-pr-ctl status
```

KISS clients attach to `/var/run/baycom-pr/kiss`. For AX.25 `listen`/`call`, USB KISS still needs an axports line if you use kernel AX.25 apps — many USB setups use KISS-only clients; see [PLUGIN.md](PLUGIN.md).

---

## Daily commands

```bash
sudo baycom-pr-ctl status          # is it up?
sudo baycom-pr-ctl stop            # before shutdown
sudo baycom-pr-ctl recover         # after crash / wrong IRQ
```

| Goal | Doc |
|------|-----|
| Call someone / wait for calls | [CONNECTS.md](CONNECTS.md) |
| HyBBX plugin | [PLUGIN.md](PLUGIN.md) |
| IRQ / freeze safety | [GUIDE §6](GUIDE.md#6-freeze-prevention) |
| All INI fields | [REFERENCE.md](REFERENCE.md) |

---

## Do not

- Open `/dev/ttyS0` with minicom while `baycom_ser_fdx` is loaded — use KISS or `baycom-pr-ctl minicom a` (KISS mode).
- Run two modems on one UART IRQ — preflight blocks duplicate IRQ.
- Use dual-modem profile for everyday single-radio use — use [service mode](GUIDE.md#11-service-mode-dual-modem) only when external software needs two ports.

---

## Next

[CONNECTS.md](CONNECTS.md) — incoming and outgoing examples (CB + HAM).
