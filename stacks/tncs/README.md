# tnc2c

Werkzeuge und Betriebsdokumentation für **Packet Radio auf AX25SRV** — Landolt **TNC2C** (Unit A) und Stabo+**PK-TNC2** (Unit B, Lieferung).

**Dieses Gerät:** `/dev/ttyS4`, **19200 8N1**, Firmware NORD><LINK 2.7b, Modem TCM3105 2400 Baud.

## Schnellstart

```bash
cd /home/akb/Code/tnc2c

# 1. Host-Modus (DTR während Strom-Ein)
./tnc2c-boot-wait.sh
# → TNC-Strom AUS 10s → AN → OK: HOST

# 2. Prüfen (HyBBX-verify ist in boot-wait eingebaut — kein zweiter Befehl nötig)
# Optional ohne Strom-Zyklus (nur wenn Port noch offen/DTR high):
# ./tnc2c-integration-test.sh

# 3. HyBBX (wenn Host ok, Funk optional)
# siehe docs/TNC2C-OPERATIONS.md
```

**HyBBX und minicom müssen beendet sein**, bevor `tnc2c-*`-Tools laufen.

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [docs/TNC-INVENTORY.md](docs/TNC-INVENTORY.md) | **Beide TNCs** — Kurzübersicht |
| [docs/TNC2C-OPERATIONS.md](docs/TNC2C-OPERATIONS.md) | **Betrieb Unit A** |
| [docs/TNC2C-REFERENCE.md](docs/TNC2C-REFERENCE.md) | **Referenz:** Parameter, LEDs, Pinout, Tools |
| [docs/HYBBX-TNC2C.md](docs/HYBBX-TNC2C.md) | **HyBBX-Integration:** Boot, INI, Log-Zeilen |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Roadmap, TNC-Stack, offene Punkte |
| `tnc2c-serial.env` | Bestätigte Seriell-Parameter |

Interne Recherche (nicht für Veröffentlichung): `research/` — siehe [research/README.md](research/README.md).

## Tools (Kurz)

| Tool | Wann |
|------|------|
| `tnc2c-boot-wait.sh` | **TNC einschalten** — Host-Modus holen |
| `tnc2c-host-reset.sh` | Recovery ohne Strom-Reset |
| `tnc2c-autotest.sh --host-check` | Schnelltest 19200-8N1 |
| `tnc2c-health.sh` | Vollständiger Check (ohne TX) |
| `tnc2c-integration-test.sh` | **HyBBX-Ready-Check** (nach boot-wait) |
| `tnc2c-listen.sh` | Passiv lauschen (sicher) |

Vollständige Matrix: [docs/TNC2C-REFERENCE.md](docs/TNC2C-REFERENCE.md#tool-matrix).

## HyBBX

Snippet: `hybbx-tnc2c.ini` — Integration: [docs/HYBBX-TNC2C.md](docs/HYBBX-TNC2C.md).

## Sicherheit

`kiss on`, `--tx`, KISS-Frames können **PTT ziehen**. Nur mit Dummyload senden.
