# MAX25 device compatibility — full list

Complete inventory of hardware that **works with MAX25-Stack today**, is **planned or scaffolded**, or is **documented as unsupported**. For operators and integrators choosing modems, TNCs, and soft-modem paths.

**Related:** [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) (workflow) · [DEVICES-LIST-FULL.md](DEVICES-LIST-FULL.md) (all hardware) · [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) (release boundary) · [HARDWARE-ACCEPTANCE.md](HARDWARE-ACCEPTANCE.md) (smoke tests) · [BAYCOM.md](BAYCOM.md) · [PACKET-RADIO.md](PACKET-RADIO.md) · [CRDOP.md](CRDOP.md)

**Machine-readable registries:** `plugins/manifest.yaml` · `share/clients/index.yaml` · `stacks/baycom-pr/config/modems.ini`

---

## How to read this document

MAX25 uses two layers:

| Layer | What it is | Example |
|-------|------------|---------|
| **Device plugin** | `max25d` device id in `[devices]` | `tnc2c`, `baycom-ser12`, `soft-crdop` |
| **Hardware catalog** | BayCom modem product id in `baycom-pr.ini` | `catalog = albrecht-pc-com` under device `baycom-ser12` |

### Status legend

| Status | Meaning |
|--------|---------|
| **active** | Device plugin shipped; operator workflow and acceptance apply |
| **planned** | Plugin exists; deferred from current release acceptance |
| **scaffold** | Plugin + INI/templates; hardware validation pending |
| **bench** | Dev/test only — no on-air RF path |
| **optional** | Mode or plugin — not a standalone RF device |
| **practical** | Used on reference stations or CI with real/stack path |
| **by design** | Stack claims compatibility; site validation still required |
| **theoretical** | Serial profile documented; no dedicated device plugin |
| **unsupported** | Explicitly out of scope |

### Verification legend (BayCom catalog)

| Tag | Meaning |
|-----|---------|
| **offline-verified** | Documented proof on reference hardware |
| **supported-by-design** | Catalog + kernel/driver match; not bench-signed per SKU |

---

## Summary — MAX25 device plugins

| Device ID | Label | Hardware family | Plugin status | Practical today | Interface | On-air (typical) | HyBBX |
|-----------|-------|---------------|---------------|-----------------|-----------|------------------|-------|
| `tnc2c` | Landolt TNC2C | `tncs` | **active** | **yes** | Serial → KISS | 1200 / 2400 AFSK | `packet_radio` (`tnc2c`) |
| `pktnc2` | PK-TNC2 / TNC-2 | `tncs` | planned | partial | Serial → KISS | 1200 AFSK | `packet_radio` (`tnc2`) |
| `baycom-ser12` | BayCom SER12 (kernel) | `modems` | **active** | **yes** | Kernel UART → KISS PTY | 1200 Bell 202 | `baycom` (kernel `ser12*`) |
| `baycom-par96` | BayCom PAR96 (LPT) | `modems` | scaffold | no | Kernel LPT → KISS PTY | 9600 G3RUH | `baycom` (kernel `par96`) |
| `baycom-kiss` | KISS serial (USB/async) | `modems` | scaffold | no | Serial KISS | 1200 (profile) | `baycom` (kiss backend) |
| `soft-crdop` | MAX25-SoftModem (CRDOP) | `soft-modems` | **active** | **yes** (bench+) | ALSA → TCP :8515/:8516 | 1200–19200 | `crdop` |
| `audio-dummy` | Acoustic bench | `acoustic-bench` | **active** | bench only | ALSA loopback / sniff | — | — |
| `max25-terminal` | Operator client | `terminal` | **active** | **yes** | M25/1 TCP / Unix | — | — |

**v1.0.0 RF-active trio:** `tnc2c`, `baycom-ser12`, `soft-crdop`.

**Service-mode aliases (not separate manifest entries):** `baycom-a`, `baycom-b` — dual kernel SER12; see [BAYCOM.md](BAYCOM.md).

**Optional wire mode:** ARDOP-plugin on `soft-crdop` (`ardop_compat=true`) — [plugins/external/ardop/README.md](../plugins/external/ardop/README.md).

---

## 1. TNC devices (`hardware/tncs`)

Stack path: `stacks/tncs/` · Backend: `KissSerialBackend` · HyBBX: `packet_radio`

### 1.1 `tnc2c` — Landolt TNC2C (active)

| Topic | Value |
|-------|-------|
| **Practical** | Yes — reference TNC for MAX25; boot-wait, serial watch, native TF recovery |
| **Host serial** | Default 19200 8N1, DTR+RTS on (`kiss_entry=kiss_on`) |
| **On-air** | 1200 / 2400 AFSK (TCM3105; jumper-dependent) |
| **max25d** | `tnc2c = /dev/ttyS4` (example) |
| **Config** | `share/max25/serial/tnc2c-serial.env.example`, `[serial.tnc2c]` |
| **Client profile** | `share/clients/tnc2c.yaml` |

Firmware class: TheFirmware TF 2.7 (NORD><LINK). Recovery: [stacks/tncs/docs/TNC-RECOVERY.md](../stacks/tncs/docs/TNC-RECOVERY.md).

### 1.2 `pktnc2` — PK-TNC2 / TAPR TNC-2 (planned)

| Topic | Value |
|-------|-------|
| **Practical** | Partial — boot-wait script exists; v1.1+ acceptance |
| **Host serial** | Default 9600 8N1, DTR+RTS off (`kiss_entry=auto`) |
| **On-air** | 1200 AFSK (typical CB) |
| **max25d** | `pktnc2 = /dev/ttyS5` (example) |
| **HyBBX aliases** | `pktnc2`, `pk-tnc2`, `tapr`, `thefirmware` → profile `tnc2` |
| **Client profile** | `share/clients/pktnc2.yaml` |

Same backend as `tnc2c`; differs in serial profile and firmware detection.

### 1.3 Theoretical TNC serial profiles (no device plugin)

Documented in [PACKET-RADIO.md](PACKET-RADIO.md) for manual `[serial.*]` tuning. Use `pktnc2` or a custom device id with matching serial section.

| Radio/TNC class | Host line | RTS/DTR | Host baud | KISS entry | MAX25 expectation |
|-----------------|-----------|---------|-----------|------------|-------------------|
| PK-232 | 8N1 | off | 9600 | `kiss on` | Theoretical — same stack path as other serial KISS TNCs |
| MFJ-1278 | 7E1 | off | 4800 | `auto` | Theoretical |
| Kantronics KPC | 8N1 | off | 9600 | `kiss on` | Theoretical |
| Generic async KISS TNC | 8N1 | varies | 9600–19200 | `kiss on` / `auto` | Prefer `baycom-kiss` when no dedicated plugin |

**Note:** `plugins/manifest.yaml` mentions PK-232 in the hardware group description; there is **no** `pk232` device plugin yet.

### 1.4 On-air speed reference (TNC family)

| Modulation | Speed | Typical hardware |
|------------|-------|------------------|
| Bell 202 AFSK | **1200** | TNC2C, PK-TNC2, most CB TNCs |
| AFSK (higher) | **2400** | TNC2C (radio jumper example) |
| G3RUH FSK | **9600** | 9600 TNC firmware, PAR96 class |
| Specialised | **19200** | Rare; CRDOP phase cap |

---

## 2. BayCom kernel modems — SER12 (`device: baycom-ser12`)

Stack path: `stacks/baycom-pr/` · Driver: `baycom_ser_fdx` / `baycom_ser_hdx` · Backend: `BayComKissBackend` · KISS PTY: `/var/run/baycom-pr/kiss`

**Requires:** Real **8250/16550 UART** (`/dev/ttyS*`) — **not** USB-serial adapter for kernel bit-bang path.

**max25d:** `baycom-ser12 = baycom:a` · Site INI: `/etc/baycom/baycom-pr.ini` with `catalog = <id>`

All catalog entries below map to device plugin **`baycom-ser12`**.

| Catalog ID | Product | On-air | Stack | Verification | Notes |
|------------|---------|--------|-------|--------------|-------|
| `baycom-ser12` | BayCom DIY (TCM3105) | 1200 | supported | by design | Reference ser12 design |
| `albrecht-pc-com` | Albrecht PC-COM / AE8000 | 1200 | supported | **offline-verified** | Reference station proof |
| `albrecht-pc-com-4500` | Albrecht PC-COM 4500 CB | 1200 | supported | by design | Same L1 as PC-COM |
| `baypac-bp1` | Tigertronics BayPac BP-1 | 1200 | supported | by design | Legacy BayPac |
| `baypac-bp2` | Tigertronics BayPac BP-2 | 1200 | supported | by design | DE-25, port-powered |
| `baypac-bp2m` | BayPac BP-2M | 1200 / 300 HF | supported | by design | HF: `mode=ser3*` `baud=300` in site INI |
| `fx614-ser12` | FX614 Bell 202 (SP3EJJ) | 1200 | supported | by design | TCM3105 replacement chip |
| `mx614-ser12` | MX614 Bell 202 (QST/homebrew) | 1200 | supported | by design | Same host bit-bang class |
| `pmp-ezpacket-ser12` | Poor Man's Packet / EZPacket DIY | 1200 | supported | by design | TCM3105 DIY |
| `am7911-ser12` | AM7911-based ser12 | 1200 | supported | by design | May need higher TXTAIL |
| `ser12-300-hf` | ser12 @ 300 bd HF | 300 | supported | by design | `mode=ser3*` |
| `tnc2-ser12-clone` | Generic DIY ser12 clone | 1200 | supported | by design | Verify DE-9 pinout |
| `cb-ser12-generic` | Generic CB 1200 bd BayCom class | 1200 | supported | by design | txdelay 30–35 typical on CB |
| `ser12-hdx-fallback` | ser12 HDX fallback | 1200 | supported | by design | `baycom_ser_hdx`, iface `bcsh*` |

**Practical today:** `albrecht-pc-com` offline-verified; all others **by design** until site smoke test ([HARDWARE-ACCEPTANCE.md](HARDWARE-ACCEPTANCE.md) § baycom-ser12).

**Dual radio (service mode):** two UARTs → `baycom-a` / `baycom-b`, KISS `kiss-a` / `kiss-b`, netdevs `bcsf0` / `bcsf1` — `share/max25/max25d.dual-baycom.ini.example`.

---

## 3. BayCom kernel modems — PAR96 (`device: baycom-par96`)

Driver: `baycom_par` · Backend: `BayComKissBackend` · On-air: **9600 G3RUH FSK**

| Catalog ID | Product | Verification | Plugin status |
|------------|---------|--------------|---------------|
| `baycom-par96` | BayCom par96 (parallel G3RUH) | by design | scaffold |
| `baycom-picpar` | picpar / par97 (DF9IC) | by design | scaffold |
| `baypac-bp96a` | Tigertronics BayPac BP-96A | by design | scaffold |

**Requires:** Parallel port (`CONFIG_BAYCOM_PAR`, `CONFIG_PARPORT`), typical `iobase=0x378`. **Practical:** template INI only — hardware validation pending.

---

## 4. BayCom KISS serial (`device: baycom-kiss`)

Userspace KISS on async serial — **no** kernel BayCom bit-bang. Backend: `KissRawSerialBackend`.

| Catalog ID | Product | Host baud | Plugin status |
|------------|---------|-----------|---------------|
| `kiss-serial-usb` | KISS on USB (`ttyUSB` / `ttyACM`) | 9600 | scaffold |
| `kiss-serial-rs232` | KISS on RS-232 | 9600 | scaffold |

**Typical hardware (theoretical/practical via scaffold):** OpenTracker, Mobilinkd-class, KISS firmware TNCs, digipeaters with USB serial.

**max25d:** `baycom-kiss = /dev/ttyUSB0` · `[serial.baycom-kiss]` 9600 8N1, DTR+RTS off.

**Client profiles:** `share/clients/kiss-serial-usb.yaml`, `kiss-serial-rs232.yaml`.

---

## 5. Soft modems — MAX25-SoftModem / CRDOP (`device: soft-crdop`)

Stack path: `stacks/crdop/` · Backend: `CrdopTcpBackend` · HyBBX: `crdop`

| Topic | Value |
|-------|-------|
| **Product** | In-house sound-card AX.25 modem — [CRDOP.md](CRDOP.md) |
| **Practical** | Bench T0–T6 offline; on-air RF optional per site |
| **Interface** | ALSA IN/OUT → `crdopc` / `audio-dummyd` → TCP **8515** (control) / **8516** (data) |
| **On-air** | **1200** Bell 202 AFSK (P0); roadmap **9600–19200** G3RUH (P1); **19200 max** current phase |
| **Duplex** | Half (default), full when interface allows |
| **max25d** | `soft-crdop = crdop:default` · `[device.soft-crdop]` |
| **Build** | Default ON (`MAX25_BUILD_CRDOP=ON`) |

### CRDOP profiles (INI templates)

| Profile | Template | Status |
|---------|----------|--------|
| CB / default | `stacks/crdop/share/crdop.ini.example` | **active** |
| Dual | `crdop-dual.ini.example` | template |
| Amateur | `crdop-amateur.ini.example` | template |

### ARDOP-plugin (optional — not a separate device)

| Topic | Value |
|-------|-------|
| **Attaches via** | `soft-crdop` with `ardop_compat=true` |
| **Wire** | ARDOP host format on same TCP ports |
| **Registry** | `plugins/external/ardop/` |

---

## 6. Acoustic bench (`device: audio-dummy`)

| Topic | Value |
|-------|-------|
| **Purpose** | DSP evaluation, loopback, ALSA sniff — **no RF** |
| **max25d** | `audio-dummy = audio:loopback` |
| **Tools** | `stacks/crdop/tools/audio-dummyd`, Bell 202 bench tests |

---

## 7. Operator client (`device: max25-terminal`)

Not RF hardware. Text client + F10 menu → M25/1 on TCP **7325** or Unix `/run/max25/modem.sock`.

Browser terminal (WebSocket, **in development**): [WEBSOCKET.md](WEBSOCKET.md) — not production in v1.0.0; does not replace `max25-terminal`.

---

## 8. Planned BayCom hardware (catalog only)

| Catalog ID | Product | Stack status | Notes |
|------------|---------|--------------|-------|
| `baycom-epp` | BayCom EPP high-speed | **planned** | Kernel `baycom_epp` WIP |

---

## 9. Explicitly unsupported

| Catalog ID | Product | Reason |
|------------|---------|--------|
| `unsupported-baycom-uscc` | BayCom 9k6 USCC | SCC card — not UART ser12 |
| `unsupported-optopcscc` | PA0HZP OptoPcScc | SCC-based — different driver stack |
| `unsupported-ser12-usb-adapter` | ser12 via USB-UART only | Kernel ser12 needs real UART; use `kiss-serial-usb` |
| `unsupported-lpt-ser12` | LPT bit-bang ser12 (DigiCom-style) | DOS TFPCX path only |
| `unsupported-kiss-tnc` | Legacy catalog entry | **Superseded** by `kiss-serial-*` |

---

## 10. HyBBX attach matrix

MAX25 prepares hardware **first**; HyBBX attaches as Secondary consumer. One process per serial port.

| MAX25 hardware | HyBBX plugin | `[networks]` | INI example |
|----------------|--------------|--------------|-------------|
| `tncs` | `packet_radio` | `ax25 = yes` | `share/hybbx/tnc2c-host.ini.example`, `pktnc2-host.ini.example` |
| `modems` (ser12) | `baycom` | `baycom = yes` | `share/hybbx/baycom-ser12-host.ini.example` |
| `soft-modems` | `crdop` | `crdop = yes` | `share/hybbx/crdop-host.ini.example` |
| Dual BayCom service | `baycom` ×2 | transport sections | `share/hybbx/service-dual.ini.example` |

Detail: [HYBBX.md](HYBBX.md).

---

## 11. max25d backend reference

| Device ID(s) | Backend class | Link |
|--------------|---------------|------|
| `tnc2c`, `pktnc2` | `KissSerialBackend` | Serial KISS |
| `baycom-ser12`, `baycom-par96`, `baycom-a`, `baycom-b` | `BayComKissBackend` | Kernel KISS PTY |
| `baycom-kiss` | `KissRawSerialBackend` | Async serial KISS |
| `soft-crdop` | `CrdopTcpBackend` | TCP :8515/:8516 |
| `audio-dummy` | `AudioDummyBackend` | Bench audio path |

Daemon detail: [stacks/daemon/README.md](../stacks/daemon/README.md).

---

## 12. Heterogeneous station example

All four RF families on one `max25d`: `share/max25/max25d.full-station.ini.example`

```ini
[devices]
default = tnc2c
tnc2c = /dev/ttyS4
pktnc2 = /dev/ttyS5
baycom-ser12 = baycom:a
soft-crdop = crdop:default
```

Use `enabled = …` to limit which ids start when not all hardware is present.

---

## 13. Source file index

| Purpose | Path |
|---------|------|
| Plugin registry | `plugins/manifest.yaml` |
| Client / catalog index | `share/clients/index.yaml` |
| BayCom hardware DB | `stacks/baycom-pr/config/modems.ini` |
| Daemon config template | `share/max25/max25d.ini.example` |
| Full station | `share/max25/max25d.full-station.ini.example` |
| Dual BayCom | `share/max25/max25d.dual-baycom.ini.example` |
| HyBBX snippets | `share/hybbx/*.ini.example` |
| Per-device plugins | `plugins/devices/*/plugin.yaml` |
| v1 scope | `docs/V1.0.0-SCOPE.md` |
| Acceptance | `docs/HARDWARE-ACCEPTANCE.md` |

---

*This list reflects MAX25-Stack **v1.0.0** registry and BayCom catalog **v0.5.0**. Update when device plugins or `modems.ini` entries change.*
