# Entwicklung — tnc2c + HyBBX + CB

Roadmap und interner Stand. Operator-Doku: [docs/TNC2C-OPERATIONS.md](docs/TNC2C-OPERATIONS.md).

## TNC-Stack (Schichten)

```
┌─────────────────────────────────────────┐
│  HyBBX (AX.25, Routing, Applikation)    │
├─────────────────────────────────────────┤
│  KISS (Frames, kiss on/off)             │  ← tnc2c-health --tx, send-test
├─────────────────────────────────────────┤
│  Host (kiss off, INFO, cmd:, MYCALL)   │  ← minicom, host-reset
├─────────────────────────────────────────┤
│  Boot (DTR high während Strom-Ein)     │  ← tnc2c-boot-wait ✅
├─────────────────────────────────────────┤
│  Seriell (19200 8N1, RTS/DTR, Pin 4↔5) │  ← tnc2c-serial.env ✅
├─────────────────────────────────────────┤
│  Kabel (Modemkabel DB25↔DE9)           │  ✅
└─────────────────────────────────────────┘
```

Jede Schicht baut auf der darunter — **Boot ohne DTR = Echo-Modus**.

## Aktueller Stand (2026-07-10)

| Schicht | Status | Evidenz |
|---------|--------|---------|
| Kabel / Seriell | ✅ | Modemkabel, 19200 8N1 |
| Boot (boot-wait) | ✅ | OK: HOST, passives Banner |
| Host (minicom/INFO) | ✅ | NORD><LINK 2.7b, Checksum DC0A |
| KISS / TX | ⏳ | nicht mit Funk getestet |
| RF / CB AE 6110 | ⏳ | abgeklemmt für Standalone |
| HyBBX Live-Packet | ⏳ | INI fertig, RF offen |

**Single Source of Truth (intern):** `research/tnc2c/CONFIRMED.md`

## Phasen

### Phase A — Seriell + Host ✅

- [x] Modemkabel vs. falsches eBay-Kabel
- [x] 19200 8N1 bestätigt (nicht 7E1, nicht 4800)
- [x] `tnc2c-boot-wait.sh` — DTR während Power-On
- [x] `tnc2c-host-reset.sh`, `tnc2c-autotest.sh`
- [x] `tnc2c-serial.env`
- [x] Operator-Doku (`docs/`)

### Phase B — HyBBX Integration ⏳

- [x] INI CB K24 (`hybbx-tnc2c.ini`, `research/hybbx/production-ini-cb-ch24.ini`)
- [x] HyBBX TNC2C-Profil (`serial_line=8n1`, `rts_dtr=yes`)
- [x] Integrations-Doku [`docs/HYBBX-TNC2C.md`](docs/HYBBX-TNC2C.md)
- [x] `tnc2c-integration-test.sh`
- [ ] HyBBX starten mit bestätigtem Host/Boot
- [ ] KISS-Frames im Log

### Phase C — Funk-Hardware ⏳

- [ ] **Stabo XM 6012 + PK2** ankommen (eBay [227405716803](research/tnc2c/ebay-227405716803.md)) — separates 9600-Setup
- [ ] **FUNK-Brücke fotografieren** (Pos. 2 = 2400 erwartet)
- [ ] CB AE 6110 wieder anschließen
- [ ] CD-LED bei Rauschen / SQ
- [ ] PTT-LED bei Sendetest (Dummyload)
- [ ] Mike-Gain / VOL / SQ justieren
- [ ] Optional: `CALIbrate` (Loopback Pin 1↔4)

### Phase D — RF / Packet ⏳

- [ ] Live-Packet auf Kabel 24
- [ ] TXDELAY / Persist für CB halbduplex
- [ ] Ergebnisse in `research/serial-tests/`

### Phase F — Unit B (Stabo + PK-TNC2) ⏳

- [x] eBay-Recherche [227405716803](research/tnc2c/ebay-227405716803.md)
- [x] HyBBX-Vorlage `research/hybbx/hybbx-stabo-pk2.ini` (`tnc=tnc2`)
- [ ] Hardware inventarisieren (Fotos, Brücken, Kabel)
- [ ] Seriell-Port zuweisen (`ttyUSB0`?)
- [ ] Host + KISS testen (`tnc2c-probe`, HyBBX)
- [ ] CB 1200 AFSK mit Stabo FM

Siehe [research/tnc2c/hardware-inventory.md](research/tnc2c/hardware-inventory.md).

### Phase E — TNC-Stack Library (optional)

- [ ] `tnc2c-host` Modul (Boot + DTR + kiss off/on)
- [ ] Einheitliche API für HyBBX/andere Daemon
- [ ] KISS-Sniffer (RX only)

## Sicherheit

**Niemals** ohne Dummyload bei angeschlossenem Funk + Antenne:

- `kiss on`, KISS-Frames, `--tx`, `MONitor`

Stattdessen: `./tnc2c-listen.sh`

## Workflow

1. HyBBX/minicom stoppen
2. `./tnc2c-boot-wait.sh` + Strom-Zyklus
3. `./tnc2c-integration-test.sh` oder `./tnc2c-health.sh`
4. Funk → CD/PTT → `./tnc2c-health.sh --tx` (Dummyload)
5. HyBBX starten — siehe `docs/HYBBX-TNC2C.md`

## Repos

| Pfad | Rolle |
|------|-------|
| `/home/akb/Code/tnc2c/` | Tools, `docs/`, interne `research/` |
| `/home/akb/Code/hyBBX/` | HyBBX-Dev |
| `/usr/local/hybbx/hybbx.ini` | Produktion AX25SRV |

## Nächste Hardware-Schritte

1. **FUNK-Brücke** Nahaufnahme (6er-Reihe „FUNK“)
2. **CB wieder an** — RX Tip→Pin4, VOX aus
3. **CD-LED** prüfen
4. **TX mit Dummyload** — PTT-LED, `./tnc2c-health.sh --tx`
