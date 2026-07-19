# HyBBX integration · MAX25-Stack 1.8.5-fallback_untested-upcoming#1

MAX25 is the standalone RF/link layer — HyBBX consumes via transport plugins after MAX25 prep.

## Plugin mapping matrix

| MAX25 hardware | HyBBX plugin | INI `[networks]` |
|----------------|--------------|------------------|
| `hardware/tncs` | `packet_radio` | `ax25=yes` |
| `hardware/modems` | `baycom` | `baycom=yes` |
| `hardware/soft-modems` | `crdop` | `crdop=yes` |

## Order rule matrix

| Rule | Detail |
|------|--------|
| Start order | MAX25 before HyBBX |
| Serial ownership | One process per port |
| v2.4.0 HyBBX | `[max25] check=yes`, `kiss_entry=none` |
| BayCom in packet_radio | rejected — use MAX25 + baycom plugin |

## TNC workflow matrix

| Step | Action |
|------|--------|
| 1 | `max25-ctl start --hardware tncs --device tnc2c` |
| 2 | Merge `share/hybbx/tnc2c-host.ini.example` |
| 3 | HyBBX `[max25] check=yes`, `kiss_entry=none` |
| 4 | Start HyBBX Secondary → HBX to Main |

## INI fragment matrix

| Device | Example INI |
|--------|-------------|
| TNC2C | `share/hybbx/tnc2c-host.ini.example` |
| BayCom/based | via MAX25 **bcpr** (kernel SER12 host INI removed) |
| CRDOP | `share/hybbx/crdop-host.ini.example` |

## Related

| Goal | Doc |
|------|-----|
| Packet radio facts | [PACKET-RADIO.md](PACKET-RADIO.md) |
| BayCom | [BAYCOM.md](BAYCOM.md) |
