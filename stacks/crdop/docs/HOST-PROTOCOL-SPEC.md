# M25 SoftModem host protocol — implementation spec (frozen for v1.0.0)

**CRDOP** = **MAX25-SoftModem** · Native host wire for MAX25-SoftModem · **Not** ARDOP FEC/ARQ.

**Normative code:** `stacks/crdop/lib/m25_host_protocol.py` · **Consumer:** `max25d` `CrdopTcpBackend`, `audio-dummyd`, `crdopc` launcher.

---

## Transport

| Channel | Default port | Wire |
|---------|--------------|------|
| **Control** | **8515** | Line-oriented ASCII, **`\n`** terminated (native) |
| **Data** | **8516** (= ctrl + 1) | Binary AX.25 UI body **without** HDLC flags or FCS |

| Mode | Control terminator | Data semantics |
|------|-------------------|----------------|
| **Native (default)** | `\n` | KISS DATA equivalent — 16+ byte UI body |
| **ARDOP-plugin** (`ardop_compat=true`) | `\r` | ARDOP host wire mode — see [plugins/external/ardop/README.md](../../../plugins/external/ardop/README.md) |

### Bench alternate ports

When `soft-crdop` and `audio-dummyd` run on one host, bench daemon may use **8520/8521** via CLI. Production `crdopc` and INI default **8515/8516**.

---

## Control commands (native)

All commands are single lines. Reply is one line ending `\n`.

| Command | Args | Reply | Behaviour |
|---------|------|-------|-----------|
| `INITIALIZE` | — | `OK` | Reset session state |
| `PROTOCOLMODE` | `KISS` | `OK` | Select KISS-semantics data channel |
| `MYCALL` | `CALL-SSID` | `OK` | Store station ID (uppercase) |
| `LISTEN` | `TRUE`/`FALSE` | `OK` | RX enable (default true) |
| `PING` | — | `OK` | Liveness |
| `STATUS` | — | `STATUS ready mycall=…` | State snapshot |
| *(unknown)* | — | `ERR unknown command` | |

**Not supported on native path:** `PROTOCOLMODE FEC`, `FECMODE`, ARQ bandwidth commands — use **ARDOP-plugin** (`ardop_compat=true`) if needed.

---

## Data channel

### TX (host → modem)

1. TCP connect to data port.
2. Send **one** AX.25 UI frame body: `dest(7) + src(7) + ctrl(1) + pid(1) + info(0..256)`.
3. Modem responds `OK` or `ERR …` (ASCII line).

Modem builds on-air: HDLC flags, bit-stuffing, frequency-toggle line code, AFSK PHY — see `acoustic_engine.encode_ax25_ui()`.

### RX (modem → host)

Native bench: optional `STATUS` lines on control channel. Production: `max25d` parses demodulated UI and displays `[CRDOP AX25 UI src>dst] text`.

---

## max25d integration

```ini
[devices]
soft-crdop = crdop:default

[device.soft-crdop]
host = 127.0.0.1
port = 8515
listen = yes
; ardop_compat = no   # default — native KISS
```

`CrdopTcpBackend` on `open()`:

1. TCP connect `host:port` (ctrl), `host:port+1` (data).
2. Send `INITIALIZE`, `PROTOCOLMODE KISS`, `MYCALL …`, `LISTEN TRUE` (each `\n`).

---

## Layer separation

| Layer | On data TCP | On air |
|-------|-------------|--------|
| AX.25 UI body | ✅ | Inside HDLC |
| HDLC + CRC-16 | ❌ | ✅ |
| Bell 202 AFSK | ❌ | ✅ |

Same rule as KISS `0x00` DATA frames in `kiss_bridge.py`.

---

## Compliance tests

| Test | Command |
|------|---------|
| Unit | `pytest stacks/daemon/test_crdop_backend.py` |
| Bench host | `python3 stacks/crdop/tools/audio-dummyd.py --ctrl-port 8515 --data-port 8516` |
| Loopback DSP | `pytest stacks/crdop/test_bell202_line_code.py` |

---

## Version

Frozen for **MAX25-Stack v1.0.0** (dev track `CUR999`). Changes require bump in this file + `PROTOCOL.md` + `test_crdop_backend.py`.
