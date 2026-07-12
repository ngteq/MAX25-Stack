# TNC2C + HyBBX + CB — Interne Recherche

> **Nur intern.** Dieser Ordner wird **nicht veröffentlicht**.  
> Nutzbare Dokumentation für Betrieb und Referenz liegt in **`docs/`**.

Stand: 2026-07-10

## Single Source of Truth

Bei widersprüchlichen Notizen gilt:

**[tnc2c/CONFIRMED.md](tnc2c/CONFIRMED.md)** — bestätigte Fakten mit Datum und Evidenz.

Ältere Dateien (z. B. `board-from-photo.md` mit „4800 Baud“) können veraltete Hypothesen enthalten.

## Verzeichnis

| Pfad | Inhalt |
|------|--------|
| [tnc2c/CONFIRMED.md](tnc2c/CONFIRMED.md) | **Bestätigte Fakten Unit A** (Priorität) |
| [tnc2c/hardware-inventory.md](tnc2c/hardware-inventory.md) | **Beide TNCs** — Hardware-Vergleich |
| [tnc2c/development-architecture.md](tnc2c/development-architecture.md) | TNC-Stack, HyBBX Multi-TNC |
| [tnc2c/ebay-listing.md](tnc2c/ebay-listing.md) | Unit A — Landolt TNC2C (eBay 117173645481) |
| [tnc2c/ebay-227405716803.md](tnc2c/ebay-227405716803.md) | Unit B — Stabo + PK-TNC2 |
| [downloads/](downloads/) | PDFs und Text-Extrakte (Handbücher) |
| [cb-ae6110/](cb-ae6110/) | AE 6110 Bedienung, Verkabelung |
| [cables/](cables/) | RS-232 Kabel (richtig vs. falsch) |
| [hybbx/](hybbx/) | Produktions-INI CB K24 |
| [serial-tests/](serial-tests/) | Testprotokolle |
| [sources.md](sources.md) | URLs und Quellen |

## Öffentlich nutzbar (außerhalb research/)

| Dokument | Zweck |
|----------|-------|
| [../docs/TNC-INVENTORY.md](../docs/TNC-INVENTORY.md) | Beide TNCs — Operator |
| [../docs/TNC2C-OPERATIONS.md](../docs/TNC2C-OPERATIONS.md) | Betrieb Unit A |
| [../docs/HYBBX-TNC2C.md](../docs/HYBBX-TNC2C.md) | HyBBX Unit A |
| [../README.md](../README.md) | Einstieg |
| [../DEVELOPMENT.md](../DEVELOPMENT.md) | Roadmap |

## Kurzfazit (bestätigt)

| Komponente | Status |
|------------|--------|
| Seriell `/dev/ttyS4` 19200 8N1 | ✅ Host-Modus via boot-wait |
| Modemkabel | ✅ |
| Firmware 2.7b | ✅ |
| RF mit AE 6110 | ⏳ dokumentiert, Live-Test offen |
| FUNK-Brücke | ⏳ nicht fotografiert |
| **Unit B** (Stabo+PK-TNC2) | ⏳ Lieferung, INI-Vorlage fertig |

## Weiterentwicklung

[../DEVELOPMENT.md](../DEVELOPMENT.md)
