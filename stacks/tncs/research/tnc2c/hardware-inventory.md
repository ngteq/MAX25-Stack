# Hardware-Inventar — beide TNC-Setups

Stand: 2026-07-10

## Übersicht

| ID | Bezeichnung | Status | Host (PC) | Funk | HyBBX-Profil |
|----|-------------|--------|-----------|------|--------------|
| **A** | Landolt TNC2C | ✅ am AX25SRV | `/dev/ttyS4` 19200 8N1 | AE 6110 (ab) | `tnc2c` |
| **B** | Stabo XM6012 + PK-TNC2 | ⏳ Lieferung | TBD (USB/ttyS?) | integriert | `tnc2` |

---

## Unit A — Landolt TNC2C

| Merkmal | Wert | Evidenz |
|---------|------|---------|
| eBay | [ebay-listing.md](ebay-listing.md) | Anzeige |
| Firmware | NORD><LINK 2.7b, Checksum DC0A | boot-wait, minicom |
| EPROM | T2.7b.10 | Foto |
| Quarz | 4,9152 MHz | Foto `tnc2c.jpg` |
| TERM-Brücke | „4800“ (Silkscreen) → PC **19200** | Messung |
| FUNK-Brücke | **offen** — Ziel Pos.2 = 2400 | noch fotografieren |
| Modem | TCM3105 | Platine |
| Host-Port | DB25 (DCE) | Handbuch |
| Funk-Port | DIN 5-pol 180° | Handbuch |
| LEDs | POWER, PTT, CD, CON, STA | Foto |
| Batterie | >3,5 V Li | Foto |
| Strom TNC | 10–14 V DC, ~40 mA | Handbuch |
| PC-Kabel | Modemkabel DB25↔DE9 | bestätigt |
| Pin 4↔5 | am TNC überbrückt | User |

### Fotos im Repo

- `research/tnc2c/tnc2c.jpg` — Gesamtansicht, Quarz
- `research/tnc2c/tnc2c-2.jpg` — TERM-Brücke, LEDs

### Offen

- [ ] FUNK-Brücke fotografieren
- [ ] Zweiter Quarz (falls vorhanden) identifizieren
- [ ] CB AE 6110 wieder verkabeln + CD/PTT testen

---

## Unit B — Stabo XM 6012 + PK-TNC2 (Paket)

| Merkmal | Wert | Quelle |
|---------|------|--------|
| eBay | [227405716803](ebay-227405716803.md) | Anzeige |
| Funk | Stabo **XM 6012** (1994) | Anzeige |
| TNC | **PK-TNC2** / „PK 2“ (TNC-2-Klasse) | Anzeige + Recherche |
| Software-Ära | GPTNC (GP), WinStop, Paxon | Anzeige, Foren |
| FM | 26,965–27,405 MHz (40 Kan.) | cbradio.nl |
| AM | 27,005–27,135 MHz (12 Kan.) | cbradio.nl |
| Leistung FM | ~4 W | Specs |
| Mikrofon | 6-pol **Western** (Kabel brüchig) | Anzeige |
| Antenne | **PL-259** | Anzeige |
| TNC-Funk | vermutlich **9-pol** Stecker (TNC-2-Klasse) | DG1XPZ |
| TNC-PC | vermutlich **9-pol RS-232** (nicht DB25!) | DG1XPZ |
| TNC-Firmware | typ. **TF2.7b** (TheFirmware) | PK-TNC2-Doku |
| Funk-Rate (typ.) | **1200 baud AFSK** | PK-TNC2-Spec |
| Host-Rate (typ.) | 9600 **8N1** (Brücken 1200–19200) | PK-TNC2, HyBBX TNCS.md |
| LEDs TNC | Power, TX, Carrier, Connect, Status | DG1XPZ |
| Gehäuse | Alu grün eloxiert, ~110×32×95 mm | DG1XPZ |
| Strom TNC | 6–16 V, ~60 mA, 5,5/2,1 mm | DG1XPZ |
| Batterie | CR2032 | DG1XPZ |

### Lieferumfang laut Anzeige

- Stabo XM 6012 + Originalkarton + Anleitung
- PK-TNC2 + Kabel + Anleitung
- Mikrofonhalterung, Montagebügel
- PTT-Mic (Kabel defekt)

### Nach Ankunft — Inventar-Checkliste

1. [ ] Typenschild / EPROM-Label am TNC fotografieren
2. [ ] Host-Baud-Brücken am TNC
3. [ ] Kabel Funk↔TNC (9-pol?) und TNC↔PC
4. [ ] Seriell-Port am AX25SRV zuweisen (USB-Adapter?)
5. [ ] `./tnc2c-probe` / `./tnc2c-find` auf neuem Port
6. [ ] Mic-Adapter Western→4pol oder Ersatzmic

---

## Vergleich A vs B

| | Unit A (TNC2C) | Unit B (PK-TNC2) |
|--|----------------|------------------|
| Host-Format | **8N1** (7E1 = Echo) | **8N1** |
| Host-Baud | **19200** | vermutlich **9600** |
| Funk-Modem | TCM3105 | integriert (1200 AFSK) |
| Funk-Rate | **2400** AFSK | **1200** AFSK (typ.) |
| KISS-Eintritt | `kiss on` | `KISS ON` oder ESC+`@K` |
| DTR/RTS | **erforderlich** (boot-wait) | meist nicht (HyBBX: off) |
| DIN vs Western | DIN 5-pol (Funk) | Western 6-pol (Stabo Mic) |
| HyBBX | `tnc2c`, `modem=tcm3105` | `tnc2`, `radio_baud=1200` |

**Wichtig:** Beide TNCs **nicht** gleichzeitig auf demselben Seriell-Port. Zwei Instanzen HyBBX: `packet_radio1` + `packet_radio2` mit verschiedenen `device`.

---

## Kabel-Lager

| Kabel | Für | Status |
|-------|-----|--------|
| Modem DB25↔DE9 | TNC2C ↔ PC | ✅ |
| Falsch-eBay-Kabel | — | ❌ verworfen |
| Stabo/TNC-Kabel | Unit B | ⏳ mit Lieferung |

Siehe [../cables/rs232-modem-cables.md](../cables/rs232-modem-cables.md).
