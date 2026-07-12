# Protocol reference

Layer-1 for BayCom-class modems. Catalog: [MODEMS.md](MODEMS.md). INI: [MANUAL.md](MANUAL.md).

## BayCom ser12

Host generates **Bell 202 AFSK** (1200 or 300 baud) by bit-banging UART modem control lines. Modem IC modulates/demodulates only; **HDLC and clock** are in kernel `baycom_ser_fdx` + `hdlcdrv`.

TFPCX §3.1: BayCom-compatible modems work without host protocol changes.

## DE-9 electrical map

| Pin | Signal | Role |
|-----|--------|------|
| 3 | TXD | Modem supply (charge pump) |
| 4 | DTR | TX data |
| 5 | GND | Ground |
| 7 | RTS | PTT (high = TX) |
| 8 | CTS | RX data |

## Linux vs DOS on TXD

| Environment | TXD |
|-------------|-----|
| DOS TFPCX | ~+12 V static |
| Linux `baycom_ser_fdx` | Continuous `0x00` on UART THR |

Both can power the modem. Exotic builds may need hardware trim if RX bias is wrong.

## Kernel `mode` strings

| Mode | Baud | DCD |
|------|------|-----|
| `ser12*` | 1200 | Software (squelch open) |
| `ser12+` | 1200 | Hardware, inverted |
| `ser12` | 1200 | Hardware |
| `ser3*` | 300 | Software |
| `par96` | 9600 | Software (weak) |
| `picpar` | 9600 | Hardware |

Suffix `*` recommended for ser12 — [baycom.rst](https://docs.kernel.org/networking/device_drivers/hamradio/baycom.html).

## TX timing

| Parameter | Tool | Unit |
|-----------|------|------|
| TX delay | `baycom_sethdlc <iface> <n>` | n × 10 ms |
| TXTAIL (DOS) | TFPCX `@TA` | 10 ms steps |

Defaults from catalog `txdelay` — [MODEM-SETUP.md](MODEM-SETUP.md).

## Data path (kernel-ser12)

```
KISS client → baycom_kissbridge → bcsfX (ARPHRD_AX25) → baycom_ser_fdx → UART → ser12 modem → radio
```

Before modprobe: `setserial /dev/ttySx uart none`.

## Out of scope (v0.5.0)

| Item | Reason |
|------|--------|
| BayCom USCC / OptoPcScc | SCC timer hardware |
| Raw KISS TNC | Use `kissattach` or `kiss-serial` backend |
| WA8DED hostmode | Different API |
| LPT ser12 (DigiCom-style) | DOS TFPCX only — `unsupported-lpt-ser12` |
| ser12 on USB UART | Bit-bang needs hardware UART |
| `baycom_epp` | Kernel WIP |

Adapter requirements: [HARDWARE.md](HARDWARE.md).
