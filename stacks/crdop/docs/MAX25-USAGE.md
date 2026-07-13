# CRDOP in MAX25-Stack — usage guide

Complete operator and integrator workflow for **MAX25-SoftModem (CRDOP)** inside MainAX25-Stack.

**CRDOP** = **CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio). Project rule: [docs/CRDOP.md](../../../docs/CRDOP.md).

**Versions:** MAX25-Stack **v1.0.0** · CRDOP **CUR999** (pre-release until **v0.5**).

**Dependency:** CRDOP sources are standalone-capable in principle, but **MAX25-Stack is required** for build, `max25d`, INI, operator tooling, and plugin registry until **CRDOP-v1.0.0** marks a mature standalone release.

---

## Quick start

```bash
# 1. Build (CRDOP ON by default)
./scripts/build.sh

# 2. Configure daemon
sudo cp share/max25/max25d.ini.example /etc/max25/max25d.ini
# Edit: enable soft-crdop block (see below)

# 3. Start stack
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop

# 4. Terminal session
max25-terminal -U /run/max25/modem.sock
# or TCP: max25-terminal -H 127.0.0.1 -P 7325
```

Inside terminal: `SET DEVICE soft-crdop` → `CONNECT` → `SEND …`

---

## Build and install

### CMake options

| Option | Default | Effect |
|--------|---------|--------|
| `MAX25_BUILD_CRDOP` | **ON** | Build/install CRDOP scaffold + tools |
| `MAX25_BUILD_DAEMON` | ON | `max25d` with `CrdopTcpBackend` |
| `MAX25_BUILD_TERMINAL` | ON | `max25-terminal` / `max25-client` |
| `CRDOP_VENDOR_ARDOPCF` | OFF | Dev-only legacy ARDOP — **never** in releases |

Disable CRDOP only when not needed:

```bash
cmake -B build -DMAX25_BUILD_CRDOP=OFF
cmake --build build -j$(nproc)
```

### Install tree

After `cmake --install` (or `./scripts/build.sh` + local prefix):

| Path | Contents |
|------|----------|
| `bin/crdop` | Launcher — starts `audio-dummyd` with INI |
| `bin/audio-dummyd` | M25 host TCP daemon + acoustic engine |
| `bin/max25-signal-sniffer` | Bell 202 analysis |
| `share/crdop/crdop.ini.example` | CB profile template |
| `share/crdop/crdop-dual.ini.example` | CB ↔ amateur preset |
| `share/crdop/crdop-amateur.ini.example` | Amateur secondary preset |
| `share/crdop/lib/*.py` | DSP modules (installed for tooling) |
| `share/crdop/VERSION` | `CUR999` |
| `share/hybbx/crdop-host.ini.example` | HyBBX Secondary attach |
| `share/clients/soft-crdop.yaml` | Terminal device profile |

---

## Plugin model

| Plugin id | Type | Hardware family | Role |
|-----------|------|-----------------|------|
| `soft-crdop` | device | `soft-modems` | Production sound-card modem |
| `audio-dummy` | device | `acoustic-bench` | Bench — loopback / ALSA / host |
| `soft-modems` | hardware | — | CRDOP device family |
| `acoustic-bench` | hardware | — | Dev/test without RF |

Registry: `plugins/manifest.yaml`. Discovery:

```bash
./scripts/discover-plugins.sh --json | jq '.devices[] | select(.id|test("crdop|audio-dummy"))'
```

---

## max25d configuration

### Production path — `soft-crdop`

```ini
[daemon]
hardware = soft-modems
device = soft-crdop

[devices]
default = soft-crdop
soft-crdop = crdop:default

[device.soft-crdop]
host = 127.0.0.1
port = 8515
listen = yes
ardop_compat = no
```

`max25-ctl start` launches `crdop` (→ `audio-dummyd`) when `auto_start = yes` in `[stack]`.

### Bench path — `audio-dummy`

No RF; validates DSP loopback or ALSA capture:

```ini
[daemon]
hardware = acoustic-bench
device = audio-dummy

[devices]
default = audio-dummy
audio-dummy = audio:loopback
```

Modes for `audio-dummy` spec:

| Spec | Behaviour |
|------|-----------|
| `audio:loopback` | Internal DSP encode/decode |
| `audio:alsa:plughw:N,M` | Sniff live ALSA capture |
| `audio:host` | Attach to running `audio-dummyd` on :8515 |

Start bench:

```bash
./scripts/max25-ctl start --hardware acoustic-bench --device audio-dummy
max25-terminal -U /run/max25/modem.sock
```

### Sniffer (no daemon)

```bash
max25-signal-sniffer --loopback
max25-signal-sniffer -D plughw:1,0 -t 3.0
max25-signal-sniffer --mark    # 1200 Hz calibration tone
max25-signal-sniffer --space   # 2200 Hz calibration tone
```

---

## crdop.ini (modem side)

Copy and edit:

```bash
mkdir -p ~/.config/crdop
cp share/crdop/crdop.ini.example ~/.config/crdop/crdop.ini
```

Key sections — full reference: [CONFIG.md](CONFIG.md).

```ini
[profile]
radio_profile = cb          ; cb | dual | amateur

[modem]
duplex = half               ; half | full
arq_bandwidth = 500MAX

[mycall]
call = CB01-0

[audio]
backend = alsa-kernel
no_pulse = yes
capture = plughw:1,0
playback = plughw:1,0

[host]
port = 8515

[compat]
ardop_compat = no           ; yes = ARDOP-plugin wire mode
```

Launch:

```bash
CRDOP_INI=~/.config/crdop/crdop.ini ./scripts/crdopc
# or after install:
crdop
```

---

## max25-terminal / M25/1

CRDOP uses the same M25/1 session flow as other `max25d` device backends:

```
SET DEVICE soft-crdop
CONNECT
SEND Hello packet world
```

| Item | Value |
|------|-------|
| Daemon socket | `/run/max25/modem.sock` (Linux) |
| Daemon TCP | `7325` (configurable in `max25d.ini`) |
| Modem host TCP | `8515` ctrl, `8516` data (CRDOP native) |
| Client profile | `share/clients/soft-crdop.yaml` |

Protocol reference: [PROTOCOL.md](PROTOCOL.md) · [include/max25/protocol.md](../../../include/max25/protocol.md).

When `ax25_ui = yes` in `max25d.ini`, terminal `SEND` lines encode as AX.25 UI frames.

---

## HyBBX attach

HyBBX is **external** — attach after MAX25 stack is up.

1. Start CRDOP path:

   ```bash
   ./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
   ```

2. Merge `share/hybbx/crdop-host.ini.example` into HyBBX `hybbx.ini` on Secondary:

   ```ini
   [networks]
   crdop = yes

   [transport.crdop1]
   enabled = yes
   modem_host = 127.0.0.1
   modem_port = 8515
   mycall = CB-0
   listen = yes
   circuit_host = main.example.com
   circuit_port = 7323
   ```

MAX25 owns modem lifecycle; HyBBX owns sessions. See [docs/HYBBX.md](../../../docs/HYBBX.md).

---

## ARDOP-plugin

Optional **MAX25-Stack plugin** for ARDOP wire mode on `soft-crdop`.

| Item | Detail |
|------|--------|
| Registry | [plugins/external/ardop/README.md](../../../plugins/external/ardop/README.md) |
| Enable | `ardop_compat = yes` in `crdop.ini` or `[device.soft-crdop]` |
| Default | Native CRDOP / M25-KISS host (`ardop_compat = no`) |
| ARDOP host | Operator runs ARDOP-capable modem; set `CRDOP_BIN` if using `crdopc` launcher |

```ini
[compat]
ardop_compat = yes
```

```bash
CRDOP_BIN=/path/to/ardopc CRDOP_INI=~/.config/crdop/crdop.ini crdop
```

Plugin metadata: `plugins/external/ardop/plugin.yaml`.

---

## Operator profiles

| INI template | Profile | Use |
|--------------|---------|-----|
| `crdop.ini.example` | CB | Primary — K24/K25 class channels |
| `crdop-dual.ini.example` | dual | CB ↔ amateur switching |
| `crdop-amateur.ini.example` | amateur | Amateur secondary |

```bash
CRDOP_INI=share/crdop-dual.ini.example ./scripts/crdopc
```

---

## Testing in MAX25-Stack

```bash
./scripts/test.sh                    # cmake --build build --target max25_test
cmake --build build --target max25_daemon_smoke
./scripts/release-check.sh           # install + policy checks
```

CRDOP-specific offline tests: `test_crdop_backend.py`, `test_audio_dummy_backend.py`, `test_bell202_line_code.py`.

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `crdopc not found` | Run `./scripts/build.sh`; launcher uses `audio-dummyd` from install or source tree |
| No decode | `max25-signal-sniffer --loopback`; verify ALSA devices in INI |
| PulseAudio hijack | `no_pulse = yes`; use `hw:` / `plughw:` explicitly |
| Port conflict | Default :8515/:8516 — change `[host] port` + `[device.soft-crdop] port` |
| Terminal no device | `SET DEVICE soft-crdop`; check `[devices]` in `max25d.ini` |

---

## Related

| Doc | Topic |
|-----|--------|
| [INDEX.md](INDEX.md) | Full doc table |
| [DEVELOPER.md](DEVELOPER.md) | Source, modules, extending |
| [HARDWARE-INTERFACE.md](HARDWARE-INTERFACE.md) | Radio interface spec |
| [docs/PLUGINS-DEVICE-MODEL.md](../../../docs/PLUGINS-DEVICE-MODEL.md) | Unified device workflow |
| [docs/LINUX-HOST-SETUP.md](../../../docs/LINUX-HOST-SETUP.md) | Host prerequisites |
| [ROADMAP.md](../ROADMAP.md) | Phases and modulation priorities |
