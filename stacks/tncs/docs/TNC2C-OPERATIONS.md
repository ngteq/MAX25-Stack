# TNC2C — Betrieb

Kurzanleitung für den Landolt TNC2C an **AX25SRV** (`/dev/ttyS4`), CB Kanal 24.

**Bestätigte Parameter:** 19200 8N1, Firmware NORD><LINK 2.7b.

---

## Voraussetzungen

- TNC2C mit **eigenem Netzteil** (10–14 V DC)
- **Modemkabel** DB25 (TNC) ↔ DE9 (PC), nicht Nullmodem
- DB25 **Pin 4 und 5** am TNC-Sockel überbrückt
- User in Gruppe `dialout`
- **HyBBX und minicom beendet**, bevor Tools laufen

---

## 1. TNC einschalten (Host-Modus)

Der TNC braucht **DTR high während des Einschaltens**, sonst bleibt er im Echo-Modus.

**Am Funkgerät vor Boot/TX:** Squelch **schließen** (CD-LED **aus**, NF-Leitung ruhig).  
Mit offenem Squelch (CD dauernd an) ist **Senden blockiert** und Host/Banner unzuverlässig.

### Empfohlen: boot-wait

```bash
cd /home/akb/Code/tnc2c
pkill minicom 2>/dev/null
# CB: Squelch ZU, CD aus
./tnc2c-boot-wait.sh --tx-rx
```

1. Skript starten (wartet, DTR+RTS high)
2. **TNC-Strom ab** → 10–15 s warten
3. **TNC-Strom an** → LED 4+5 blinken kurz
4. Skript zeigt Firmware-Banner → **OK: HOST**

### Alternative: minicom

```bash
minicom -D /dev/ttyS4 -b 19200
```

Nach Strom-Reset: `kiss off` → Enter → `INFO` → Enter.  
Erwartung: `TheFirmware Version 2.7b … Checksum (DC0A) = DC0A`

---

## 2. Prüfen

```bash
./tnc2c-check.sh              # Port frei, Kurztest
./tnc2c-autotest.sh --host-check   # nur 19200-8N1 (~10s)
./tnc2c-health.sh             # vollständig, ohne Senden
```

| Ergebnis | Bedeutung |
|----------|-----------|
| **OK / HOST** | Seriell und Host-Modus in Ordnung |
| **ECHO** | Strom-Reset + boot-wait wiederholen |
| **DEGRADED** | Siehe Troubleshooting |

---

## 3. HyBBX starten

Siehe **[HYBBX-TNC2C.md](HYBBX-TNC2C.md)** für vollständige Checkliste.

Kurz:

```bash
# HyBBX stoppen vor Tests
sudo systemctl stop hybbx   # oder wie bei euch üblich

# INI-Ausschnitt (vollständig: research/hybbx/production-ini-cb-ch24.ini)
# baud = 19200, serial_line = 8n1, rts_dtr = yes
# modem = tcm3105, radio_baud = 2400, frequency_mhz = 27.235
```

HyBBX darf `/dev/ttyS4` nicht gleichzeitig mit `tnc2c-*`-Tools nutzen.

---

## 4. Funk anschließen (wenn Host steht)

1. **VOX am AE 6110: AUS**
2. Verkabelung: siehe [TNC2C-REFERENCE.md](TNC2C-REFERENCE.md) (DIN-Pinout)
3. RX: **3,5-mm Tip → DIN Pin 4**
4. **Squelch zu** für Boot/TX (CD **aus**); **Squelch auf** zum Empfang testen (CD bei Rauschen)
5. Erst **Empfang** prüfen, dann Senden mit Dummyload

```bash
./tnc2c-listen.sh             # passiv lauschen (sicher)
./tnc2c-health.sh --tx        # Sendetest — PTT zieht!
```

---

## 5. Sicherheit — PTT

**Niemals** ohne Dummyload/Antenne-Sicherheit:

- `kiss on` / KISS-Frames
- `./tnc2c-health.sh --tx`
- `./tnc2c-send-test.sh`
- `MONitor`, Connect-Befehle am TNC

Ungewolltes Senden wurde bei Software-Tests bestätigt (3–4× PTT).

---

## 6. Troubleshooting

```
                    TNC eingeschaltet?
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        boot-wait OK?              nur ECHO?
              │                         │
              ▼                         ▼
        ./tnc2c-health.sh      Strom AUS 10s → boot-wait
              │                         │
              ▼                    immer noch ECHO?
        HyBBX / Funk                   │
              │              ┌─────────┴─────────┐
              ▼              ▼                   ▼
        CD/PTT ok?     host-reset.sh      minicom manuell
              │        (ohne Strom-Reset)   kiss off + INFO
              ▼
        ./tnc2c-health.sh --tx
        (Dummyload!)
```

| Symptom | Maßnahme |
|---------|----------|
| Nur `INFO` zurück, kein Banner | Strom-Reset + **boot-wait** (nicht autotest --quick) |
| `~~` / Müll | Falsche Baud — muss **19200 8N1** sein |
| `cat /dev/ttyS4` hängt | Kein DTR — **boot-wait** oder minicom nutzen |
| CTS=0 | Normal an diesem PC; Pin 4↔5 am TNC reicht |
| **TX geht nicht, CD an** | Squelch **schließen** — CD muss **aus** sein |
| **Kein Banner / kein Host** | Squelch zu, NF ruhig; dann boot-wait + Strom-Zyklus |
| PTT ohne Befehl | HyBBX/KISS aktiv? `kiss off` in minicom |
| Port belegt | `pkill minicom`; HyBBX stoppen |

### Recovery ohne Strom-Reset

```bash
./tnc2c-host-reset.sh           # DTR+RTS, KISS-reset, kiss off, INFO
./tnc2c-host-reset.sh --no-kiss # ohne KISS-Frame
```

---

## 7. Typischer Workflow

| Schritt | Befehl |
|---------|--------|
| 1. Host holen | `./tnc2c-boot-wait.sh` + Strom-Zyklus |
| 2. Prüfen | `./tnc2c-health.sh` |
| 3. HyBBX | INI prüfen, starten, Log `KISS active` |
| 4. Funk | CB K24, VOX aus, CD prüfen |
| 5. Senden | `--tx` nur mit Dummyload |
