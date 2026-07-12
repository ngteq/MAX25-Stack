# Quick start

**v0.5.0** · [INDEX](INDEX.md) · [MANUAL](MANUAL.md) · [TESTING](TESTING.md)

Default layout: **one modem**. Dual-modem is optional — [Dual modem](#dual-modem-optional).

## Requirements

- Linux with `CONFIG_AX25`; `CONFIG_BAYCOM_SER_FDX` for **kernel-ser12**; `CONFIG_BAYCOM_PAR` + `CONFIG_PARPORT` for **kernel-par96**
- `gcc`, `make`, `python3`, `setserial`, `ip`
- **minicom** (recommended) · **picocom** · **socat** — see [TERMINALS.md](TERMINALS.md)
- Hardware: hardware UART (`/dev/ttyS*`) and/or KISS USB modem (`/dev/ttyUSB*`, `/dev/ttyACM*`)

## 1. Build and install

```bash
git clone https://github.com/ngteq/BayCom_PR-Stack.git
cd BayCom_PR-Stack
make all && make test             # offline QA first
sudo make install
# or: sudo bash scripts/install-root.sh
```

Installs **single-modem** config under `/etc/baycom/` (`baycom-pr.ini`, `modems.ini`, minicom profiles).

## 2. Configure (single modem)

**Automatic (recommended):**

```bash
sudo baycom-pr-ctl probe      # list UART / USB / LPT hardware
sudo baycom-pr-ctl setup      # fill missing iobase/irq/serial in INI
sudo baycom-pr-ctl doctor     # validate + safety check
```

**Manual:** edit `/etc/baycom/baycom-pr.ini` — minimum for ser12 is `serial` + `catalog`; `iobase`/`irq` optional (auto from `setserial`):

```bash
/sbin/setserial -g /dev/ttyS0
sudo baycom-pr-ctl preflight
```

See [AUTOMATION.md](AUTOMATION.md) for the full guided workflow.

USB KISS instead of ser12: set `catalog = kiss-serial-usb`, `serial = /dev/ttyUSB0` (no `iobase`/`irq`).

Parallel par96 on LPT1: copy `config/examples/baycom-pr.par96.ini` — set `iobase = 0x378`, no serial/irq. Guide: [PARPORT.md](PARPORT.md).

## 3. Start and verify (no radio)

```bash
sudo baycom-pr-ctl start
sudo baycom-pr-ctl status
sudo baycom-pr-ctl check         # quick — recommended first
sudo baycom-pr-ctl selftest      # full checklist after install
```

Expected without RF: `bcsf0: UP`, IRQ activity, `dcd=0` / `rx=0`, KISS at `/var/run/baycom-pr/kiss`.

## 4. Attach clients

| Goal | Command |
|------|---------|
| KISS / minicom | `sudo baycom-pr-ctl minicom a` |
| KISS / picocom | `picocom -b 9600 -r -l /var/run/baycom-pr/kiss` |
| AX.25 monitor | Merge [single axports snippet](../config/axports/single.snippet), then `listen -a -c radio` |
| Connect | `call radio DEST` |

More: [TERMINALS.md](TERMINALS.md) · [config/examples/terminals/](../config/examples/terminals/)

**Do not** open `/dev/ttySx` with a terminal while **kernel-ser12** owns the UART.

## Dual modem (optional)

For two modems on one host (separate UARTs):

```bash
sudo cp config/examples/baycom-pr.dual.ini /etc/baycom/baycom-pr.ini
# edit ttyS*, iobase, irq, callsigns — validate each port:
/sbin/setserial -g /dev/ttyS0 /dev/ttyS5
sudo baycom-pr-ctl preflight && sudo baycom-pr-ctl start
```

KISS links: `kiss-a`, `kiss-b`. AX.25: [dual axports snippet](../config/axports/dual.snippet). Details: [MANUAL — Dual modem](MANUAL.md#dual-modem-optional).

Bring up **one modem first**, confirm stable, then switch to dual profile.

## Connection backends

| Backend | Device | Stack path |
|---------|--------|------------|
| **kernel-ser12** | `/dev/ttyS*` | `baycom_ser_fdx` → `bcsf*` → `baycom_kissbridge` |
| **kernel-par96** | LPT `iobase` | `baycom_par` → `bcp*` → `baycom_kissbridge` |
| **kiss-serial** | `/dev/ttyUSB*`, `/dev/ttyACM*` | `baycom_kiss_serial` → `kiss_link` |

Catalog IDs: `baycom-ser12`, `kiss-serial-usb`, … — [MODEMS.md](MODEMS.md).

## Control commands

| Command | Action |
|---------|--------|
| `preflight` | Validate INI + IRQ/UART before start |
| `start` | Release UARTs, `modprobe`, bring up interfaces and KISS bridges |
| `stop` | Tear down (uses `/var/run/baycom-pr/active.env`) |
| `recover` | Post-freeze cleanup |
| `status` | Driver and per-modem summary |
| `check` | Validate INI + quick test (~3 s per modem) |
| `test` | Full offline suite including PTT calibrate |
| `selftest` | Full host checklist — [TESTING.md](TESTING.md) |

## Next

- INI reference: [MANUAL.md](MANUAL.md)
- Config paths: [CONFIGURATION.md](CONFIGURATION.md)
- Modem defaults: [MODEM-SETUP.md](MODEM-SETUP.md)
- USB power: [HARDWARE.md](HARDWARE.md)
