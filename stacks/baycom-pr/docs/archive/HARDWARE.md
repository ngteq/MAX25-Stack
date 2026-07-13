# Hardware: serial, USB, and port power

Physical interfaces for [MODEMS.md](MODEMS.md) catalog entries. Protocol: [PROTOCOL.md](PROTOCOL.md).

## Two connection paths

| Path | Host | Stack | Modems |
|------|------|-------|--------|
| **kernel-ser12** | `/dev/ttyS*` | `baycom_ser_fdx` | BayCom ser12, BayPac serial, FX614/MX614, … |
| **kernel-par96** | LPT (`iobase`) | `baycom_par` | par96, picpar, BayPac BP-96A |
| **kiss-serial** | `/dev/ttyUSB*`, `/dev/ttyACM*` | `baycom_kiss_serial` | KISS TNCs, USB packet radios |

## Port power

Many modems draw **supply current from the host serial port**:

| Pin | Role | Note |
|-----|------|------|
| TXD (3) | Charge pump / bias | Linux pumps `0x00` on THR continuously |
| DTR (4) | TX data | Must switch under load |
| RTS (7) | PTT | Must assert for calibrate / TX |
| CTS (8) | RX data | Timing-critical on kernel-ser12 |

Consumer USB adapters may lack **RS-232 levels** or **line current** for port-powered ser12 modems.

## Requirements by backend

### kernel-ser12

| Requirement | Detail |
|-------------|--------|
| UART | 8250/16450/16550A on motherboard or PCI |
| Before modprobe | `setserial … uart none`; valid `iobase` + `irq` |
| Lines | TXD, DTR, RTS, CTS, GND per [PROTOCOL.md](PROTOCOL.md) |
| Timing | Hardware bit-bang — **not** on USB UART behind `ttyUSB` |
| DCD | Software DCD (`ser12*`) recommended |

**ser12 on USB UART only:** not supported — use hardware UART or `kiss-serial-usb`.

### kernel-par96

| Requirement | Detail |
|-------------|--------|
| Port | Hardware parallel port (LPT1/LPT2) |
| Kernel | `CONFIG_PARPORT`, `CONFIG_BAYCOM_PAR`, `parport_pc` |
| Config | `iobase` (e.g. `0x378`); **no `irq=`** |
| Interface | `bcp0..bcp3` from `baycom_par` |
| DCD | par96: software; picpar: hardware preferred |

See [PARPORT.md](PARPORT.md) for wiring and workflow.

### kiss-serial

| Requirement | Detail |
|-------------|--------|
| Device | Linux `tty` (USB or serial) |
| Protocol | KISS framing, typically **8N1** |
| Speed | Catalog `kiss_baud` (default 9600) |
| Duplex | Full-duplex; no blocking half-duplex adapters |
| Power | Self-powered TNC: most adapters OK; port-powered: need real RS-232 levels |

## USB adapter checklist

1. Identify path — KISS vs kernel-ser12 (different requirements).
2. Match baud — 9600 for KISS byte stream.
3. Stable device node — prefer `/dev/serial/by-id/` symlinks in INI.
4. Power — external PSU or powered hub for marginal modems.
5. Test — `baycom-pr-ctl check` / `selftest`; PTT calibrate for ser12.

## Symptoms

| Symptom | kernel-ser12 | kiss-serial |
|---------|--------------|-------------|
| No device | Wrong tty/IRQ | Cable, driver, wrong `ttyUSBn` |
| IRQ OK, no PTT | Cable, TXD power | N/A — use KISS TNC PTT path |
| Garbled KISS | N/A | Wrong baud; bad cable/power |
| Works on DOS PC, not USB | Expected — use hardware UART | Use KISS firmware |

## Catalog cross-reference

| ID | Power note |
|----|------------|
| `baycom-ser12`, `baypac-bp2` | Port may draw from TXD; hardware UART |
| `kiss-serial-usb` | USB 5 V; self-powered TNC preferred |
| `unsupported-ser12-usb-adapter` | ser12 on USB UART only — excluded |

## References

- TFPCX §3.1 (external reference, DG0FT) — see [NOTICE](../NOTICE)
- [kernel baycom.rst](https://docs.kernel.org/networking/device_drivers/hamradio/baycom.html)
