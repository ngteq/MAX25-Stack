# TNC2C — Serielle Host-Schnittstelle (DB25)

> **Hinweis:** HyBBX `7e1` hier veraltet — dieses Gerät nutzt **8n1**. Siehe [CONFIRMED.md](CONFIRMED.md).

## Parameter (Handbuch)

- **7 Bit, Even Parity, 1 Stopbit (7E1)**
- Hardware-Handshake **RTS/CTS** (CTS zur Terminal-Freigabe)
- DCE-Pinbelegung (wie Modem)

## DB25 Pinbelegung

| Pin | Signal | Anmerkung |
|-----|--------|-----------|
| 1 | NC | |
| 2 | TXD | TNC sendet → PC empfängt |
| 3 | RXD | PC sendet → TNC empfängt |
| 4 | RTS | |
| 5 | CTS | |
| 6 | DSR | intern +5 V |
| 7 | GND | |
| 8 | DCD | intern +5 V |
| 9 | +12 V | optional (Commodore PC) |

## Kabeltyp

**Modemkabel** (nicht Nullmodem): TX/RX und RTS/CTS müssen korrekt gekreuzt sein.
Siehe [../cables/rs232-modem-cables.md](../cables/rs232-modem-cables.md).

## Gemessene Werte (dieser Host, 2026-07-10)

| Port | Kabel | RTS | CTS | DTR | DSR | Ergebnis |
|------|-------|-----|-----|-----|-----|----------|
| `/dev/ttyUSB0` | eBay falsch | 1 | **0** | 1 | 0 | Keine Antwort |
| `/dev/ttyS4` | Modemkabel OK | 1 | **1** | 1 | **1** | 28 Treffer in `tnc2c-probe` |

## Baudrate / Parität (dieses Gerät)

| Einstellung | Verhalten |
|-------------|-----------|
| **19200 8N1** | Sauberstes Echo (`INFO` → `INFO\r\n`) |
| **19200 7E1** | Echo mit `\r` (HyBBX-Standard für TNC2C) |
| 9600 / 2400 7E1 | Auf diesem Gerät zuvor verstümmelt |

**TERM-Brücke** muss zur Host-Baudrate passen. Dieses Exemplar: **19200**.

## HyBBX-Einstellung

```ini
device = /dev/ttyS4
baud = 19200
serial_line = 7e1
rts_dtr = yes
```

Log bestätigt: `host=19200 7E1 rts_dtr=on`

## Hinweise aus Handbuch

- Nur TXD/RXD: Widerstand 4,7 kΩ zwischen MAX232 Pin 2 und 8
- Manche PCs: DB25 Pin 4 und 5 im Kabel überbrücken
- Nach Parameteränderung: `RESTART` am TNC
