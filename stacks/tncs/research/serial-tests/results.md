# Serielle Tests — Ergebnisse

Tools im Projektroot: `tnc2c-probe`, `tnc2c-find`, `tnc2c-chat.sh`

## Chronologie

### Phase 1 — Falsches Kabel (`/dev/ttyUSB0`)

| Test | Ergebnis |
|------|----------|
| Zugriff | OK |
| Leitungsstatus | RTS=1, CTS=0, DTR=1, DSR=0 |
| Baud/Format | 1200–19200, 7E1 und 8N1 |
| Befehle CR/INFO/HELP/? | **Keine Antwort** |
| LED | Blinkt bei Aktivität (nur TX-Richtung) |

**Fazit:** Kabel/Adapter-Pinbelegung falsch (eBay 25→9).

### Phase 2 — Modemkabel (`/dev/ttyS4`), ohne Funk

| Test | Ergebnis |
|------|----------|
| Zugriff | OK |
| Leitungsstatus | RTS=1, **CTS=1**, DTR=1, **DSR=1** |
| `tnc2c-probe` | **28 Treffer** |
| 19200 8N1 | Echo `INFO` → `INFO\r\n` |
| 19200 7E1 | Echo `INFO` → `INFO\r` |
| Host-Modus | Kein `cmd:` / keine INFO-Liste (KISS aktiv mit HyBBX) |

**Fazit:** Serielle Kette PC ↔ Kabel ↔ TNC2C **OK**.

### Phase 3 — HyBBX 1.7.5 (Produktion)

Log-Auszug (2026-07-10):

```
[packet_radio1] tnc=tnc2c protocol=kiss device=/dev/ttyS4
[tnc] host=19200 7E1 rts_dtr=on kiss_entry=kiss_on radio=2400 modem=tcm3105
[tnc] KISS active (port 0)
[ax25] 1 configured frequencies (27.235 … 27.235 MHz)
band=cb duplex=half modulation=afsk frequency_mhz=27.235
```

**Fazit:** HyBBX + TNC2C + CB-Konfiguration **startet erfolgreich**.

## Erkannte Parameter (`tnc2c-serial.env`)

```
TNC2C_DEV=/dev/ttyS4
TNC2C_BAUD=19200
TNC2C_LINE=8n1    # manuell sauberstes Echo; HyBBX nutzt 7e1
TNC2C_RADIO_BAUD=2400
TNC2C_MODEM=tcm3105
```

## Testbefehle

```bash
cd /home/akb/Code/tnc2c
make
./tnc2c-probe /dev/ttyS4
./tnc2c-find /dev/ttyS4
```

**Wichtig:** HyBBX nicht gleichzeitig auf `/dev/ttyS4` laufen lassen beim Probing.

## Offen

- RF-Live-Test mit AE 6110 auf Kanal 24
- CD/PTT-LED mit Funkgerät
- Mike-Gain-Kalibrierung am TCM3105
