# Packet radio constants (MAX25)

Compact reference. Full prose: [docs/PACKET-RADIO.md](../../docs/PACKET-RADIO.md).

## AX.25

| Symbol | Value |
|--------|-------|
| Call length | 1–6 chars, `A–Z` `0–9` |
| SSID | 0–15 (`-0` … `-15`) |
| Address field | 7 bytes encoded |
| Max digipeaters | 8 |
| UI control | `0x03` |
| UI PID | `0xF0` (no layer 3) |
| CRC | CCITT 0x1021, init 0xFFFF, LE on wire |
| Max frame | ~330 bytes |
| Max UI payload (host) | 256 bytes |
| Broadcast payload hint (1200 baud) | ≤ 48 chars |

## KISS

| Symbol | Value |
|--------|-------|
| FEND | `0xC0` |
| FESC | `0xDB` |
| TFEND | `0xDC` |
| TFESC | `0xDD` |
| CMD DATA | `0x00` |
| KISS DATA AX.25 | **without FCS** (TNC adds CRC) |

## Serial / radio defaults

| Item | Default |
|------|---------|
| Host pacing | 2400 baud equivalent |
| Terminal width | 80 columns |
| Input line | 80 chars |
| TNC2C line | 7E1, RTS/DTR on |
| AFSK on-air | 1200 baud |
| G3RUH FSK | 9600 baud |
| BayCom SER12 netdev | `bcsf0` |
| USB TNC device | `/dev/ttyUSB0` |

## MAX25 IDs

| Terminal | AX.25 |
|----------|-------|
| CALLERID | source / MYCALL |
| CALLID | destination |
