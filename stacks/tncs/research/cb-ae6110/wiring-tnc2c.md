# Verkabelung TNC2C ↔ Albrecht AE 6110 VOX

## Empfohlene Verdrahtung

```
TNC2C Pin 2 (GND)  ──────────────  AE6110 Schwarz (Masse)
TNC2C Pin 3 (PTT)   ──────────────  AE6110 Rot (PTT)
TNC2C Pin 1 (TX-AF)  ──[opt. 1µF]──  AE6110 Weiß (Mikro)
TNC2C Pin 4 (RX-AF)  ──────────────  AE6110 3,5mm Tip (Empfang)
TNC2C Pin 2 (GND)   ──────────────  AE6110 3,5mm Sleeve (Masse)
```

## Warum 3,5-mm-Buchse für RX?

- Mono-Buchse hinten, 8 Ω Lautsprecher-Ausgang
- Eingebauter Lautsprecher schaltet ab bei Stecker
- Stabilerer Pegel als Mic-Leitung für Empfang

## TX / Mikrofon

- TNC Pin 1 → Weiß (Mic + Bias)
- Optional **1 µF** in Serie (Trennung Gleichspannung)
- Electret-Bias liefert das Funkgerät (~6–7 V)

## PTT

- TNC Pin 3 zieht PTT (Rot) gegen Masse
- **VOX am Funk aus**
- Mic-PTT nicht parallel nutzen

## Strom TNC2C

- Eigene **12-V-DC-Versorgung** an 2,1-mm-Buchse (250 mA Sicherung)
- Pin 5 (+12 V vom Funk) optional, nicht zwingend

## 10-Ω-Widerstand TNC Pin 4

- Behalten, wenn Abgriff **nach** Lautstärkeregler (3,5-mm-Buchse)
- Entfernen nur bei Abgriff **vor** Lautstärkeregler im Funk

## Schutz

- ~5 Ω in PTT-Leitung empfohlen (Handbuch TNC2C, falls Relais nachgerüstet)
- ZPD18 Überspannungsschutz PTT auf TNC-Platine

## ASCII-Übersicht

```
┌─────────────┐     NF 5-pol DIN      ┌──────────────┐
│   TNC2C     │◄─────────────────────►│  AE 6110 VOX │
│             │  1 TX, 2 GND, 3 PTT   │              │
│  /dev/ttyS4 │  4 RX, 5 +12V (opt.)  │  CH 24 FM    │
└──────┬──────┘                       │  3,5mm RX    │
       │ DB25 Modem                   │  Mic 4-pol   │
       ▼                              └──────┬───────┘
   AX25SRV PC                                Antenne
```
