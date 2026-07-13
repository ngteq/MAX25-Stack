# Linux host setup example

Example **settings and install steps** for running **`max25d`** on a small Linux host with a USB TNC, BayCom modem, or sound-card modem. MAX25 does not recommend specific hardware platforms — use this as a configuration template.

Example INI: `share/max25/max25d.ini.host.example`

---

## What runs on the Linux host

| Component | On Linux host | Notes |
|-----------|---------------|-------|
| **`max25d`** | Yes | Python 3 — no x86-only code |
| **`max25-terminal`** | Yes | Local UI via Unix socket or `127.0.0.1:7325` |
| **TNC2C / USB TNC** | Yes | `/dev/ttyUSB*`, `/dev/ttyACM*` |
| **BayCom SER12** | Yes | UART or USB-serial; kernel modules need headers |
| **CRDOP** — MAX25-SoftModem (`soft-crdop`) | Yes | ALSA sound device |
| **HyBBX attach** | Yes | After MAX25 prep — [HYBBX.md](HYBBX.md) |

Remote operators use **`max25-terminal`** over the network to this host’s `max25d` (TCP port **7325**).

---

## Hardware checklist

| Attachment | Typical device | Notes |
|------------|----------------|-------|
| USB TNC (TNC2C, KISS) | `/dev/ttyUSB0` | Powered USB hub may help RF-heavy setups |
| USB serial BayCom / KISS | `/dev/ttyUSB0` | User in group `dialout` |
| UART (SER12) | `/dev/ttyS*` / `ttyAMA0` | Disable serial console if UART is shared |
| USB sound (CRDOP) | ALSA `plughw:…` | 12 kHz path — see `stacks/crdop` docs |

```bash
# Serial access (logout/login after)
sudo usermod -aG dialout "$USER"

# List serial ports
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/ 2>/dev/null
```

---

## Dependencies (Debian / Ubuntu)

```bash
sudo apt-get update
sudo apt-get install -y \
  build-essential make cmake pkg-config git \
  python3 \
  libncurses-dev \
  libasound2-dev
```

Optional **AX.25 userland** for BayCom kernel sessions (`listen`, `call` via `baycom-pr-ctl`): install distro packages (`ax25-apps`, `libax25`). max25d does **not** use these libraries — it ships `ax25_codec.py` / `kiss_bridge.py`. To build missing host tools from vendored tarballs: `cmake -DMAX25_BUNDLE_AX25=ON` (off by default).

**BayCom kernel stack** additionally needs kernel headers matching the running kernel:

```bash
sudo apt-get install -y linux-headers-$(uname -r)
```

Or use the repo helper:

```bash
./scripts/install-max25.sh --deps
```

---

## Build (CMake)

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
# Default binaries: max25-terminal, tnc2c-probe, baycom_test, CRDOP scaffold, max25d helpers
# Skip SoftModem: cmake -B build -DMAX25_BUILD_CRDOP=OFF && cmake --build build -j$(nproc)
cmake --install build --prefix /usr/local
```

If the tree was moved to another checkout path, remove stale caches first:

```bash
rm -rf build stacks/crdop/build
cmake -B build && cmake --build build -j$(nproc)
```

---

## Install

```bash
./scripts/install-max25.sh --deps    # apt packages + build + install
```

Or step by step:

```bash
./scripts/build.sh
cmake --install build --prefix /usr/local
```

Installs:

| Path | Content |
|------|---------|
| `/usr/local/bin/max25d` | Daemon |
| `/usr/local/bin/kiss_bridge.py` | KISS serial helper (imported by `max25d`) |
| `/usr/local/bin/max25-terminal` | Operator client |
| `/usr/local/bin/max25-client` | Symlink → `max25-terminal` |
| `/usr/local/bin/max25-ctl` | Stack control (legacy entry) |
| `/usr/local/share/max25/` | `max25d.ini` examples, systemd unit example |

### BayCom only (kernel modem, single PC-COM)

```bash
./scripts/build.sh
sudo ./scripts/install-max25.sh          # installs baycom-pr-ctl + /etc/baycom/baycom-pr.ini.example
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
./scripts/max25-ctl start --hardware modems --device baycom-ser12
```

Full operator guide: [BAYCOM.md](BAYCOM.md). Stack internals: `stacks/baycom-pr/docs/GETTING-STARTED.md`.

---

## Configure max25d

Copy and edit site config:

```bash
sudo mkdir -p /etc/max25
sudo cp share/max25/max25d.ini.host.example /etc/max25/max25d.ini
sudo nano /etc/max25/max25d.ini
```

**Host example** (`share/max25/max25d.ini.host.example`) defaults to USB TNC (`tnc2c`). Switch `[daemon]` for your hardware:

| Hardware | `hardware=` | `device=` |
|----------|-------------|-----------|
| USB TNC2C | `tncs` | `tnc2c` |
| BayCom SER12 | `modems` | `baycom-ser12` |
| CRDOP sound modem | `soft-modems` | `soft-crdop` |

Set `[modem] callerid` / `callid` to your callsigns. Terminals can override live via F10 menu.

### Multi-device (optional)

For multiple TNCs on one Linux host, add `[devices]` (see `share/max25/max25d.ini.example`):

```ini
[devices]
default = tnc2c
tnc2c = /dev/ttyUSB0
pktnc2 = /dev/ttyUSB1
```

M25/1: `SET DEVICE <id>`, `GET DEVICES`, `RX device=<id> …` — [MAX25-CLIENT.md](MAX25-CLIENT.md).

---

## Run max25d

### Foreground (debug)

```bash
# Without auto-starting hardware (protocol test):
max25d --no-stack -c /etc/max25/max25d.ini

# With stack (TNC/modem/CRDOP per ini):
sudo max25d -c /etc/max25/max25d.ini
```

`sudo` may be required when `auto_start=yes` launches BayCom kernel paths or binds `/run/max25/modem.sock`. Without root, set `MAX25_UNIX` to a writable path or use TCP **7325** (see `max25d` startup log for the active socket).

### systemd (24/7)

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

## Operator terminal

**Local** (same host, keyboard + monitor or SSH with TTY):

```bash
max25-terminal -U /run/max25/modem.sock --ax25-ui
# or if no root / no runtime dir:
max25-terminal -H 127.0.0.1 -p 7325 --ax25-ui
```

**Remote** (another machine on LAN):

```bash
max25-terminal -T -H linux-host.local -p 7325 -P changeme --ax25-ui
```

F10 menu, CALLERID/CALLID: [MAX25-TERMINAL.md](MAX25-TERMINAL.md). Client binding: [MAX25-CLIENT.md](MAX25-CLIENT.md).

---

## Example workflows

### USB TNC2C

```bash
# /etc/max25/max25d.ini → hardware=tncs device=tnc2c
sudo max25d -c /etc/max25/max25d.ini
max25-terminal -U /run/max25/modem.sock
```

HyBBX later: `share/hybbx/tnc2c-host.ini.example`.

### BayCom on UART (ttyS0)

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
# max25d.ini: hardware=modems device=baycom-ser12 + [device.baycom-ser12] baycom_ini=
sudo max25d -c /etc/max25/max25d.ini
```

See [BAYCOM.md](BAYCOM.md).

### CRDOP (MAX25-SoftModem) + USB sound

```bash
./scripts/build.sh
# Configure ALSA — stacks/crdop/docs/
# /etc/max25/max25d.ini → hardware=soft-modems device=soft-crdop
sudo max25d -c /etc/max25/max25d.ini
```

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| No `/dev/ttyUSB0` | Cable, power hub, `dmesg \| tail`, `lsusb` |
| Permission denied on serial | `groups` → `dialout`; re-login |
| BayCom preflight fails | `sudo baycom-pr-ctl doctor`; IRQ/iobase in `/etc/baycom/baycom-pr.ini` |
| CRDOP no audio | `aplay -l`, `arecord -l`; ALSA device name in crdop config |
| `max25d` bind error on 7325 | `ss -tlnp \| grep 7325`; stop duplicate instance |
| Unix socket EACCES | Run as root, use systemd unit, or use TCP localhost |
| Kernel module build fails | `uname -r` vs installed `linux-headers-$(uname -r)` |

Offline smoke (no hardware):

```bash
max25d --no-stack -c share/max25/max25d.ini.example &
python3 stacks/daemon/test_proto.py && python3 stacks/daemon/test_auth.py
```

---

## See also

- [PLATFORMS.md](PLATFORMS.md) — Linux daemon model
- [MAX25-CLIENT.md](MAX25-CLIENT.md) — M25/1 protocol
- [ARCHITECTURE.md](ARCHITECTURE.md) — stack layers
- [stacks/baycom-pr/docs/GETTING-STARTED.md](../stacks/baycom-pr/docs/GETTING-STARTED.md) — BayCom on Linux
- [stacks/crdop/docs/BUILD.md](../stacks/crdop/docs/BUILD.md) — CRDOP build (incl. ARM)
