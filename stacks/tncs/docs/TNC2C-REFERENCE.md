# TNC2C — Referenz

Kompakte Referenz für **dieses** Landolt TNC2C-Exemplar (AX25SRV).

---

## Bestätigte Parameter

| Parameter | Wert |
|-----------|------|
| Port | `/dev/ttyS4` |
| Host-Baud | **19200** |
| Host-Format | **8N1** |
| Firmware | NORD><LINK **2.7b** (EPROM T2.7b.10) |
| Funk-Modem | TCM3105, **2400** Baud AFSK |
| CB-Kanal | **24** (27,235 MHz) |
| Quarz (sichtbar) | 4,9152 MHz |
| TERM-Brücke (Silkscreen) | „4800“ → effektiv **19200** am PC |

Konfiguration: `tnc2c-serial.env`

---

## LEDs (Leiste, oben → unten)

| # | Label | Bedeutung |
|---|-------|-----------|
| 1 | POWER | Betriebsspannung |
| 2 | PTT | Senden aktiv |
| 3 | CD | Carrier Detect (Modem/Rauschen) |
| 4 | CON | Connected |
| 5 | STA | Status |

**Boot:** LED 4+5 blinken kurz beim Einschalten — normal.

**Ohne Funk:** LED 3 oft dauernd AN (Pin 4 offen).

---

## DB25 (PC, Host-Port)

DCE — **Modemkabel** zum PC. Pin 4↔5 **am TNC überbrücken**.

| Pin | Signal |
|-----|--------|
| 2 | TXD (TNC → PC) |
| 3 | RXD (PC → TNC) |
| 4 | RTS |
| 5 | CTS |
| 6 | DSR (+5 V intern) |
| 7 | GND |
| 8 | DCD (+5 V intern) |

---

## DIN 5-pol (Funk)

```
     Pin 2 GND
Pin 4 RX      Pin 1 TX/Mic
     Pin 3 PTT
     Pin 5 +12V
```

| Pin | Funktion | AE 6110 |
|-----|----------|---------|
| 1 | TX-Audio → Funk | Weiß (Mic) |
| 2 | Masse | Schwarz |
| 3 | PTT | Rot |
| 4 | RX-Audio ← Funk | 3,5 mm **Tip** |
| 5 | +12 V (optional) | — |

**VOX am Funk: AUS.**

---

## Tool-Matrix

| Situation | Tool | PTT-Risiko |
|-----------|------|------------|
| **TNC einschalten / Host holen** | `./tnc2c-boot-wait.sh` | nein |
| Port frei? Kurztest | `./tnc2c-check.sh` | nein |
| Host ohne Strom-Reset | `./tnc2c-host-reset.sh` | nein |
| Schnelltest 19200 | `./tnc2c-autotest.sh --host-check` | nein |
| Alle Baud-Profile | `./tnc2c-autotest.sh --quick` | nein* |
| Vollständiger Check | `./tnc2c-health.sh` | nein |
| Sendetest | `./tnc2c-health.sh --tx` | **ja** |
| KISS-Einzeltest | `./tnc2c-send-test.sh` | **ja** |
| Passiv lauschen | `./tnc2c-listen.sh` | nein |
| HyBBX-Ready | `./tnc2c-integration-test.sh` | nein |
| Interaktiv | `minicom -D /dev/ttyS4 -b 19200` | bei Befehlen |
| Port/Baud finden | `./tnc2c-probe`, `./tnc2c-find` | nein |
| Manuell chatten | `./tnc2c-chat.sh` | bei Befehlen |

\* `--quick` testet falsche Baud zuerst — **nicht** direkt nach Strom-Reset verwenden.

### Make-Targets

```bash
make boot-wait    # Host-Boot
make host-reset   # Recovery
make autotest     # Profil-Sweep
make integration # HyBBX-Ready
make health       # Health-Check
make check        # Preflight
```

---

## Wichtige Host-Befehle (minicom)

| Befehl | Zweck |
|--------|-------|
| `kiss off` | Terminalmodus (vor INFO) |
| `INFO` | Firmware + Parameter |
| `HELP` | Kurzhilfe |
| `MYCALL TEST-0` | Kennung setzen |
| `RESTART` | Nach Parameteränderung |

In **KISS-Modus** (HyBBX aktiv): kein `cmd:`-Prompt — normal.

---

## HyBBX INI (Kern)

```ini
[transport.packet_radio1]
tnc = tnc2c
protocol = kiss
device = /dev/ttyS4
baud = 19200
serial_line = 8n1
rts_dtr = yes
modem = tcm3105
radio_baud = 2400
frequency_mhz = 27.235
radio_band = cb
```

Vollständig: `research/hybbx/production-ini-cb-ch24.ini`

---

## Weiterführend

- Betrieb & Troubleshooting: [TNC2C-OPERATIONS.md](TNC2C-OPERATIONS.md)
- Entwicklung/Roadmap: [../DEVELOPMENT.md](../DEVELOPMENT.md)
- Original-Handbuch: `TNC2C.pdf`
