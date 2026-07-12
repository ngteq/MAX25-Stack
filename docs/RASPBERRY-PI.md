# Raspberry Pi — Build, Install, max25d

**Raspberry Pi is a primary deployment target** for MAX25: many operators attach TNCs, BayCom modems, or USB sound cards (CRDOP) directly to the Pi. The full Linux stack — **`max25d`**, BayCom, TNCs, CRDOP — runs natively on Pi OS.

Supported Pi OS: **Raspberry Pi OS** (Debian Bookworm base), **32-bit (armhf)** and **64-bit (aarch64)**. Other ARM SBCs with stock Debian/Ubuntu often work the same way.

## What runs on the Pi

| Component | On Pi | Notes |
|-----------|-------|-------|
| **`max25d`** | Yes | Python 3 — no x86-only code |
| **`max25-terminal`** | Yes | Local UI via Unix socket or `127.0.0.1:7325` |
| **TNC2C / USB TNC** | Yes | `/dev/ttyUSB*`, `/dev/ttyACM*` |
| **BayCom SER12** | Yes | GPIO UART or USB-serial; kernel modules need headers |
| **CRDOP (`soft-crdop`)** | Yes | ALSA; Pi Zero / Zero 2 W tested upstream in CRDOP/ardopcf |
| **HyBBX attach** | Yes | After MAX25 prep — [HYBBX.md](HYBBX.md) |

Remote phones/laptops use **`max25-terminal`** over Wi‑Fi/Ethernet to the Pi’s `max25d` (TCP port **7325**).

---

## Hardware checklist

| Attachment | Typical device | Pi notes |
|------------|----------------|----------|
| USB TNC (TNC2C, KISS) | `/dev/ttyUSB0` | Powered USB hub recommended for RF-heavy setups |
| USB serial BayCom / KISS | `/dev/ttyUSB0` | User in group `dialout` |
| GPIO UART (SER12) | `/dev/ttyAMA0` / `serial0` | Enable UART in `raspi-config`; no console on serial |
| USB sound (CRDOP) | ALSA `plughw:…` | 12 kHz path — see `stacks/crdop` docs |

```bash
# Serial access (logout/login after)
sudo usermod -aG dialout "$USER"

# List serial ports
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/ 2>/dev/null
```

---

## Dependencies (Pi OS)

```bash
sudo apt-get update
sudo apt-get install -y \
  build-essential make cmake pkg-config git \
  python3 \
  libncurses-dev \
  libasound2-dev
```

**BayCom kernel stack** additionally needs kernel headers matching the running kernel:

```bash
sudo apt-get install -y raspberrypi-kernel-headers
# or on generic Debian ARM:
# sudo apt-get install -y linux-headers-$(uname -r)
```

Or use the repo helper:

```bash
./scripts/install-max25.sh --deps
```

---

## Build

From a clone of MAX25-Stack:

```bash
git clone git@github.com:ngteq/MAX25-Stack.git
cd MAX25-Stack

make all          # tncs + baycom-pr + crdop + max25d + max25-terminal
make test
make release-check   # optional offline gates
```

Native build on the Pi (no cross-compile required). CRDOP also supports `aarch64-linux-gnu` cross-build from x86 CI — not needed on-device.

**Memory:** Pi 3/4/5 and Zero 2 W are comfortable for `max25d` + one modem path. Pi Zero (512 MB) works for CRDOP per upstream ardopcf notes; avoid running heavy desktop + multiple stacks simultaneously.

---

## Install

### One-shot (recommended on Pi)

```bash
./scripts/install-max25.sh --deps    # apt packages + build + install
```

Or step by step:

```bash
make all
sudo make install PREFIX=/usr/local
```

Installs:

| Path | Content |
|------|---------|
| `/usr/local/bin/max25d` | Daemon |
| `/usr/local/bin/max25-terminal` | Operator client |
| `/usr/local/bin/max25-client` | Symlink → `max25-terminal` |
| `/usr/local/bin/max25-ctl` | Stack control (legacy entry) |
| `/usr/local/share/max25/` | `max25d.ini` examples, systemd unit example |

### BayCom only (kernel modem)

```bash
make -C stacks/baycom-pr all
sudo make -C stacks/baycom-pr install
sudo bash stacks/baycom-pr/scripts/install-root.sh   # full root setup + preflight
```

See `stacks/baycom-pr/docs/GETTING-STARTED.md`.

---

## Configure max25d on the Pi

Copy and edit site config:

```bash
sudo mkdir -p /etc/max25
sudo cp share/max25/max25d.ini.pi.example /etc/max25/max25d.ini
sudo nano /etc/max25/max25d.ini
```

**Pi example** (`share/max25/max25d.ini.pi.example`) defaults to USB TNC (`tnc2c`). Switch `[daemon]` section for your hardware:

| Hardware | `hardware=` | `device=` |
|----------|-------------|-----------|
| USB TNC2C | `tncs` | `tnc2c` |
| BayCom SER12 | `modems` | `baycom-ser12` |
| CRDOP sound modem | `soft-modems` | `soft-crdop` |

Set `[modem] callerid` / `callid` to your callsigns. Terminals can override live via F10 menu.

---

## Run max25d

### Foreground (debug)

```bash
# Without auto-starting hardware (protocol test):
max25d --no-stack -c /etc/max25/max25d.ini

# With stack (TNC/modem/CRDOP per ini):
sudo max25d -c /etc/max25/max25d.ini
```

`sudo` may be required when `auto_start=yes` launches BayCom kernel paths or binds `/run/max25/modem.sock`. Without root, Unix socket falls back to `/tmp/max25/modem.sock`; TCP **7325** still works.

### systemd (24/7 on Pi)

```bash
sudo cp /usr/local/share/max25/max25d.service.example /etc/systemd/system/max25d.service
# Edit ExecStart path if not /usr/local/bin/max25d
sudo systemctl daemon-reload
sudo systemctl enable --now max25d
sudo systemctl status max25d
journalctl -u max25d -f
```

`RuntimeDirectory=max25` in the unit example provides `/run/max25/` for the Unix socket.

---

## Operator terminal on the Pi

**Local** (same Pi, keyboard + monitor or SSH with TTY):

```bash
max25-terminal -U /run/max25/modem.sock --ax25-ui
# or if no root / no runtime dir:
max25-terminal -H 127.0.0.1 -p 7325 --ax25-ui
```

**Remote** (phone/laptop on LAN):

```bash
max25-terminal -H raspberrypi.local -p 7325 --ax25-ui
```

F10 menu, CALLERID/CALLID: [MAX25-TERMINAL.md](MAX25-TERMINAL.md). Client binding: [MAX25-CLIENT.md](MAX25-CLIENT.md).

---

## Typical Pi workflows

### USB TNC2C

```bash
# /etc/max25/max25d.ini → hardware=tncs device=tnc2c
sudo max25d -c /etc/max25/max25d.ini
# Power-cycle TNC during boot-wait if using auto_start
max25-terminal -U /run/max25/modem.sock
```

HyBBX later: `share/hybbx/tnc2c-edge.ini.example`.

### BayCom on GPIO or USB

```bash
sudo baycom-pr-ctl probe
sudo baycom-pr-ctl setup
# /etc/max25/max25d.ini → hardware=modems device=baycom-ser12
sudo max25d -c /etc/max25/max25d.ini
```

### CRDOP + USB sound

```bash
make -C stacks/crdop all
# Configure ALSA — stacks/crdop/docs/
# /etc/max25/max25d.ini → hardware=soft-modems device=soft-crdop
sudo max25d -c /etc/max25/max25d.ini
```

---

## Troubleshooting (Pi)

| Symptom | Check |
|---------|--------|
| No `/dev/ttyUSB0` | Cable, power hub, `dmesg \| tail`, `lsusb` |
| Permission denied on serial | `groups` → `dialout`; re-login |
| BayCom preflight fails | `sudo baycom-pr-ctl doctor`; IRQ/iobase in `/etc/baycom/baycom-pr.ini` |
| CRDOP no audio | `aplay -l`, `arecord -l`; ALSA device name in crdop config |
| `max25d` bind error on 7325 | `ss -tlnp \| grep 7325`; stop duplicate instance |
| Unix socket EACCES | Run as root, use systemd unit, or use TCP localhost |
| Kernel module build fails | `uname -r` vs installed headers; `raspberrypi-kernel-headers` |

Offline smoke (no hardware):

```bash
max25d --no-stack -c share/max25/max25d.ini.example &
make -C stacks/daemon smoke
```

---

## See also

- [PLATFORMS.md](PLATFORMS.md) — Linux daemon model
- [MAX25-CLIENT.md](MAX25-CLIENT.md) — M25/1 protocol
- [ARCHITECTURE.md](ARCHITECTURE.md) — stack layers
- [stacks/baycom-pr/docs/GETTING-STARTED.md](../stacks/baycom-pr/docs/GETTING-STARTED.md) — BayCom on Linux
- [stacks/crdop/docs/BUILD.md](../stacks/crdop/docs/BUILD.md) — CRDOP build (incl. ARM)
