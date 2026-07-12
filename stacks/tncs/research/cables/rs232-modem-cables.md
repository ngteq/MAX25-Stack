# RS-232 Kabel und Adapter

## TNC2C erwartet

- **DB25 Buchse** am TNC = **DCE** (wie Modem)
- PC/COM = **DTE**
- Verbindung mit **Modemkabel** oder **Modemadapter** (TX/RX gekreuzt)

## Korrekte Modem-Pinbelegung (DE9 ↔ DB25)

Wie auf Foto [RS232A259-modem-adapter.jpg](RS232A259-modem-adapter.jpg):

| DE9 (PC, DTE) | DB25 (TNC, DCE) | Signal |
|---------------|-----------------|--------|
| 1 | 8 | DCD |
| 2 | 3 | RXD ← vom TNC |
| 3 | 2 | TXD → zum TNC |
| 4 | 20 | DTR |
| 5 | 7 | GND |
| 6 | 6 | DSR |
| 7 | 4 | RTS |
| 8 | 5 | CTS |
| 9 | 22 | RI |

### Kette mit 1:1-Kabeln

```
USB-Seriell (DE9 Stecker, DTE)
    ↓ 1:1 DE9 (kein Nullmodem!)
DE9-Seite Adapter
    ↓ (fest im Adapter, Kreuzung)
DB25-Seite Adapter
    ↓ 1:1 DB25
TNC2C DB25 Buchse
```

## eBay-Kabel — NICHT geeignet

Angebot: https://www.ebay.de/itm/276338716740

**Stecker passen:** DB25 Stecker → TNC, DE9 Buchse → USB-Adapter ✓

**Pinbelegung falsch:**

```
eBay:     1-4, 2-2, 3-3, 4-5, 4-6, 5-7, 6-20, 8-20
Standard: 1-8, 2-3,  3-2,  4-20, 5-7, 6-6, 7-4, 8-5, 9-22
```

| Signal | Standard (TNC2C) | eBay-Kabel |
|--------|------------------|------------|
| TX/RX | 2↔3, 3↔2 | 2-2, 3-3 (Daten evtl. ok) |
| GND | 5-7 | 5-7 ✓ |
| RTS/CTS | 7-4, 8-5 | **fehlt / falsch** (4-5, 4-6, 6-20, 8-20) |
| DCD/DSR | 1-8, 6-6 | **falsch** |

### Gemessenes Verhalten mit eBay-Kabel (`/dev/ttyUSB0`)

- RTS=1, **CTS=0**, DSR=0
- LED blinkt bei Senden (PC→TNC)
- **Keine Antwort** auf INFO/HELP — RX/Handshake defekt

## Funktionierendes Setup (`/dev/ttyS4`)

- Richtiges **Modemkabel** oder Selbstbau-Adapter RS232A259
- **CTS=1, DSR=1**
- `tnc2c-probe`: 28 Treffer

## Kaufkriterien

**Gut:**
- „AT Modem Adapter“ / „DCE/DTE Modem“
- Pinbelegung wie Tabelle oben

**Schlecht:**
- Nullmodem
- Drucker-Kabel
- Belegung `2-2, 3-3` ohne RTS↔CTS-Kreuzung
- Gender: DB25 **Stecker** + DE9 **Buchse** für TNC+PC-Adapter
