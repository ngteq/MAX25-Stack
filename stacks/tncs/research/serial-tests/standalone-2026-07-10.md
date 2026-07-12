# TNC2C Standalone-Test (ohne Funk, nur /dev/ttyS4)

> **Vorläufiges Protokoll** vom Morgen — später am Tag Host-Modus via boot-wait bestätigt.  
> Aktueller Stand: [CONFIRMED.md](../tnc2c/CONFIRMED.md).

Stand: 2026-07-10 — Strom frisch, kein HyBBX, kein baycom, CB nicht angeschlossen.

## Umgebung

| Check | Ergebnis |
|-------|----------|
| HyBBX | aus |
| baycom/kissbridge | aus |
| Funk am TNC | **nicht angeschlossen** |
| Port | `/dev/ttyS4` frei |

## Seriell

| Parameter | Ergebnis |
|-----------|----------|
| Bestes Profil | **19200 8N1** |
| RTS / DSR | 1 |
| **CTS** | **0** (dauerhaft) |
| Spontanverkehr | 0 Bytes |

## Host-Modus

| Befehl | Antwort | Bewertung |
|--------|---------|-----------|
| `INFO` | `INFO\r\n.` | nur Echo + `.` |
| `HELP` | `HELP\r\n.` | nur Echo |
| `kiss off` | `kiss off\r\n.` | nur Echo |
| `RESTART` | `RESTART\r\n.` | nur Echo |
| Zufallsstring | `\x07\x07…\r\n.` | **kein** Echo → kein reines Kabel-Loopback |
| `cmd:` / INFO-Liste | — | **nie gesehen** |

**Fazit:** Datenweg PC↔TNC ok, aber **kein echter Host-/KISS-Dialog**. Software-Befehle lösen **kein PTT** aus (LED2 bleibt aus).

## LEDs ohne Funk (erwartet)

- **LED1** Power: an
- **LED3** CD: oft **an** (Pin4 offen / kein Abschluss)
- **LED2** PTT: nur bei echtem Senden
- **LED4/5**: kurz beim Einschalten, dann aus

## Wahrscheinliche Ursachen (priorisiert)

1. **CTS=0** — TNC meldet nicht „bereit“ → DB25 **Pin 4↔5** im Modemkabel überbrücken
2. TNC hängt in **Echo/Transparent** — Stromreset, dann `kiss off` in minicom
3. **TERM-Brücke** physisch prüfen (soll 19200 sein)
4. Firmware/EPROM oder defekter TNC (wenn nach CTS-Fix kein `cmd:`)

## Nächste Schritte (nur TNC2C)

```bash
./tnc2c-health.sh /dev/ttyS4
minicom -D /dev/ttyS4 -b 19200   # 8N1, dann kiss off, INFO
```

Erst bei **`cmd:`** oder INFO-Listing → `./tnc2c-health.sh --tx` oder Funk wieder an.

## Tool

`./tnc2c-health.sh` — kompletter Check (Abschnitte 1–7)
