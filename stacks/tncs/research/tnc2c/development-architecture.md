# TNC-Stack — Entwicklungsarchitektur

Stand: 2026-07-10  
Ziel: Beide TNCs (TNC2C + PK-TNC2) unter HyBBX auf AX25SRV betreibbar machen.

---

## Schichtenmodell

```
┌─────────────────────────────────────────────────────────────┐
│  Applikation (HyBBX Main/Secondary, BBS, APRS, DX)          │
├─────────────────────────────────────────────────────────────┤
│  AX.25 / HBX (Routing, Connect, UI-Frames)                  │
├─────────────────────────────────────────────────────────────┤
│  KISS (0xC0 … 0xC0, Port 0, Parameter-Frames)               │
├─────────────────────────────────────────────────────────────┤
│  Host-Dialog (kiss on/off, INFO, cmd:, MODEM, MYCALL)       │
├─────────────────────────────────────────────────────────────┤
│  Boot / Recovery (DTR-Timing, Strom-Zyklus, KISS-Reset)     │  ← tnc2c-boot-wait
├─────────────────────────────────────────────────────────────┤
│  Seriell (Baud, Parität, RTS/DTR, Pin 4↔5)                  │
├─────────────────────────────────────────────────────────────┤
│  Kabel + Hardware (TNC, Funk, Antenne)                      │
└─────────────────────────────────────────────────────────────┘
```

**Regel:** Jede Schicht setzt die darunterliegende voraus. HyBBX startet bei **KISS** — Boot/Host muss vorher stehen (TNC2C) oder TNC muss KISS-ready sein (PK-TNC2).

---

## Unit A — Landolt TNC2C (implementiert)

| Schicht | Tool / Code | Status |
|---------|-------------|--------|
| Boot | `tnc2c-boot-wait.sh` | ✅ |
| Host | minicom, `host-reset`, `autotest --host-check` | ✅ |
| KISS | `tnc2c-health.sh --tx`, HyBBX `kiss_on_startup` | ⏳ RF offen |
| HyBBX | `hybbx-tnc2c.ini`, `tnc=tnc2c` | ⏳ Live-Test |
| RF | CB AE 6110, 2400 AFSK | ⏳ abgeklemmt |

### TNC2C-spezifische Besonderheiten

1. **DTR während Power-On** — ohne `boot-wait` → Echo-Modus
2. **8N1** statt Handbuch-7E1
3. **19200** statt TERM-Silkscreen „4800“
4. HyBBX-Default `tnc2c` = 7E1 → **INI override `serial_line=8n1`**

### Geplante Library (`tnc2c-host`)

```python
# Zukunft — einheitliche API
class Tnc2cHost:
    def boot_wait(self, dev, power_cycle_callback) -> bool
    def ensure_host(self, dev) -> bool      # INFO banner
    def kiss_on(self) / kiss_off(self)
    def open_kiss_stream(self) -> Iterator[bytes]
```

---

## Unit B — PK-TNC2 + Stabo (vorbereitet)

| Schicht | Geplant | Status |
|---------|---------|--------|
| Inventar | Fotos, Brücken, Kabel | ⏳ Ankunft |
| Seriell | `tnc2c-probe` auf neuem Port | ⏳ |
| Host | `*` Autobaud, INFO, TF2.7b Banner | ⏳ |
| KISS | `KISS ON` oder ESC+`@K` | ⏳ |
| HyBBX | `tnc=tnc2`, `kiss_entry=auto` | INI-Vorlage |
| RF | Stabo XM6012 FM, 1200 AFSK | ⏳ |

### HyBBX-Profil PK-TNC2

Siehe `research/hybbx/hybbx-stabo-pk2.ini`:

```ini
tnc = tnc2
protocol = kiss
baud = 9600
serial_line = 8n1
kiss_entry = auto
radio_baud = 1200
modulation = afsk
```

Kein `boot-wait` nötig (DTR optional) — aber **Autobaud** mit `*` beim ersten Connect testen.

### Unterschiede zu TNC2C

| Thema | TNC2C | PK-TNC2 |
|-------|-------|---------|
| HyBBX `rts_dtr` | **yes** | off (default) |
| KISS entry | `kiss_on` | **auto** |
| Host parity | 8N1 (override) | 8N1 (native) |
| Funk connector | DIN 5 | 9-pol (typ.) |
| Boot ritual | **Strom + DTR** | meist Plug&Play |

---

## HyBBX Multi-TNC (Ziel)

```ini
[transport.packet_radio1]
tnc = tnc2c
device = /dev/ttyS4
link_id = cb2400
frequency_mhz = 27.235
...

[transport.packet_radio2]
tnc = tnc2
device = /dev/ttyUSB0
link_id = cb1200
frequency_mhz = 27.235
...
```

HyBBX unterstützt bis zu 8 Instanzen — siehe `/home/akb/Code/hyBBX/docs/TNCS.md`.

---

## Test-Matrix (Entwicklung)

| Test | Unit A | Unit B |
|------|--------|--------|
| Seriell scan | `tnc2c-probe /dev/ttyS4` | `tnc2c-probe /dev/ttyUSB0` |
| Host banner | `boot-wait` | `INFO` / `*` autobaud |
| Health | `tnc2c-health.sh` | anpassen / generisch |
| KISS TX | `--tx` + Dummyload | nach Host ok |
| HyBBX log | `KISS active` | `KISS active` |
| RF loopback | Pin1↔4 + CALIBRATE | TNC-2 Loopback laut Anleitung |

---

## Lücken / To-Build

1. **`tnc2c-integration-test.sh`** — HyBBX-Ready-Check (HOST ohne Strom-Reset wenn möglich)
2. **`tnc2-probe`** oder erweitertes `tnc2c-probe` für TF2.7 / PK-TNC2 Marker
3. **`hybbx-prestart.sh`** — boot-wait → HyBBX start (Unit A)
4. **Doku Unit B** nach Inventar-Fotos vervollständigen
5. **CONFIRMED.md** für Unit B anlegen nach ersten Messungen

---

## Referenzen

- HyBBX TNC-Profile: `/home/akb/Code/hyBBX/docs/TNCS.md`
- PK-TNC2 Hardware: [DG1XPZ](https://qsl.net/dg1xpz/amateurfunk/pktnc2.html)
- Intern bestätigt: [CONFIRMED.md](CONFIRMED.md)
- Operator: [../../docs/TNC-INVENTORY.md](../../docs/TNC-INVENTORY.md)
