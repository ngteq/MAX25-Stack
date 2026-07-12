# TNC2C — Bestätigte Fakten (Single Source of Truth)

**Stand:** 2026-07-10  
**Gerät:** Landolt TNC2C, eBay [117173645481](ebay-listing.md)  
**Host:** AX25SRV, `/dev/ttyS4`  
**Status:** Seriell + Host-Modus bestätigt; Funk/CB noch nicht im Live-Betrieb

> Alle anderen `research/`-Dateien sind Arbeitsnotizen. Bei Widersprüchen gilt **diese Datei**.

---

## 1. Seriell PC ↔ TNC (bestätigt)

| Parameter | Wert | Evidenz |
|-----------|------|---------|
| Gerät | `/dev/ttyS4` | `tnc2c-serial.env`, alle Tests |
| Baud | **19200** | Autotest, minicom, boot-wait |
| Format | **8N1** | minicom Statuszeile; 7E1 nur Echo |
| Kabel | **Modemkabel** DB25↔DE9 | `research/cables/` |
| DB25 Pin 4↔5 | **überbrückt am TNC-Sockel** | User bestätigt |
| DTR/RTS | **müssen high** bleiben | boot-wait-Erfolg vs. printf-Fehlschlag |
| CTS am PC | oft **0** | unkritisch mit Pin-4↔5-Brücke + `-crtscts` |
| DSR | **1** | health/autotest |

**Nicht verwenden:** 4800, 9600, 7E1 — nur Müll oder Echo.

---

## 2. Firmware / Host-Modus (bestätigt)

| Parameter | Wert | Evidenz |
|-----------|------|---------|
| Firmware | **NORD><LINK 2.7b** DAMA/SMACK/XHOST | minicom INFO, boot-wait |
| EPROM | **T2.7b.10** | Platine-Foto |
| Checksum | **DC0A** | INFO-Ausgabe |
| Host-Boot | **`./tnc2c-boot-wait.sh`** + Strom-Zyklus | Terminal 2026-07-10 21:30, **OK: HOST** |
| Manuell | minicom 19200 8N1, `kiss off`, `INFO` | Terminal, Firmware-Banner |
| Echo-Modus | nach KISS/falschen Tests ohne Reset | autotest `--quick` ohne vorherigen Boot |

### Boot-Sequenz (bewährt)

```bash
pkill minicom
./tnc2c-boot-wait.sh
# Während Skript läuft: TNC-Strom AUS → 10s → AN
# → Boot-Banner passiv, OK: HOST
```

**Kritisch:** DTR muss **während** des Einschaltens high sein (Skript offen halten). Späteres Öffnen der Leitung → oft nur Echo.

---

## 3. Hardware Platine (Fotos, teilweise bestätigt)

| Merkmal | Wert | Status |
|---------|------|--------|
| Quarz sichtbar | **4,9152 MHz** | Foto `tnc2c.jpg` |
| Werkvariante | Landolt **4,9 MHz** | eBay + Landolt-Katalog |
| TERM-Brücke | Silkscreen „4800“, gelötet | Foto `tnc2c-2.jpg` |
| Effektive PC-Baud | **19200** (nicht 4800!) | gemessen; siehe Quarz-Tabelle |
| FUNK-Brücke | **nicht fotografiert** | offen — Ziel: Pos. 2 = 2400 |
| Batterie | >3,5 V | Foto |
| Modem | **TCM3105** | Platine |
| LEDs (oben→unten) | POWER, PTT, CD, CON, STA | Foto LED-Leiste |
| Boot-LEDs | **4+5 blinken** kurz | User bestätigt |

### Quarz / Brücken-Erklärung

Handbuch-Tabelle gilt für Quarz **9,8304 MHz**. Dieses Board hat **4,9152 MHz** (= Hälfte). Landolt dokumentiert bei 9,8-MHz-Umbau: **TERM „4800“ = 19200 PC-Baud**. Das passt zu den Messungen.

Siehe [jumpers-calibration.md](jumpers-calibration.md) für Handbuch-Tabellen (Referenz, nicht 1:1 für dieses Board).

---

## 4. Funk / CB (live getestet 2026-07-11)

| Parameter | Wert | Status |
|-----------|------|--------|
| Funkgerät | Albrecht AE 6110 VOX | angeschlossen |
| Kanal | **24** (27,235 MHz) | HyBBX-INI |
| Modem-Baud Funk | **2400** (TCM3105) | Handbuch FUNK Pos. 2 |
| RX-Verkabelung | **3,5 mm Tip → DIN Pin 4** | CD-LED ok |
| VOX | **AUS** | Pflicht für Packet |
| **TX** | nur wenn **LED3 (CD) AUS** | User bestätigt + Modem-Ton am 2. CB |
| **Host/Banner** | nur bei **ruhiger NF-Leitung** | Squelch zu, CD aus (siehe unten) |

### Squelch / CD — kritisch für Betrieb

| LED3 (CD) | Squelch (CB) | Wirkung |
|-----------|--------------|---------|
| **AN** | offen / Rauschen | Empfang erkannt — **TX blockiert** (Kanal belegt) |
| **AUS** | zu / Leitung ruhig | **TX möglich**, Boot/Banner zuverlässig |

**Praxis:**
- **Vor boot-wait / Host / TX:** Squelch **schließen** (CD aus, NF-Leitung frei/ruhig)
- **Empfang testen:** Squelch öffnen → CD bei Rauschen/Signal
- Offenes Squelch + Dauer-CD verhindert Senden und kann Host/Boot stören

Dieses Verhalten entspricht **DCD/CSMA** (Kanal busy) und sauberem NF-Pegel am TCM3105.

---

## 5. HyBBX (konfiguriert)

```ini
device = /dev/ttyS4
baud = 19200
serial_line = 8n1
rts_dtr = yes
modem = tcm3105
radio_baud = 2400
frequency_mhz = 27.235
```

Vollständig: [../hybbx/production-ini-cb-ch24.ini](../hybbx/production-ini-cb-ch24.ini)

**Hinweis:** Frühere HyBBX-Tests mit `7e1` — für dieses Gerät **`8n1`** verwenden.

---

## 6. Verworfene / widerlegte Annahmen

| Annahme | Ergebnis |
|---------|----------|
| TERM „4800“ → PC 4800 Baud | **falsch** — PC braucht 19200 |
| Handbuch 7E1 für dieses Gerät | **falsch** — 8N1 |
| `printf > /dev/ttyS4` für Reset | **funktioniert nicht** — kein DTR |
| `--quick` autotest nach Strom-Reset | **stört Boot** — falsche Baud zuerst |
| DTR-Drop beim Testen | **stört Terminal-Erkennung** |
| eBay-Kabel (Pin 2-2, 4-5) | **falsch** — kein RX |
| Reines Kabel-Loopback | **ausgeschlossen** — Zufallsbytes kein Echo |

---

## 7. Chronologie (wichtigste Meilensteine)

| Datum | Ereignis |
|-------|----------|
| 2026-07-10 | Modemkabel OK, 19200 8N1 Echo |
| 2026-07-10 | minicom: Firmware-Banner nach Strom-Reset |
| 2026-07-10 | `boot-wait`: **OK: HOST** passiv beim Einschalten |
| 2026-07-10 | Forum-Recherche: Echo/KISS/DTR bekanntes Muster |
| 2026-07-11 | TX bestätigt (2. CB, Modem-Ton); Stecker-Fix |
| 2026-07-11 | **TX nur bei CD aus**; Boot bei ruhiger NF-Leitung (SQ zu) |

---

## 8. Verweise

| Thema | Datei |
|-------|-------|
| Foren/DTR/Echo | [forum-serial-host.md](forum-serial-host.md) |
| Hardware beide Units | [hardware-inventory.md](hardware-inventory.md) |
| TNC-Stack / HyBBX | [development-architecture.md](development-architecture.md) |
| Platine (Fotos) | [board-from-photo.md](board-from-photo.md) |
| eBay Landolt | [ebay-listing.md](ebay-listing.md) |
| eBay Stabo+PK2 | [ebay-227405716803.md](ebay-227405716803.md) |
| Brücken Handbuch | [jumpers-calibration.md](jumpers-calibration.md) |
| CB-Verkabelung | [../cb-ae6110/wiring-tnc2c.md](../cb-ae6110/wiring-tnc2c.md) |
| Operator-Doku (öffentlich) | [../../docs/TNC2C-OPERATIONS.md](../../docs/TNC2C-OPERATIONS.md) |
| Referenz (öffentlich) | [../../docs/TNC2C-REFERENCE.md](../../docs/TNC2C-REFERENCE.md) |
