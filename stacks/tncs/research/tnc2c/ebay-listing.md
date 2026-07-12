# eBay-Angebot — dieses TNC2C-Exemplar

Stand: 2026-07-10

## Quelle

| Feld | Wert |
|------|------|
| URL | https://www.ebay.de/itm/117173645481 |
| Artikelnr. | **117173645481** |
| Titel | **Landolt TNC2C** |
| Zustand (laut Verkäufer) | **guter Zustand** |
| Verkauf | Privat — *Ohne Garantie, Rücknahme und Sachmängelgewährleistung* |

## Artikelbeschreibung (Verkäuertext, vollständig)

> Landolt TNC2C  
> Genaue Beschreibung bei DL0BN  
> guter Zustand  
> Ohne Garantie, Rücknahme und Sachmängelgewährleistung

*(Quelle: `https://itm.ebaydesc.com/itmdesc/117173645481` — eBay-Beschreibungs-iframe; Hauptseite war per Bot blockiert.)*

## Was die Anzeige **nicht** nennt

Keine Angaben zu: Firmware/EPROM, Baudraten, TERM-/FUNK-Brücken, Quarz, Kabel, Modem-Typ, Fotos im Text.

Verweis **„Genaue Beschreibung bei DL0BN“** → Amateurfunk-Clubstation [DL0BN](https://www.dl0bn.de/) (dort u. a. [TNC2C-Handbuch-PDF](https://www.dl0bn.de/dc7xj/Anleitungen/Anleitungen.htm) verlinkt). Technische Details müssen am Gerät gemessen werden.

## Einordnung (Landolt-Katalog)

Landolt bot den TNC2C werkseitig u. a. als **„Fertiggerät 4,9 MHz“** und **„Fertiggerät 9,8 MHz“** an ([landolt.de/tnc2c.htm](http://www.landolt.de/info/afuinfo/tnc2c.htm)). Das passt zum auf der Platine sichtbaren **4,9152-MHz-Quarz** — halbe Taktung gegenüber 9,8304 MHz, mit abweichender TERM-Brücken-Zuordnung (siehe Handbuch).

## Abgleich mit Messungen an diesem Gerät

| Thema | Anzeige | Gemessen / fotografiert |
|-------|---------|-------------------------|
| Hersteller/Typ | Landolt TNC2C | ✓ Landolt-Platine, TCM3105, EPROM **T2.7b.10** |
| Firmware | — | **NORD><LINK 2.7b** (minicom) |
| Quarz | — | **4,9152 MHz** sichtbar → **4,9-MHz-Variante** |
| TERM-Brücke | — | Silkscreen bis 4800, gelötet auf **4800** |
| Host-PC | — | **19200 8N1** (Firmware-Banner); 4800 7E1 = Müll |
| Funk | — | FUNK-Brücke noch offen; Ziel **2400** (TCM3105) |

**Fazit:** Anzeige bestätigt **echten Landolt TNC2C**, aber keine Seriell-Parameter. Die **4,9-MHz-Werkvariante** erklärt Quarz + Brücken-Rätsel besser als ein „falsch konfigurierter“ 9,8-MHz-TNC.
