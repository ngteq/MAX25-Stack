# TNC2C — Brücken und Kalibrierung

> **Handbuch-Tabellen** (9,8304 / 2,4576 MHz). Dieses Board: **4,9152 MHz**, effektiv **19200** bei TERM „4800“.  
> Siehe [CONFIRMED.md](CONFIRMED.md).

## Brücke TERM (Terminal → PC)

Quarz **9,8304 MHz**:

| Position | Baud |
|----------|------|
| 1 | 9600 |
| 2 | 4800 |
| 3 | 2400 |
| 4 | 1200 |
| 5 | 600 |
| 6 | 300 |
| — | **19200** (erweitert, Position 1 bei 9,8304 MHz laut Tabelle) |

**Dieses Setup (Handbuch 9,8304 MHz):** TERM = **19200** — *bei unserem 4,9-MHz-Board effektiv 19200 bei Silkscreen „4800“, siehe CONFIRMED.md*

## Brücke FUNK (Modem → Funk)

Quarz **2,4576 MHz** (Standard):

| Position | Baud |
|----------|------|
| 1 | 1200 |
| 2 | 2400 |
| 3 | 4800 |
| 4 | 9600 |
| 5 | 19200 |
| 6 | 38400 |

**Dieses Setup:** FUNK Position **2** = **2400 Baud** (TCM3105)

## Modem-Abgleich (TCM3105)

1. NF Pin 1 und Pin 4 kurzschließen (Analog-Loopback)
2. Mike-Gain-Poti (1 kΩ, neben Modemquarz) ganz aufdrehen → CD-LED muss leuchten
3. Falls nicht: 10-Ω-Abgleichwiderstand durchtrennen
4. Terminal: `CALIbrate` → `D` → Oszilloskop 50 % Tastverhältnis oder UB/2 am 50-kΩ-Poti
5. Beenden mit `Q`

## Sendepegel (Mike-Gain)

- So einstellen, dass im Mithörempfänger ein **leichter Lautstärkerückgang** hörbar ist
- Referenz: cq-DL 8/86 S. 471 (FM-Hub DL8LE)
- FM-Hub bei 1200/2200 Hz möglichst ähnlich (max. ~6 dB Unterschied im Empfangsweg)

## BR1 (Uhrentakt)

- Standard: untere Brücke geschlossen
- Falls Software-Uhr 4× zu langsam: obere Brücke schließen, untere öffnen

## BR2 (PTT-Relais)

- Standard: Pin 13–14 überbrückt, kein Relais
- Bei PTT-Problemen: Relais + Freilauf-Diode nachrüsten, ~5 Ω in PTT-Leitung
