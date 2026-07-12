# TNC-Inventar — Operator-Übersicht

Kurzreferenz für **beide** Packet-Radio-Setups auf AX25SRV.

---

## Unit A — Landolt TNC2C (Primary)

| | |
|--|--|
| **Gerät** | Landolt TNC2C, NORD><LINK 2.7b |
| **PC-Port** | `/dev/ttyS4` |
| **Host** | **19200 8N1**, DTR+RTS an |
| **Funk** | Albrecht AE 6110 (aktuell ab), CB **K24** 27,235 MHz |
| **Funk-Rate** | **2400** AFSK (TCM3105) |
| **HyBBX** | `tnc=tnc2c`, `hybbx-tnc2c.ini` |
| **Boot** | `./tnc2c-boot-wait.sh` + Strom aus/an |

**Status:** Seriell + Host ✅ | RF ⏳

Details: [TNC2C-OPERATIONS.md](TNC2C-OPERATIONS.md)

---

## Unit B — Stabo XM6012 + PK-TNC2 (Secondary)

| | |
|--|--|
| **Gerät** | Stabo XM 6012 CB + **PK-TNC2** TNC-2-Klasse |
| **PC-Port** | **TBD** (USB-Adapter empfohlen) |
| **Host** | vermutlich **9600 8N1** |
| **Funk** | integriert (Stabo FM 40 Kan.) |
| **Funk-Rate** | vermutlich **1200** AFSK |
| **HyBBX** | `tnc=tnc2`, `kiss_entry=auto` |
| **Software (Original)** | GPTNC / WinStop / Paxon (DOS/Win) |

**Status:** ⏳ Lieferung erwartet — noch nicht getestet

Details (intern): `research/tnc2c/ebay-227405716803.md`

---

## Wann welches Setup?

| Ziel | Setup |
|------|-------|
| HyBBX CB 2400, bestätigter Stack | **Unit A** (TNC2C) |
| 1200-Baud CB-Packet, Legacy-TNC | **Unit B** (PK-TNC2) |
| Vergleich / Redundanz | Beide parallel (verschiedene Seriell-Ports) |

---

## Schnell-Befehle (Unit A)

```bash
cd /home/akb/Code/tnc2c
./tnc2c-boot-wait.sh          # Strom-Zyklus während Skript läuft
./tnc2c-integration-test.sh     # HyBBX-Ready?
./tnc2c-health.sh               # Vollcheck ohne TX
```

---

## Sicherheit

- **VOX aus** (AE 6110)
- **PTT** nur mit Dummyload: `--tx`, `kiss on`, HyBBX-Send
- Pro Port nur **ein** Programm (HyBBX **oder** tnc2c-tools)

---

## Weiterführend

| Dokument | Inhalt |
|----------|--------|
| [TNC2C-REFERENCE.md](TNC2C-REFERENCE.md) | Pinout, LEDs, Tools |
| [HYBBX-TNC2C.md](HYBBX-TNC2C.md) | HyBBX Unit A |
| [../DEVELOPMENT.md](../DEVELOPMENT.md) | Roadmap |
