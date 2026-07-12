# HyBBX — zwei TNCs (TNC2C + PK-TNC2)

Referenz-INI: `hybbx-dual.ini` (Basis: `/usr/local/hybbx/hybbx.ini`)

| Unit | TNC | Port | Host | Funk | Kanal |
|------|-----|------|------|------|-------|
| A | TNC2C | `/dev/ttyS4` | 19200 8N1 | 2400 AFSK | K24 27,235 MHz |
| B | PK-TNC2 | `/dev/ttyS5` | 9600 8N1 | 1200 AFSK | K25 27,245 MHz |

## Installieren

```bash
# INI (Dual-TNC mit Zeitversatz)
sudo cp ~/Code/tnc2c/hybbx-dual.ini /usr/local/hybbx/hybbx.ini

# HyBBX neu bauen + installieren (ax25_auto_stagger ab 2026-07-11)
cd ~/Code/hyBBX && cmake --build build
sudo cmake --install build --prefix /usr/local
sudo cp build/src/hybbx /usr/local/hybbx/hybbx   # falls install-Pfad abweicht
```

## Start (beide TNCs)

```bash
pkill hybbx; pkill minicom

# Unit A
sudo -u hybbx ~/Code/tnc2c/tnc2c-boot-wait.sh
# TNC2C: aus → Skript → an

# Unit B
sudo -u hybbx ~/Code/tnc2c/pktnc2-boot-wait.sh
# PK-TNC2: aus → Skript → an

# HyBBX
sudo -u hybbx /usr/local/hybbx/hybbx-start &
```

Erwartung im Log:

```
[packet_radio1] ... device=/dev/ttyS4 ... frequency_mhz=27.235
[packet_radio2] ... device=/dev/ttyS5 ... frequency_mhz=27.245
[tnc] KISS active (port 0)   # je Instanz
```

## Session

```bash
~/Code/tnc2c/hybbx-connect.sh
```

## On-Air zwischen den Units

1200 ↔ 2400 decodiert nicht — On-Air-Link nur nach Rate-Anpassung oder separatem COM-Setup (Maas).
Beide Frequenzen sind in HyBBX für Metadaten/Broadcast eingetragen.

## AX.25 Auto-Broadcast (staggered)

`[broadcast]` in `hybbx-dual.ini`:

| Einstellung | Wert | Bedeutung |
|-------------|------|-----------|
| `ax25_auto_interval` | 300 | Max. ein Beacon alle 5 Minuten **pro Kanal** |
| `ax25_auto_stagger` | 150 | 2,5 Min Abstand zwischen K24 und K25 |

Timing (beide Links online, sortiert nach MHz):

- **K24** (`packet_radio1`, 27,235 MHz): T+0 s, T+300 s, T+600 s …
- **K25** (`packet_radio2`, 27,245 MHz): T+150 s, T+450 s, T+750 s …

*Nach HyBBX-Neustart:* erster Beacon K25 nach ~150 s, K24 nach ~300 s; danach exakt wie oben (150 s Versatz, nie gleichzeitig).

Die Radios senden nie gleichzeitig. Einzel-TNC-Setup: `ax25_auto_stagger = 0` (oder weglassen).

Log beim Start: `[broadcast] … interval=300s stagger=150s …`

## Erwartetes Log bei funktionierendem Auto-Broadcast

Pro Kanal (staggered), in dieser Reihenfolge:

**K24 (27,235 MHz, ~T+0 / T+300 s …)**

```
[broadcast] ax25 27.235 MHz (1 hub): Broadcast: UN1TME online
[packet_radio1] RF TX UN1TME>QST (28 bytes)
```

**K25 (27,245 MHz, ~T+150 / T+450 s …)**

```
[broadcast] ax25 27.245 MHz (1 hub): Broadcast: UN1TME online
[packet_radio2] RF TX UN1TME>QST (28 bytes)
```

- `(1 hub)` = ein Circuit-Link hat das HBX-Frame per TCP erhalten (noch **kein** RF-Beweis).
- `[packet_radioN] RF TX …` = KISS an TNC gesendet — das ist der RF/PTT-Nachweis.
- Fehlt `RF TX` direkt nach `(1 hub)`, Circuit-Downlink oder TNC-TX prüfen (Log: `circuit disconnected`, `AX25_UI unpack failed`, `RF TX failed`).

Circuit stabil:

```
[packet_radio1] linked to internal circuit 127.0.0.1:7323 (HBX)
[packet_radio2] linked to internal circuit 127.0.0.1:7323 (HBX)
[circuit] link authenticated id=packet-radio1 … 27.235MHz
[circuit] link authenticated id=packet-radio2 … 27.245MHz
```

Kein ständiges `circuit disconnected — reconnecting` im Leerlauf (Bug bei O_NONBLOCK ohne poll: behoben ab 2026-07-11).

## Nur TNC2C (Produktion heute)

Einzel-INI bleibt unverändert in `/usr/local/hybbx/hybbx.ini` ohne `packet_radio2`.
