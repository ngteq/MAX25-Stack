# HyBBX + Landolt TNC2C — Integration

Schritt-für-Schritt für **AX25SRV** mit bestätigtem TNC2C-Profil.

**Voraussetzung:** Host-Modus am TNC (Firmware-Banner) — siehe [TNC2C-OPERATIONS.md](TNC2C-OPERATIONS.md).

---

## Parameter (dieses Gerät)

| INI | Wert |
|-----|------|
| `device` | `/dev/ttyS4` |
| `baud` | `19200` |
| `serial_line` | `8n1` |
| `rts_dtr` | `yes` |
| `tnc` | `tnc2c` |
| `protocol` | `kiss` |
| `modem` | `tcm3105` |
| `radio_baud` | `2400` |
| `clock_mhz` | `4.9` |
| `frequency_mhz` | `27.235` |
| `radio_band` | `cb` |
| `radio_duplex` | `half` |

Fertige INI: `hybbx-tnc2c.ini` (lokal) oder `research/hybbx/production-ini-cb-ch24.ini`.

---

## Warum Boot vor HyBBX?

HyBBX öffnet `/dev/ttyS4` mit **RTS+DTR** und sendet sofort **`kiss on`**.  
Der TNC2C muss dafür im **Terminal-/Host-Modus** sein — nicht im Echo-Modus.

**Empfohlener Ablauf:**

1. HyBBX und minicom **stoppen**
2. **`./tnc2c-boot-wait.sh`** starten
3. TNC **Strom aus** → 10 s → **Strom an** → `OK: HOST`
4. Skript beenden (oder minicom nicht starten)
5. **Sofort** HyBBX starten — DTR bleibt durch HyBBX high

Alternative: TNC-Strom aus, HyBBX starten (assert DTR), TNC-Strom an — **weniger getestet** als boot-wait.

---

## Checkliste — Integration

### Vor dem Start

- [ ] `pkill minicom`; HyBBX gestoppt
- [ ] `fuser /dev/ttyS4` leer
- [ ] `./tnc2c-boot-wait.sh` → **OK: HOST**
- [ ] Optional: `./tnc2c-integration-test.sh` → HOST ok
- [ ] Funk: VOX **AUS**, Verkabelung DIN (oder noch abgeklemmt für KISS-only-Test)

### INI prüfen

```ini
[transport.packet_radio1]
enabled = yes
tnc = tnc2c
protocol = kiss
device_type = serial
device = /dev/ttyS4
baud = 19200
serial_line = 8n1
rts_dtr = yes
kiss_on_startup = yes
modem = tcm3105
radio_baud = 2400
clock_mhz = 4.9
radio_band = cb
radio_duplex = half
frequency_mhz = 27.235
txdelay = 50
persist = 128
slot = 10
```

**Wichtig:** `serial_line = 8n1` — HyBBX-Default für `tnc2c` ist 7E1, dieses Gerät braucht **8N1**.

### HyBBX starten

```bash
cd /home/akb/Code/hyBBX
./scripts/hybbx.sh    # oder euer Produktions-Start
```

### Log-Zeilen (erwartet)

```
[tnc] opened /dev/ttyS4 host=19200 8N1 rts_dtr=on ...
[tnc] KISS active (port 0)
```

Fehlerbilder:
- Kein KISS / IO-Fehler → TNC war im Echo-Modus → **boot-wait** wiederholen
- Port busy → minicom/HyBBX-Doppelstart

### Nach Start testen

- Telnet/Circuit verbinden (laut hybbx.ini)
- Kein ungewolltes PTT (LED2) ohne Sendebefehl
- Mit Funk + Dummyload: UI/Beacon testen

---

## Was HyBBX vom TNC erwartet

| Phase | HyBBX-Aktion | TNC-Antwort |
|-------|--------------|-------------|
| Open | Serial 19200 8N1, DTR+RTS on | — |
| Init | `kiss on` (wenn `kiss_on_startup=yes`) | KISS-Modus |
| Params | KISS-Parameter-Frames (TXDELAY, PERSIST, …) | — |
| RX/TX | KISS-Frames `0xC0 … 0xC0` | AX.25 über Modem |
| Shutdown | `kiss off` | Terminalmodus |

HyBBX sendet **kein** `kiss off` vor `kiss on` — deshalb muss der TNC bootfähig sein.

`kiss_entry` / `kiss_exit` in neueren HyBBX-Docs: für TNC2C reicht `kiss_on_startup = yes` (= `kiss on`).

---

## CB Kanal 24

- Funk manuell auf **Kanal 24** (27,235 MHz)
- `frequency_mhz = 27.235` in INI = Metadaten für HyBBX/HBX
- Halbduplex: `radio_duplex = half`

---

## Störquellen

| Problem | Lösung |
|---------|--------|
| Echo nach Tests | Strom-Reset + boot-wait |
| HyBBX + tnc2c-tools parallel | Nur eines darf `/dev/ttyS4` |
| 7E1 in INI | Auf `8n1` ändern |
| PTT zieht ungefragt | `kiss off` in minicom; HyBBX stoppen |
| baycom-stack aktiv | stoppen (Port-Konflikt) |

---

## Referenzen

- [TNC2C-OPERATIONS.md](TNC2C-OPERATIONS.md)
- [TNC2C-REFERENCE.md](TNC2C-REFERENCE.md)
- HyBBX: `/home/akb/Code/hyBBX/docs/TNCS.md`
- Produktions-INI: `research/hybbx/production-ini-cb-ch24.ini`
