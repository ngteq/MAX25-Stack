# TNC2C — NF-Buchse (5-pol DIN 180°)

Von vorne auf die Buchse gesehen:

```
    Pin 2 (GND)
Pin 4 (RX)   Pin 1 (TX/Mic)
    Pin 3 (PTT)
    Pin 5 (+12V)
```

| Pin | Funktion | Impedanz / Hinweis |
|-----|----------|-------------------|
| 1 | Mikrofon-Eingang (TX-Audio zum Funk) | ~600 Ω |
| 2 | Masse | |
| 3 | PTT | gegen Masse = Senden |
| 4 | Lautsprecher-Ausgang (RX vom Funk) | ~10 Ω |
| 5 | +12 V vom Funkgerät | optional |

## 10-Ω-Widerstand an Pin 4

- Dient als Abschluss des NF-Verstärkers bei abgeschaltetem Lautsprecher
- **Entfernen**, wenn NF **vor** dem Lautstärkeregler im Funk abgegriffen wird

## Stromversorgung

- Empfohlen: eigene **DC-Buchse 2,1 mm**, 10–14 V, 250 mA Sicherung
- Pin 5 optional vom Funk — Außenhülse der DC-Buchse **niemals** auf +12 V legen

## Verbindung zum AE 6110

Siehe [../cb-ae6110/wiring-tnc2c.md](../cb-ae6110/wiring-tnc2c.md).
