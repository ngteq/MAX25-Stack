# AX.25 native codec — `ax25_codec.py`

**Purpose:** In-tree AX.25 UI framing for MAX25-Stack without bundling libax25.

**Code:** `stacks/daemon/ax25_codec.py` · **Consumers:** `kiss_bridge.py`, `hdlc_codec.py`, `acoustic_engine.py`, `device_backends.py`.

**Policy:** `MAX25_BUNDLE_AX25=OFF` — `third_party/ax25/*.tar.gz` reference only.

---

## Responsibilities

| Function | Description |
|----------|-------------|
| Address encode/decode | 7-byte dest/src, SSID 0–15, last-addr bit |
| UI frame build/parse | Control `0x03`, PID `0xF0` |
| CRC-16-CCITT | RFC 1171 table — residual `0xF0B8` |
| Callsign validation | `validate_callsign()` strict; `parse_callsign()` legacy clamp |

---

## KISS vs on-air

| Path | Bytes carried |
|------|---------------|
| **KISS DATA** (`0x00`) | UI body **without** FCS |
| **On-air HDLC** | Flags + stuffed bits + body + FCS |
| **CRDOP host TCP data** | Same as KISS DATA — see [HOST-PROTOCOL-SPEC.md](../stacks/crdop/docs/HOST-PROTOCOL-SPEC.md) |

`kiss_bridge.py` adds/strips FCS when bridging to serial TNCs that expect it.

---

## CRC verification

Test vector: ax25ipd `crc.c` — buffer `buf[i]=i` for `i=0..255` → `compute_crc` = **0x303C**.

---

## Limits

| Item | Limit |
|------|-------|
| UI info field | 256 bytes max (AX.25) |
| Digipeater path | Parse support in codec; full WIDE routing = application |
| Connected mode I/S frames | Partial — UI primary for v1 |
| FX.25 / IL2P | Not in this module |

---

## Relation to libax25

| Feature | libax25 | `ax25_codec.py` |
|---------|---------|-----------------|
| FCS | ✅ | ✅ matched |
| Address layout | ✅ | ✅ matched |
| Kernel AF_AX25 | ✅ | Not used — userspace path |
| ax25-tools CLI | Host package optional | `baycom-pr-ctl listen` if installed |

---

## Tests

```bash
python3 -m pytest stacks/daemon/test_bans.py stacks/daemon/test_crdop_backend.py -q
```

Dedicated `test_ax25_codec.py` — add when extending I-frame support.

---

## Related docs

- [PACKET-RADIO.md](PACKET-RADIO.md) — AX.25 / KISS context
- [include/max25/packet-radio.md](../include/max25/packet-radio.md) — protocol summary
- `stacks/daemon/ax25_codec.py` — implementation
