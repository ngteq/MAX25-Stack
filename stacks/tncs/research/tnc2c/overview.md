# Landolt TNC2C — Übersicht

> Bestätigte Werte: [CONFIRMED.md](CONFIRMED.md). Operator-Doku: [../../docs/TNC2C-REFERENCE.md](../../docs/TNC2C-REFERENCE.md).

Quelle: `../TNC2C.pdf` / [downloads/TNC2C.txt](../downloads/TNC2C.txt)

## Hersteller / Vertrieb

- Frankfurter PR-Gruppe (DDØZR, DC2FI, DB5ZK, DB1ZG)
- Vertrieb: Landolt Computer, Hellmut Landolt DF5FF, Maintal

## Hardware dieses Exemplars

| Merkmal | Wert |
|---------|------|
| Herkunft | eBay [117173645481](https://www.ebay.de/itm/117173645481) — siehe [ebay-listing.md](ebay-listing.md) |
| Werkvariante (Landolt) | vermutlich **4,9 MHz** (Quarz 4,9152 MHz auf Platine) |
| Modem-IC | **TCM3105** (TI, Bell 202 AFSK) |
| Host-Port | DB25, **DCE** (wie Modem) |
| NF | 5-pol DIN 180° |
| Strom | 10–14 V DC, ~40 mA Empfang, Sicherung 250 mA träge |
| Terminal-Brücke | **19200** (Position 1 bei 9,8304 MHz Quarz) — *dieses Board: 4,9152 MHz, Brücke „4800“, PC gemessen **19200 8N1*** |
| Funk-Brücke | **2400** (Position 3 bei 2,4576 MHz Quarz) |

## LEDs

| LED | Bedeutung |
|-----|-----------|
| Power | Betriebsspannung |
| PTT | Senden aktiv |
| Carrier Detect | Träger / Modem-Empfang |
| Connected | Verbindung (Host) |
| Status | Status |

Nach Einschalten: Power, Status, Connected an → nach 2–3 s Status/Connected aus = betriebsbereit.

## Wichtige Befehle (Host-Modus, nicht in KISS)

- `INFO` — Befehlsliste und Standardwerte
- `HELP` — Kurzanleitung
- `RESTART` — nach Änderung der Schnittstellenparameter
- `CALIbrate` — Modem-Abgleich (siehe [jumpers-calibration.md](jumpers-calibration.md))

In **KISS-Modus** (HyBBX) kommt nur Kommando-Echo, kein `cmd:`-Prompt — erwartetes Verhalten.
