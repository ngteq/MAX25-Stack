# AE 6110 — Einstellungen für Packet (TNC2C / HyBBX)

Kanal **24** (27,235 MHz), Halbduplex, AFSK 1200/2200 Hz über TCM3105.

## Empfohlene Funkgerät-Einstellungen

| Einstellung | Wert | Warum |
|-------------|------|-------|
| Kanal | **24** | Kabel 24 / 27,235 MHz |
| Modulation | **FM** | EU-CB Standard, AFSK auf FM-Demodulator |
| VOX | **AUS** | Sonst Konflikt mit TNC-PTT |
| ASQ | **AUS** | Automatische Sperre stört Carrier Detect |
| SQ (manuell) | **0.F** oder **0,3–0,5** | CD-LED am TNC soll bei Signal reagieren |
| RF-Gain | **hoch** (R.8–R.9) | Schwache Packet-Signale |
| VOL | **~30–50 %** | Pegel für 3,5-mm-RX-Abgriff |
| Mikrofon | dran lassen | Nur für UP/DN/SQ — nicht per Mic-PTT senden |

## Bedienung (Kurz)

### VOX aus
- **[VOX]** drücken bis Anzeige erlischt

### ASQ aus
- **[SQ]** gedrückt halten bis **„AQ“** verschwindet

### Squelch (SQ)
1. **[SQ]** kurz → Display zeigt SQ, dann X.X
2. **[UP]/[DN]** am Mic: Pegel wählen
3. **[SQ]** oder 3 s warten zum Speichern

- `0.F` = Squelch aus (Rauschen hörbar)
- `0.1` … `2.8` = zunehmend geschlossen

### RF-Gain
1. **[EMG]** halten → **„R“** blinkt
2. **[UP]/[DN]**: Pegel erhöhen
3. **[EMG]** halten zum Verlassen

### FM/AM
- **[A/F]** → **FM** wählen

## TNC2C prüfen (mit angeschlossenem Funk)

1. Power-LED TNC an
2. Squelch öffnen → **Carrier-Detect-LED** reagiert
3. Sendetest (niedrige Leistung / Dummyload) → **PTT-LED**
4. Mike-Gain-Poti am TNC: leichter Rückgang im Monitor hörbar

## Typische Probleme

| Symptom | Maßnahme |
|---------|----------|
| CD immer an | SQ etwas schließen |
| CD nie an | SQ öffnen, VOL erhöhen, 3,5-mm-Kabel prüfen |
| Dauer-Senden | VOX aus, kein paralleler Mic-PTT |
| Kein Decode | FM prüfen, Mike-Gain, VOL, Antenne/SWR |

## Rechtlicher Hinweis

CB-Betrieb nur im zulässigen EU-CB-Bereich, 4 W, passende Antenne. Kein Senden ohne Antenne oder Dummyload.
