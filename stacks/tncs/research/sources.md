# Quellen

## Primärdokumente (lokal)

| Datei | Beschreibung |
|-------|--------------|
| [downloads/TNC2C.txt](downloads/TNC2C.txt) | Text-Extrakt aus `../TNC2C.pdf` |
| [downloads/Albrecht-AE6110-VOX-manual.pdf](downloads/Albrecht-AE6110-VOX-manual.pdf) | Offizielle Bedienungsanleitung (DE/EN/…) |
| [downloads/Albrecht-AE6110-VOX-manual.txt](downloads/Albrecht-AE6110-VOX-manual.txt) | Text-Extrakt der Anleitung |
| [cables/RS232A259-modem-adapter.jpg](cables/RS232A259-modem-adapter.jpg) | Foto Selbstbau DE9↔DB25 Modemadapter |

## Online-Quellen (heruntergeladen bzw. recherchiert)

### TNC2C

- Landolt 9,8 MHz Umbau (Baud-Tabelle): https://www.landolt.de/info/afuinfo/tnc2c9_8mhz.htm
- Foren-Recherche Echo/Host/Linux: [tnc2c/forum-serial-host.md](tnc2c/forum-serial-host.md)
- FlexPacket Linux: https://gettoweb.de/amateurfunk/flexpacket-fuer-linux/
- Spaß am TNC2 (KISS/JHOST Reset): https://gettoweb.de/amateurfunk/spass-am-tnc2/
- Funkbasis TNC2 + Linux: https://funkbasis.de/viewtopic.php?t=51330
- TF 2.6 Befehle: https://www.ralfzimmermann.de/tf26_2.html
- Serial TNCs in Linux: https://www.complete.org/serial-tncs-in-linux/
- **Dieses Gerät (eBay):** https://www.ebay.de/itm/117173645481 — Details [tnc2c/ebay-listing.md](tnc2c/ebay-listing.md)
- Lokales PDF: `../TNC2C.pdf`

### Albrecht AE 6110 VOX

- https://www.k-po.com/files/uploads/product-downloads/1858/User-manual-AE-6110-VOX.pdf
- https://www.cbradio.nl/abrecht/downloads/Manual_Albrecht_AE6110_VOX_10_2020_ENG_DE_FR_ITA_HU_PL_RO.pdf
- https://diesnerfunk.de/media/pdf/78/79/f9/Gesamtanleitung_AE6110_VOX_10_2020_3.pdf
- https://www.manualslib.de/manual/764517/Albrecht-Ae-6110-Vox.html

### RS-232 / Kabel

- eBay-Angebot (falsche Belegung): https://www.ebay.de/itm/276338716740
- Pinbelegung in Anzeige: `1-4, 2-2, 3-3, 4-5, 4-6, 5-7, 6-20, 8-20`

### HyBBX (lokales Dev-Repo)

- `/home/akb/Code/hyBBX/` — 7E1/RTS-DTR-Unterstützung für TNC2C
- Produktions-INI auf Server: `/usr/local/hybbx/hybbx.ini`

### CB Kanal 24

- EU 40-Kanal-CB: Kanal 24 = **27,235 MHz** (Kabel 24 / „Packet-Kanal“ in der CB-Szene)
