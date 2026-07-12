# TNC2C Platine — Fotos `tnc2c.jpg` + `tnc2c-2.jpg`

> **Hinweis:** Frühe Hypothese „4800 Baud“ ist **widerlegt**. Bestätigt: **19200 8N1**.  
> Siehe [CONFIRMED.md](CONFIRMED.md).

Stand: 2026-07-10

## Batterie
> 3,5 V — **ok**

## Quarz (Gesamtansicht `tnc2c.jpg`)
- Sichtbar: **4,9152 MHz** (Mitte der Platine)
- Handbuch nennt oft 2,4576 MHz (FUNK) und 9,8304 MHz (TERM) — dieses Board weicht ab

## TERM-Brücke (`tnc2c-2.jpg`) — **WICHTIG**

Silkscreen **TERM** mit Baud-Werten:
`300 | 600 | 1200 | 2400 | 4800`

**Aktuell gelötet: 4800** (Brücke bei der 4800-Beschriftung)

→ Host/Terminal des TNC läuft auf **4800 Baud**, **nicht 19200**.

Das erklärt:
- Echo bei 19200, aber kein `cmd:`
- HyBBX/`tnc2c-health` mit 19200 falsch konfiguriert

### Korrekte PC-Einstellung (laut Platine)
```
4800 7E1   (Handbuch-Standard für TNC2C)
```
ggf. auch `4800 8N1` testen.

## LEDs (`tnc2c-2.jpg`, von oben nach unten)
| # | Label |
|---|-------|
| 1 | POWER |
| 2 | PTT |
| 3 | CD |
| 4 | CON |
| 5 | STA |

(Reihenfolge auf Gesamtfoto horizontal anders angeordnet — Beschriftung an der LED-Leiste maßgeblich.)

## EPROM
- Aufkleber: **T2.7b.10** / **A 2.75.10**

## FUNK-Brücke
- Auf den Fotos **nicht sichtbar** — separate Nahaufnahme nötig (zweite 6er-Reihe „FUNK“)

## DB25 vs DIN
- **DB25** Pin 4+5 Brücke = RTS/CTS (RS-232) ✓
- **DIN** Pin 4+5 **nicht** brücken (RX + 12 V)

## Nächste Schritte
```bash
minicom -D /dev/ttyS4 -b 4800   # Parität E, 7 Bit, 1 Stop
# kiss off → INFO
./tnc2c-health.sh   # nach Update von tnc2c-serial.env auf 4800
```

Wenn 19200 am TNC gewünscht: TERM-Brücke umsetzen (und passenden Quarz/Tabelle beachten).
