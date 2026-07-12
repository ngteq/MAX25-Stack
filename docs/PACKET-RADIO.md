# Packet Radio & AX.25 — technical reference (MAX25)

Technical facts for **MainAX25-Stack (MAX25)** developers and operators. Describes on-air and host-side behaviour that `max25d`, hardware stacks, and `max25-terminal` rely on.

HyBBX is only mentioned where MAX25 hands off after prep ([HYBBX.md](HYBBX.md)). The rules below are distilled from production AX.25/KISS practice (including the reference implementation in the upstream HyBBX tree).

---

## Layer model in MAX25

```
Operator
   → max25-terminal (text lines, CALLERID/CALLID, --ax25-ui)
   → max25d (M25/1, plugin lifecycle, KISS/serial/kernel)
   → Hardware stack (tncs | baycom-pr | crdop)
   → RF (AFSK 1200 / G3RUH 9600 / ARDOP — device dependent)
```

| Layer | MAX25 owns | Examples |
|-------|------------|----------|
| Operator UI | `max25-terminal` | F10 menu, live IDs, line pacing |
| Session / IPC | `max25d` | M25/1, CONNECT, SEND |
| Device prep | `max25d` + `stacks/*` | boot-wait, `modprobe`, KISS PTY, `crdopc` |
| AX.25 UI build/parse | `max25d` (target) | dest/source/digi, CRC, KISS DATA |
| KISS framing | `max25d` → TNC | FEND/FESC, port nibble |
| Kernel AX.25 | `stacks/baycom-pr` | `hdlcdrv`, `bcsf0`, `AF_PACKET` |
| HyBBX attach | external | After stack is up — INI in `share/hybbx/` |

**CRDOP / ARDOP** (`soft-crdop`) is **not AX.25** — TCP sound-card modem parallel to packet radio. See `stacks/crdop/`.

---

## AX.25 addresses

### Text form (CALLERID / CALLID / MYCALL)

| Rule | Value |
|------|--------|
| Call body | 1–**6** characters, `A–Z` / `0–9`, uppercased on use |
| SSID | Optional `-0` … `-15` (0–15 decimal) |
| Text examples | `CB0`, `DG1ABC`, `DK0WC-7` |

MAX25 terminal **CALLERID** = AX.25 **source**. **CALLID** = AX.25 **destination** (first address field in UI frames).

### On-air encoding (7 bytes per address)

Each address field is **7 octets**:

1. Six call characters, **left-aligned**, space-padded, each shifted **left one bit** (LSB = 0).
2. Byte 7: SSID in bits 1–4 (`(ssid & 0x0F) << 1 | 0x60`), bit 0 = **address extension** (0 = more addresses follow, 1 = last address before control).

**Path order** in a UI frame:

```
DEST → [DIGI1 → … → DIGIn] → SOURCE (last, extension bit set)
```

| Constant | Value |
|----------|--------|
| Max digipeaters | 8 |
| Encoded address size | 7 bytes |
| Max frame (incl. CRC) | 330 bytes typical cap |

### UI frame layout

After address fields:

| Field | Value |
|-------|--------|
| Control | `0x03` — Unnumbered Information (UI) |
| PID | `0xF0` — no layer 3 protocol |
| Info | Payload (operator text) |
| FCS | CRC-CCITT **0x1021**, init `0xFFFF`, little-endian on wire |

CRC is computed over addresses + control + PID + info (not including the CRC bytes).

**Parsing RX:** accept only UI (`ctrl == 0x03`) with valid FCS; extract payload bytes after PID.

---

## `--ax25-ui` in max25-terminal

When `SET AX25_UI on` / `--ax25-ui`:

| Step | Behaviour |
|------|-----------|
| Operator types a line | Plain text (max **256** bytes recommended payload) |
| `max25d` builds UI frame | `CALLERID` → source, `CALLID` → dest, no digi unless extended later |
| Toward KISS TNC | AX.25 body **without FCS** inside KISS DATA — TNC firmware adds CRC on air |
| Toward kernel BayCom | Full frame per `hdlcdrv` / stack rules |
| Display RX | Decode UI → show payload text (path optional in status line) |

Digipeater path (`via`) is reserved for a later M25/1 extension; v1 uses direct dest/source only.

---

## KISS (TNC host protocol)

KISS frames serial traffic between host and TNC (Phil Karn / Chepponis, 1987).

### Framing

| Byte | Meaning |
|------|---------|
| `0xC0` | FEND — frame delimiter |
| `0xDB` | FESC — escape next byte |
| `0xDC` | TFEND — escaped FEND |
| `0xDD` | TFESC — escaped FESC |

Frame: `FEND` + `(port<<4 | cmd)` + payload + `FEND`.

### Commands (low nibble)

| Cmd | Name | Use |
|-----|------|-----|
| `0x00` | DATA | Raw AX.25 frame bytes (see FCS note) |
| `0x01` | TXDELAY | Post-PTT delay (10 ms units) |
| `0x02` | PERSIST | CSMA persistence (0–255) |
| `0x03` | SLOTTIME | Slot time (10 ms units) |
| `0x04` | TXTAIL | TX tail (10 ms units) |
| `0x05` | FULLDUPLEX | 0 = half, 255 = full |
| `0x06` | SETHARDWARE | PTT / hardware bits |

### KISS DATA and FCS

**Critical:** many TNCs (TheFirmware, PK-TNC2, TNC2C) expect KISS DATA with the AX.25 frame **minus the 2-byte FCS**. The TNC computes and appends CRC before the transmitter keys.

Host algorithm:

1. Build full UI frame **with** FCS.
2. If CRC validates on the built buffer, strip last 2 bytes before `KISS CMD_DATA`.
3. If no valid FCS present, send buffer as-is.

### KISS entry / exit (TNC2 class)

| Method | Sequence | Profiles |
|--------|----------|----------|
| `kiss on` | Host command before KISS | TNC2C, PK-232, Kantronics |
| ESC + `@K` | `0x1B` `@` `K` | Older TheFirmware / Landolt TF2.7 |
| `auto` | Try `kiss on`, then ESC+`@K` | `tnc2`, `generic`, `mfj1278` |
| KISS exit | `0xC0 0xFF 0xC0` (Return) | When leaving KISS after ESC+`@K` entry |

MAX25 boot-wait (`tnc2c-boot-wait.sh`) leaves the TNC in host command mode; `max25d`/HyBBX then enters KISS.

### MYCALL before TX

TheFirmware / PK-TNC2 often **will not key PTT** on KISS DATA until host **`MYCALL <call>`** was accepted.

MAX25 mapping:

- Set TNC MYCALL from `max25d.ini` `[modem] callerid=` or live `SET CALLERID` before stack TX.
- HyBBX edge: `mycall=` / `[broadcast] ax25_mycall` in `share/hybbx/*.ini.example`.

---

## Serial profiles (TNC → host)

Defaults for MAX25 `hardware/tncs` paths. Override only when hardware docs require it.

| Profile | Host line | RTS/DTR | Host baud (typical) | KISS entry |
|---------|-----------|---------|---------------------|------------|
| **TNC2C** (Landolt) | **7E1** | **on** | 2400 (TERM jumper) / up to 19200 | `kiss on` |
| TNC-2 / PK-TNC2 (TF) | 8N1 | off | 2400–9600 | `auto` |
| PK-232 | 8N1 | off | 9600 | `kiss on` |
| MFJ-1278 | 7E1 | off | 4800 | `auto` |
| Kantronics KPC | 8N1 | off | 9600 | `kiss on` |
| BayCom async KISS | 8N1 | off | 1200–2400 | `kiss on` |

**TNC2C:** DTR/RTS during **power-on** boot-wait — without it the firmware stays in echo mode. See `stacks/tncs/`.

**Host baud** is UART speed to the TNC, not on-air speed. On-air is set on the modem board (jumpers / `radio_baud` metadata).

---

## On-air modulation

| Mode | Speed | Typical hardware |
|------|-------|------------------|
| **AFSK** (Bell 202 / TCM3105) | **1200** baud | CB/HAM packet default, TNC2C, BayCom SER12 |
| **G3RUH FSK** | **9600** baud | 9600 modem boards, some TNCs |
| 19200 | rare | specialised TNC firmware |

`radio_baud` in INI examples is QoS/metadata for edge links; the **radio** must physically match.

---

## CB CSMA (shared channel)

On busy CB packet (`radio_band=cb`):

| Parameter | CB note |
|-----------|---------|
| **persist** | `255` = always key when TNC accepts frame (recommended default on shared CB) |
| Lower persist (e.g. 63, 128) | TheFirmware may **randomly drop** KISS DATA when channel looks busy — beacons look intermittent though host logged success |

Set `persist`, `slot`, `txdelay`, `txtail` in HyBBX transport INI or stack config — `max25d` should apply same values when driving KISS directly.

---

## BayCom kernel path (Linux)

Native SER12/PAR96 — **not** async USB serial.

| Fact | Detail |
|------|--------|
| Driver | `baycom_ser_fdx`, `baycom_ser_hdx`, `baycom_par`, `baycom_epp` + `hdlcdrv` |
| SER12 interface | `bcsf0` typical (`ser12*` = software DCD recommended) |
| UART | Bit-banged via **8250/16450/16550** I/O base + IRQ — COM1 `0x3F8/IRQ4` classic |
| USB-serial | **Not** supported on native kernel path — use KISS firmware or `hardware/tncs` |
| Frames | HDLC + AX.25 UI on netdev (`AF_PACKET` / `ETH_P_AX25`) |
| MAX25 prep | `stacks/baycom-pr/scripts/baycom-pr-ctl` — module load, KISS PTY optional |

HyBBX `baycom` plugin consumes the prepared netdev or KISS PTY — see [HYBBX.md](HYBBX.md).

---

## Terminal traffic conventions

Aligned with packet-radio terminal practice (2400 baud host feel):

| Setting | Default | Purpose |
|---------|---------|---------|
| Host pacing baud | **2400** | ~1 byte per 10 bit times on output |
| Line width | **80** columns (max 132) | Wrap display |
| Input line max | **80** characters | One UI chunk sizing |
| AX.25 UI payload cap | **256** bytes | Outbound text limit |
| Palette | Light gray on black | `\033[37;40m` |

`max25-terminal` should pace and wrap like HyBBX `client_display` when connected over slow links.

For **broadcast** traffic on 1200 baud, keep UI payloads **short** (≤ **48** characters recommended on shared channels) to reduce channel occupancy.

---

## One process per RF port

| Rule | Reason |
|------|--------|
| Only **one** owner per `/dev/tty*` | boot-wait, KISS, or HyBBX — never minicom + driver + HyBBX concurrently |
| One `KissBridge` per device id | `max25d` `[devices]` — each id maps to one serial port |
| BayCom kernel loaded | **No** minicom on raw UART |
| MAX25 `max25d` owns prep | HyBBX opens serial **after** boot-wait / `baycom-pr-ctl start` |

### Multi-device (max25d)

Configure multiple heterogeneous devices in `max25d.ini`:

```ini
[devices]
default = tnc2c
tnc2c = /dev/ttyS4
pktnc2 = /dev/ttyS5
baycom-ser12 = baycom:a
soft-crdop = crdop:default
```

| Device id | Backend | Link |
|-----------|---------|------|
| `tnc2c`, `pktnc2` | `kiss-serial` | Serial KISS after boot-wait |
| `baycom-ser12`, `baycom-par96` | `baycom-kiss` | KISS PTY `/var/run/baycom-pr/kiss` |
| `baycom-kiss` | `kiss-raw-serial` | USB/async KISS serial |
| `soft-crdop` | `crdop-tcp` | ARDOP TCP `:8515` / `:8516` |

Full station example: `share/max25/max25d.full-station.ini.example`.

M25/1: `devices=` in `STATUS`, `SET DEVICE <id>` for TX routing, `RX device=<id> …` on receive. See [`include/max25/protocol.md`](../include/max25/protocol.md).

**Validation:** TNC2C serial KISS is CI-tested. BayCom and CRDOP backends are wired but may log startup warnings until hardware-validated.

---

## MAX25 ↔ field mapping

| Operator / M25/1 | AX.25 / TNC |
|----------------|-------------|
| `CALLERID` | Source address, `MYCALL` on TNC |
| `CALLID` | Destination address (UI frames) |
| `SEND <text>` | UI payload bytes |
| `SET AX25_UI on` | Build UI + KISS DATA path |
| `stack=tncs` | Serial KISS after boot-wait |
| `stack=modems` | BayCom kernel or KISS PTY |
| `stack=soft-modems` | CRDOP TCP — not AX.25 |

---

## Implementation status in MAX25

| Item | Status |
|------|--------|
| AX.25 UI build/parse rules (this doc) | **Specified** |
| CALLSIGN validation (6+SSID) | **max25d** + `max25-terminal` |
| KISS encode + FCS strip | **max25d** `kiss_bridge.py` |
| Serial KISS bridge (TNC2C/PK-TNC2) | **max25d** `kiss_bridge.py` |
| Multi-device backends (5+ concurrent) | **max25d** `device_backends.py` |
| BayCom KISS PTY attach | **max25d** `BayComKissBackend` → `/var/run/baycom-pr/kiss` |
| CRDOP ARDOP TCP attach | **max25d** `CrdopTcpBackend` → `:8515/:8516` |
| MYCALL + kiss entry per profile | **max25d** / stack scripts |
| Kernel BayCom TX/RX | **stacks/baycom-pr** (mature) |
| TNC2C boot-wait | **stacks/tncs** (mature) |

Reference algorithms: HyBBX `plugins/packet_radio/ax25.c`, `kiss.c`, `tnc.c` (upstream, GPL) — MAX25 will implement equivalent logic inside `max25d` without vendoring HyBBX.

---

## Quick diagnostics

| Symptom | Likely cause |
|---------|----------------|
| TNC echoes chars, no KISS | Boot-wait / DTR / wrong serial line (7E1 vs 8N1) |
| KISS OK, no RF | `MYCALL` missing; PTT wiring; persist too low on CB |
| Garbled RX | Host baud mismatch; wrong `radio_baud` on air |
| BayCom IRQ errors | Wrong `iobase`/`irq` — can freeze host; run preflight |
| Frame too long | Payload > 256 B or path too many digis |

---

## See also

- [MAX25-CLIENT.md](MAX25-CLIENT.md) — M25/1 binding
- [MAX25-TERMINAL.md](MAX25-TERMINAL.md) — operator UI
- [LINUX-EDGE-SETUP.md](LINUX-EDGE-SETUP.md) — example edge install & USB TNC setup
- [HYBBX.md](HYBBX.md) — attach after prep (minimal)
- [include/max25/packet-radio.md](../include/max25/packet-radio.md) — constants cheat sheet
- `stacks/tncs/`, `stacks/baycom-pr/docs/`, `share/hybbx/*.ini.example`
