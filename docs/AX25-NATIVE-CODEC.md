# AX.25 native codec · MAX25-Stack 1.5.0

In-tree userspace AX.25 encode/decode — no kernel AX.25 required for max25d.

## Component matrix

| Module | Role |
|--------|------|
| `ax25_codec.py` | Address encode/decode, FCS |
| `kiss_bridge.py` | KISS frame wrap/unwrap |
| `banlist.py` | Source address ban list |

## Build matrix

| Option | Default | Effect |
|--------|---------|--------|
| `MAX25_BUNDLE_AX25` | OFF | Vendored ax25-apps tarballs reference-only |
| In-tree codec | always | Used by max25d and terminal |

## FCS matrix

| Direction | Rule |
|-----------|------|
| To TNC (KISS DATA) | FCS stripped |
| From TNC (RX) | FCS validated in codec |
| UI frames | Built in terminal or HyBBX attach path |

## Related

| Goal | Doc |
|------|-----|
| Packet radio | [PACKET-RADIO.md](PACKET-RADIO.md) |
| Hardware acceptance | [HARDWARE-ACCEPTANCE.md](HARDWARE-ACCEPTANCE.md) |
