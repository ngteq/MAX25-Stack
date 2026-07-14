# Packet Radio & AX.25 · MAX25-Stack 1.5.0

Technical reference for on-air and host-side AX.25/KISS behaviour in MAX25.

## Layer matrix

| Layer | MAX25 owns |
|-------|------------|
| Operator UI | `max25-terminal` |
| Session / IPC | `max25d` M25/1 |
| Device prep | boot-wait, modprobe, KISS PTY |
| AX.25 codec | `ax25_codec.py` / `kiss_bridge.py` |
| KISS framing | FEND/FESC, port nibble |
| HyBBX attach | external — after stack up |

## Address matrix

| Rule | Value |
|------|-------|
| Call body | 1–6 chars A–Z/0–9 |
| SSID | `-0` … `-15` |
| Path order | DEST → DIGI* → SOURCE |

## KISS matrix

| Item | Rule |
|------|------|
| FCS on DATA to TNC | stripped — TNC adds on air |
| KISS return recovery | `0xC0 0xFF 0xC0` before prep |
| MYCALL | MAX25 prep — not HyBBX |

## CRDOP note matrix

| Item | Value |
|------|-------|
| Device id | `soft-crdop` |
| Speed | 1200 bd primary, up to 19200 bd |
| Duplex | half and full |
| TCP ports | 8515 control / 8516 data |

## Related

| Goal | Doc |
|------|-----|
| Device workflow | [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) |
| HyBBX | [HYBBX.md](HYBBX.md) |
