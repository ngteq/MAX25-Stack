# Albrecht AE 6110 VOX — Übersicht

Quelle: [downloads/Albrecht-AE6110-VOX-manual.pdf](../downloads/Albrecht-AE6110-VOX-manual.pdf)

## Technische Daten (Auszug)

| Parameter | Wert |
|-----------|------|
| Versorgung | 13,2 V, max. 2 A |
| Sendeleistung | 4 W |
| Antenne | UHF SO-239 |
| FM-Frequenzhub | < 1,9 kHz |
| Audio | 8 Ω extern, 300–3000 Hz |
| Empfang | besser als 1 µV (20 dB SINAD) |

## EU-CB Standard

- 40 Kanäle FM/AM, **26,965–27,405 MHz**
- **Kanal 24 = 27,235 MHz** (Packet-Betrieb auf „Kabel 24“)

## Anschlüsse

| Anschluss | Verwendung |
|-----------|------------|
| ANT (hinten) | CB-Antenne, SWR < 2 empfohlen |
| **3,5 mm Mono** (hinten) | Externer Lautsprecher 8 Ω — **RX-Abgriff für TNC** |
| Mikrofonbuchse (4-pol) | PTT + Mic + Masse |
| Strom | 12 V, 5 A Sicherung im Kabel |

## Mikrofon-Stecker (Farben, typisch)

| Farbe | Funktion |
|-------|----------|
| Rot | PTT (gegen Masse = TX) |
| Weiß | Mikrofon + Electret-Bias (~6–7 V) |
| Schwarz | Masse |
| Blau | Masse (oft ungenutzt) |

**Hinweis:** Nur Original-Mikrofon für garantierte VOX-Funktion — für Packet ist VOX ohnehin **aus**.

## Bedienelemente (Packet-relevant)

| Taste | Funktion |
|-------|----------|
| VOL | Ein/Aus + Lautstärke |
| [SQ] | Rauschsperre (kurz) / ASQ (halten) |
| [A/F] | AM/FM, Scan (halten) |
| [VOX] | VOX ein/aus |
| [EMG] | Notruf CH9/19; **RF-Gain** (halten) |
| Mic [UP]/[DN] | Kanal, SQ, RF-Gain |

Siehe [packet-settings.md](packet-settings.md) für konkrete Packet-Einstellungen.
