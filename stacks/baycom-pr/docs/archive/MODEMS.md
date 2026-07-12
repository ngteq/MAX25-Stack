# Modem catalog

Hardware reference for [modems.ini](../config/modems.ini). Setup: [MODEM-SETUP.md](MODEM-SETUP.md). Protocol: [PROTOCOL.md](PROTOCOL.md).

## Rules

| Path | Requirement |
|------|-------------|
| **kernel-ser12** | Bell 202 on **hardware UART** via `baycom_ser_fdx` |
| **kernel-par96** | G3RUH 9600 on **parallel port** via `baycom_par` |
| **kiss-serial** | KISS framing on USB/async via `kiss_serial` |
| **Not this stack** | SCC cards, LPT ser12 bit-bang, ser12-on-USB-UART-only |

## Catalog fields

| Key | Meaning |
|-----|---------|
| `stack` | `supported` \| `planned` \| `unsupported` |
| `driver` | Linux module or `kiss_serial` |
| `verification` | `offline-verified`, `supported-by-design`, `planned`, `n/a` |
| `txdelay` | Default TX delay (×10 ms); override in site INI |

Site instances: `catalog = <id>` in [baycom-pr.ini](../config/baycom-pr.ini).

## Compatibility matrix

| Catalog ID | Product | Driver | Stack | Speed |
|------------|---------|--------|-------|-------|
| `kiss-serial-usb` | KISS USB modem | `kiss_serial` | supported | 9600 |
| `kiss-serial-rs232` | KISS async serial | `kiss_serial` | supported | 9600 |
| `baycom-ser12` | BayCom DIY (TCM3105) | `baycom_ser_fdx` | supported | 1200 |
| `albrecht-pc-com` | Albrecht PC-COM / AE8000 | `baycom_ser_fdx` | **offline-verified** | 1200 |
| `albrecht-pc-com-4500` | PC-COM 4500 CB | `baycom_ser_fdx` | supported | 1200 |
| `baypac-bp1` / `bp2` / `bp2m` | Tigertronics BayPac | `baycom_ser_fdx` | supported | 1200/300 |
| `fx614-ser12` / `mx614-ser12` | FX614 / MX614 builds | `baycom_ser_fdx` | supported | 1200 |
| `pmp-ezpacket-ser12` | Poor Man's Packet | `baycom_ser_fdx` | supported | 1200 |
| `am7911-ser12` | AM7911 designs | `baycom_ser_fdx` | supported | 1200 |
| `ser12-300-hf` | 300 bd HF | `baycom_ser_fdx` | supported | 300 |
| `cb-ser12-generic` / `tnc2-ser12-clone` | Generic kits | `baycom_ser_fdx` | supported | 1200 |
| `ser12-hdx-fallback` | Bad UART delta | `baycom_ser_hdx` | supported | 1200 |
| `baycom-par96` / `picpar` / `baypac-bp96a` | Parallel 9600 | `baycom_par` | **supported** | 9600 |
| `baycom-epp` | EPP modem | `baycom_epp` | planned | — |
| `unsupported-*` | See below | — | **no** | — |

## DE-9 pinout (PC side, BayCom ser12)

| Pin | Signal | Function |
|-----|--------|----------|
| 3 | TXD | Modem power (charge pump) |
| 4 | DTR | TX data |
| 5 | GND | Ground |
| 7 | RTS | PTT (high = TX) |
| 8 | CTS | RX data |

## Per-type notes

### Albrecht PC-COM / AE8000

- BayCom-compatible (TFPCX §3.1). **txdelay = 35**. Offline verified on AX25SRV (v0.5.0).

### Tigertronics BayPac

- BP-1/2: DE-25 serial. BP-2M: 300+1200. BP-96A: parallel — see [PARPORT.md](PARPORT.md).

### TCM3105 successors (FX614 / MX614)

- Same host protocol as ser12; different modem IC on board.

### AM7911

- May need higher txdelay (25–30).

### par96 / picpar

- LPT shift-register G3RUH 9600; `baycom_par` → `bcp0..bcp3`. Full guide: [PARPORT.md](PARPORT.md).
- **par96**: software DCD. **picpar**: hardware DCD recommended.

### Excluded (`unsupported-*`)

| ID | Reason |
|----|--------|
| `unsupported-baycom-uscc` | SCC 9k6 — not UART ser12 |
| `unsupported-optopcscc` | OptoPcScc |
| `unsupported-ser12-usb-adapter` | ser12 on USB UART only |
| `unsupported-lpt-ser12` | LPT bit-bang ser12 — DOS TFPCX |
| `unsupported-kiss-tnc` | Deprecated — use `kiss-serial-*` |

## Instance example

```ini
[modem.radio]
catalog = albrecht-pc-com
serial = /dev/ttyS0
iface = bcsf0
kiss_link = /var/run/baycom-pr/kiss-a
txdelay = 35
iobase = 0x3f8
irq = 4
```

## References

| Source | Topic |
|--------|--------|
| [kernel baycom.rst](https://docs.kernel.org/networking/device_drivers/hamradio/baycom.html) | Driver modes, DCD |
| TFPCX 2.10 §3.1 (external reference, DG0FT) | Compatible modems, pinout |
| [Tigertronics BayPac](https://tigertronics.com/baysuprt.htm) | BP series |
| [SM0VPO BayCom DIY](https://www.sm0vpo.com/use/baycom.htm) | Original ser12 |

TFPCX is third-party reference material — not shipped in this repository. See [NOTICE](../NOTICE).
