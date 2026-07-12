# Operator guide

BayCom PR-Stack brings **one modem** online by default, exposes **KISS PTYs** and **AX.25 ports** for packet connects. Developed primarily for **HyBBX** (plugin); works fully with **terminal AX.25 clients** (`listen`, `call`) for CB and Amateur traffic.

**CB** and **HAM** use the same stack — profile templates and `txdelay` differ. **Station ID:** `callsign` in INI.

**New modem owners:** start with [GETTING-STARTED.md](GETTING-STARTED.md) and [CONNECTS.md](CONNECTS.md).

---

## 1. Install

**Requires:** Linux, `gcc`, `make`, `python3`, `setserial`, `ip`; kernel `CONFIG_AX25`, `CONFIG_BAYCOM_SER_FDX` (ser12), optional `CONFIG_BAYCOM_PAR` + `CONFIG_PARPORT` (LPT 9600).

```bash
git clone https://github.com/ngteq/BayCom_PR-Stack.git && cd BayCom_PR-Stack
make all && make test && make verify    # offline QA
sudo make install                       # → /usr/local/sbin + /etc/baycom/
```

---

## 2. First start (3 minutes)

```bash
sudo baycom-pr-ctl probe      # scan UART / USB / LPT
sudo baycom-pr-ctl setup      # auto-fill missing iobase/irq in INI
sudo baycom-pr-ctl doctor     # validate + safety (use --offline in CI only)
sudo baycom-pr-ctl start
sudo baycom-pr-ctl selftest   # offline checklist, no RF
```

---

## 3. Service profiles

| Use case | Template | Install |
|----------|----------|---------|
| **Single (default)** | `config/baycom-pr.ini` | `make install` |
| **CB 27 MHz** | `config/examples/baycom-pr.cb.ini` | `sudo cp … /etc/baycom/baycom-pr.ini` |
| **Amateur HAM** | `config/examples/baycom-pr.ham.ini` | same |
| **USB KISS** | see [GETTING-STARTED §C](GETTING-STARTED.md#path-c--usb-kiss-no-kernel-baycom-driver) | no kernel baycom module |
| **LPT 9600 par96** | `config/examples/baycom-pr.par96.ini` | needs LPT hardware |
| **Service dual** | `config/examples/baycom-pr.dual.ini` | [§11 Service mode](#11-service-mode-dual-modem) only |

Dual modem is **not** for everyday single-radio use — see [§11](#11-service-mode-dual-modem).

### CB vs HAM (equal stack)

| | CB | Amateur |
|--|-----|---------|
| Speed | 1200 bd Bell 202 | 1200 bd (VHF/UHF) · 9600 par96 (LPT) |
| Catalog | `albrecht-pc-com-4500`, `cb-ser12-generic`, `albrecht-pc-com` | `baycom-ser12`, `albrecht-pc-com`, `baypac-bp2` |
| `txdelay` | 30–35 | 20–35 |
| `ax25_port` | `cb0` (your choice) | `radio` (your choice) |

### Minimal INI (ser12)

Only `serial` + `catalog` required — `iobase`/`irq` from `setserial` or `setup`:

```ini
[modem.a]
catalog = albrecht-pc-com
serial = /dev/ttyS0
iface = bcsf0
kiss_link = /var/run/baycom-pr/kiss
callsign = YOURCALL-0
txdelay = 35
ax25_port = cb0
```

USB KISS — no `iobase`/`irq`:

```ini
[modem.a]
catalog = kiss-serial-usb
serial = /dev/ttyUSB0
kiss_baud = 9600
kiss_link = /var/run/baycom-pr/kiss
```

---

## 4. Topology

**Single:** `KISS client → kiss (PTY) → baycom_kissbridge → bcsf0 → baycom_ser_fdx → UART → modem`

**Dual:** two independent chains (`bcsf0`+`bcsf1`, separate IRQ/KISS/ax25_port). One `modprobe baycom_ser_fdx` with comma-separated params.

**Rule:** never open `/dev/ttyS*` with minicom while `baycom_ser_fdx` is loaded — use `kiss_link` or `baycom-pr-ctl minicom`.

---

## 5. Commands

```bash
baycom-pr-ctl [-c /etc/baycom/baycom-pr.ini] COMMAND
```

| Command | Purpose |
|---------|---------|
| `probe` | Hardware scan (UART, USB, LPT) |
| `setup` | Auto-fill INI from probe (creates `.bak`) |
| `doctor` | Full health check |
| `preflight` | Safety gate before start (IRQ/UART) |
| `start` / `stop` / `restart` | Stack control |
| `recover` | Post-crash cleanup |
| `status` | Per-modem summary |
| `check` | Quick test (~3 s, no PTT) |
| `test` | Full offline suite per modem |
| `selftest` | Host checklist |
| `minicom [id] [--kiss\|--serial]` | Terminal attach |
| `axports apply\|show\|check` | Sync `/etc/baycom/axports/axports` from INI |
| `listen [port\|modem]` | Wrapper: `listen -a -c <port>` |
| `call <port> <dest>` | Wrapper: `call <port> <dest>` |

Axports apply runs automatically on `setup` and `start`. Optional boot unit: `config/systemd/baycom-pr.service`.

## 6. Freeze prevention

Wrong IRQ is the #1 host-freeze cause. Built-in protection:

| Layer | Tool |
|-------|------|
| Config validation | `baycom_validate_config.py` |
| Pre-start safety | `preflight` |
| Staged dual start | one UART at a time |
| IRQ storm rollback | auto-stop if >80k IRQ/s |
| Crash cleanup | `recover` |

**Safe workflow (single modem)**

```bash
sudo baycom-pr-ctl preflight && sudo baycom-pr-ctl start
```

**After freeze/reboot**

```bash
sudo baycom-pr-ctl recover
sudo bash scripts/check-freeze.sh
sudo baycom-pr-ctl doctor && sudo baycom-pr-ctl start
```

Service dual workflow: [§11](#11-service-mode-dual-modem).

Env overrides: `BAYCOM_STAGED_START=0` (skip staged), `BAYCOM_MAX_IRQ_PER_SEC=80000`, `BAYCOM_SELFTEST_FULL=no` (default).

---

## 7. Testing (no radio)

| Check | Command |
|-------|---------|
| Repo offline | `make test` · `make verify` |
| Config only | `python3 tools/baycom_validate_config.py /etc/baycom/baycom-pr.ini` |
| With hardware | `sudo baycom-pr-ctl selftest` |
| IRQ activity | `baycom_test irq 2` (while stack up) |
| PTT path | `baycom_test calibrate 2` (optional, needs root) |

On-air RX/TX is operator responsibility — not covered by offline tests.

---

## 8. Terminals

| Tool | When | Example |
|------|------|---------|
| `baycom-pr-ctl minicom a` | Stack up (KISS) | default |
| `baycom-pr-ctl minicom a --serial` | Stack stopped | raw UART |
| picocom | KISS or serial | `picocom -b 9600 /var/run/baycom-pr/kiss` |
| socat | Bridge to TCP | see `config/examples/terminals/` |

Minicom profiles: `/etc/baycom/minicom/minirc.baycom-kiss`, `minirc.baycom-serial`.

---

## 9. Parallel port (par96 / picpar)

G3RUH 9600 bd on LPT — driver `baycom_par`, interfaces `bcp0`..`bcp3`:

```ini
[modem.a]
catalog = baycom-par96
iobase = 0x378
mode = par96
iface = bcp0
options = softdcd
```

No `serial`/`irq`. Requires `parport_pc`. Example: `config/examples/baycom-pr.par96.ini`.

---

## 10. AX.25 ports and connects

`callsign` and `ax25_port` live in INI. `setup` and `start` write `/etc/baycom/axports/axports` and symlink `/etc/ax25/axports` automatically:

```bash
sudo baycom-pr-ctl axports show    # preview
sudo baycom-pr-ctl axports check   # verify vs INI
```

Reference snippets: `config/axports/single.snippet`, `dual.snippet`.

**Incoming / outgoing / monitor:** [CONNECTS.md](CONNECTS.md) (11 copy-paste examples).  
**HyBBX:** [PLUGIN.md](PLUGIN.md).

---

## 11. Service mode (dual modem)

**When:** continuous operation with **two radios** — HyBBX multi-port, digipeater, automation. **Not** for normal single-radio operators.

**Requires:** two UARTs, unique IRQ each, stable power, staged start.

```bash
sudo cp config/examples/baycom-pr.dual.ini /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl setup
sudo setserial -g /dev/ttyS0 /dev/ttyS5    # must match INI (e.g. IRQ 4 + 30)
sudo baycom-pr-ctl preflight               # zero errors
sudo baycom-pr-ctl start                   # staged probe
```

`start` applies axports for both modems from INI (dual snippet is reference only). KISS: `kiss-a`, `kiss-b`. Ports: `cb0`/`cb1` or your names.

Typical PC-COM pair: `ttyS0` IRQ 4 · `ttyS5` IRQ 30 — not IRQ 3 on the second port.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `I/O busy` on modprobe | `baycom-pr-ctl stop`; close minicom on UART |
| Preflight IRQ mismatch | `setserial -g` → fix INI or `setup` |
| Host freeze | `recover`; verify IRQ; start single first |
| KISS link missing | `baycom-pr-ctl start`; check bridge PID in status |
| USB TNC | use `kiss-serial-usb`, not ser12-on-USB-adapter |

Technical reference: [REFERENCE.md](REFERENCE.md) · Connects: [CONNECTS.md](CONNECTS.md) · Developer: [DEVELOPER.md](DEVELOPER.md)
