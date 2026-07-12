# TNC2C — Foren, Doku & Echo-vs-Host (Recherche)

> Interne Recherche. Konsolidiert in [CONFIRMED.md](CONFIRMED.md) und [../../docs/TNC2C-OPERATIONS.md](../../docs/TNC2C-OPERATIONS.md).

Stand: 2026-07-10

Symptome dieses Setups: minicom nach Strom-Reset mit **19200 8N1** → `kiss off` + `INFO` liefert NORD><LINK-2.7b-Banner; automatisierte Tests oft nur **Echo** (`INFO` → `INFO`); **CTS=0** am PC; Pin **4↔5** am TNC überbrückt; Quarz **4,9152 MHz**, TERM-Brücke auf **„4800“**.

---

## Kurzfazit

| Thema | Was Foren/Doku sagen |
|-------|----------------------|
| **Echo statt cmd:/INFO-Listing** | TNC nicht im **Terminal-/Kommandomodus** (KISS, Hostmode, Transparenz) oder PC-Timing stört Boot |
| **Strom-Reset nötig** | Mehrfach bestätigt: TF/FlexPacket brauchen **Terminalmodus** nach KISS/Host — sonst Init scheitert |
| **DTR absenken** | Handbuch: DTR/RTS für **Terminal-Erkennung**; DTR-Drop kann Zustand ändern — **nicht** direkt nach Power-On testen |
| **CTS=0 am PC** | Mit **Pin 4↔5 am TNC** oft normal; KISS/Linux: **`-crtscts`** setzen, Bridge reicht |
| **19200 + TERM „4800“** | Landolt **4,9-MHz-Werkvariante** + ggf. Mod: bei **9,8-MHz-Umbau** gilt **TERM „4800“ = 19200 PC-Baud** ([Landolt](https://www.landolt.de/info/afuinfo/tnc2c9_8mhz.htm)) |
| **7E1 vs 8N1** | Handbuch **7E1**; TF 2.7b/NORD><LINK oft **8N1** in der Praxis ([TF-Befehle](https://www.ralfzimmermann.de/tf26_2.html)) |

---

## 1. Echo-only vs echter Host/Terminalmodus

### TAPR / generisches TNC2-Wissen

- Doppeltes Echo (`cmd:RREESSEETT`): **Terminal und TNC** echoen — am TNC `ECHO OFF` ([TAPR TNC2 Manual](http://aprs.facile.free.fr/pdfs/TAPR%20TNC2%20rev2%20system%20manual1.1.8.txt)).
- **Transparent mode**: Zeichen werden **durchgereicht**, kein Kommandoparser — wirkt wie reines Echo ([Symek TNC2H](http://www.symek.com/pdf/tnc2hg.pdf)).
- **KISS mode**: Binärprotokoll; Terminalbefehle wie `INFO` werden nicht mehr normal beantwortet ([Xastir/Landolt TF](https://xastir.xastir.narkive.com/QjRgaQoX/with-tnc2-from-landolt), [packet-radio.net KISS-Skripte](https://packet-radio.net/category/software/)).

### The Firmware (NORD><LINK 2.7b)

- **ESC E 0/1** — Echo ein/aus ([TF 2.6 Befehlsliste](https://www.ralfzimmermann.de/tf26_2.html)).
- **ESC JHOST 0/1** — Terminal- vs **Hostmode** (für SP, FlexPacket, GP …) ([WA8DED Host Guide](https://www.ir3ip.net/iw3fqg/doc/wa8ded.htm)).
- Im **Hostmode** keine normalen Terminal-Prompts — Programme pollen mit **G**-Befehl.

**Relevanz:** Wenn nur der eingegebene Befehl zurückkommt, ist der TNC oft in **KISS**, **Hostmode** oder **Transparenz** — nicht im interaktiven Terminal. Nach Strom-Reset ist Terminalmodus kurz verfügbar (bei euch bestätigt).

---

## 2. Linux / PC — typische Forenfälle

### „TNC nicht im Terminalmodus“ (Funkbasis.de)

- [Thread: SP + DOSBox + TNC2](https://funkbasis.de/viewtopic.php?t=51330): Fehler **„Tnc nicht im Terminalmodus“** — **Gtkterm/Screen** funktionieren manuell, Emulatoren scheitern an **Synchronisation/Baud**.
- Tipp: **Native Linux-Tools** (linpac, kissattach, axlisten) statt DOS-Emu; **Baud innen/außen gleich** erzwingen.

### FlexPacket + TF2.7 (gettoweb.de)

- [FlexPacket für Linux](https://gettoweb.de/amateurfunk/flexpacket-fuer-linux/): Wenn TNC **nicht im Terminalmodus** → Initialisierung scheitert → **TNC neu starten** (Strom).
- Verweis auf [Spaß am TNC2](https://gettoweb.de/amateurfunk/spass-am-tnc2/) für Fern-Reset ohne physischer Reset.

### Spaß am TNC2 — konkrete Sequenzen

Quelle: [gettoweb.de/amateurfunk/spass-am-tnc2](https://gettoweb.de/amateurfunk/spass-am-tnc2/)

```bash
# KISS verlassen (KISS-Reset-Frame)
stty -F /dev/ttyS4 19200 cs8 -cstopb -crtscts
printf '\xc0\xff\xc0' > /dev/ttyS4

# Hostmode → Terminal (JHOST 0)
stty -F /dev/ttyS4 19200 cs8 -cstopb -crtscts
for i in $(seq 1 300); do printf '\x00'; done > /dev/ttyS4
printf '\x00\x01\x06JHOST 0\r' > /dev/ttyS4
```

**Parallele zu eurem Setup:** `kiss off` in minicom entspricht dem Verlassen von KISS; danach liefert `INFO` das Firmware-Banner.

### Mikrocontroller.net — TNC2 + Nord><LINK

- [Packet Radio mit TNC2](https://www.mikrocontroller.net/topic/420656): Firmware **NORD><LINK TF 2.7b**; **KISS-Mode** für Linux-Programme; TheNetNode für autonomen Betrieb.

### Linux KISS / Flow Control

- [complete.org — Serial TNCs in Linux](https://www.complete.org/serial-tncs-in-linux/): **XON/XOFF** und **RTS/CTS** stören KISS — `stty raw -ixon -ixoff -crtscts`.
- [TNC-X / Apple Linux Hinweis](http://www.tnc-x.com/apple.htm): KISS ohne Flow Control; ggf. **RTS↔CTS** überbrücken wenn Software RTS falsch hält.
- [BPQ32 RS232 Cabling](https://www.cantab.net/users/john.wiseman/Documents/BPQ32%20RS232%20Cabling.htm): Minimal-KISS-Kabel mit **RTS↔CTS**-Jumper am Stecker.
- [packet-radio.net — KPC3+ RTS/CTS](https://packet-radio.net/category/modems/page/3/): Ähnliches Problem — **Pin 4↔5 (DB25)** überbrücken wenn Stack RTS low zieht.

---

## 3. Handbuch Landolt TNC2C (lokal: `research/downloads/TNC2C.txt`)

- **7E1**, **RTS/CTS** — Handshake dient **Terminalabschaltung** (Erkennung ob PC da ist).
- **Pin 4 und 5 im Kabel überbrücken** — „um den TNC2C freizugeben“ (manche Rechner).
- **DTR/RTS** werden in der Praxis zusammen mit Terminal-Erkennung genutzt; reines TXD/RXD braucht **4,7 kΩ** am MAX232.

**CTS=0 am PC trotz TNC-Bridge:** Der PC liest **seine** CTS-Leitung; wenn das Mainboard **kein Loopback** auf CTS liefert, bleibt CTS=0 — **Datenverkehr kann trotzdem laufen**, solange Software **kein crtscts** erzwingt.

---

## 4. Quarz 4,9152 MHz + TERM „4800“ → 19200

| Quelle | Aussage |
|--------|---------|
| [Landolt TNC2C Katalog](https://www.landolt.de/info/afuinfo/tnc2c.htm) | Werkvarianten **4,9 MHz** und **9,8 MHz** |
| [Umbau 9,8 MHz](https://www.landolt.de/info/afuinfo/tnc2c9_8mhz.htm) | Nach 9,8-MHz-Mod: **TERM „4800“ = 19200 Baud**; von 4,9-Mod aus **verdoppeln sich** die Raten |
| [eBay/Platine](ebay-listing.md) | Sichtbar **4,9152 MHz**, TERM auf **4800** — passt zu **19200 am PC**, nicht zu 4800 Handbuch-Standard |

**Erklärung:** Silkscreen „4800“ bezieht sich auf die **Standard-Tabelle (9,8304 MHz)**. Mit **4,9-MHz-Variante** bzw. Modifikation ist die **effektive PC-Rate 19200** — genau euer Messwert.

---

## 5. Empfohlene Sequenz (konsolidiert aus Doku + eure Messung)

### Manuell (minicom) — Referenz

1. TNC **stromlos** 10–15 s
2. Netzteil an, **LED 4+5** blinken
3. **Sofort** minicom **19200 8N1** (nicht warten, nicht vorher autotesten)
4. Optional kurz warten, dann: `kiss off` → `INFO`
5. Firmware-Banner = **Terminalmodus OK**

### Automatisiert (Repo-Tools)

**Mit Strom-Reset (empfohlen):**

```bash
pkill minicom; sleep 1
./tnc2c-boot-wait.sh          # starten, dann TNC Strom aus/an
# oder: Strom aus → 10 s → an → innerhalb ~5 s:
./tnc2c-autotest.sh --host-check --write-env
```

**Ohne Strom-Reset (Recovery):** [`tnc2c-host-reset.sh`](../../tnc2c-host-reset.sh) — DTR+RTS, KISS-reset, `kiss off`, `INFO`.

**Nicht tun direkt nach Power-On:**

- `--quick` (falsche Baudraten zuerst)
- **DTR-Drop** (`boot_listen` / `--dtr-cycle`) — kann Terminal-Erkennung stören
- **Ctrl+C** / KISS-Frames vor `kiss off`

### Wenn wieder Echo-only (ohne Strom-Reset)

**Nicht** `printf … > /dev/ttyS4` — setzt **kein DTR/RTS**, TNC bleibt oft stumm oder im Echo.

Stattdessen:

```bash
./tnc2c-host-reset.sh              # DTR+RTS, KISS-reset, kiss off, INFO
./tnc2c-host-reset.sh --power-hint # mit Hinweis auf Strom-Reset
./tnc2c-host-reset.sh --no-kiss    # nur kiss off + INFO
make host-reset
```

Roh-Shell-Variante (nur wenn DTR anderweitig gesetzt ist) — siehe [Spaß am TNC2](https://gettoweb.de/amateurfunk/spass-am-tnc2/):

```bash
stty -F /dev/ttyS4 19200 cs8 -cstopb -crtscts raw -ixon -ixoff
printf '\xc0\xff\xc0' > /dev/ttyS4
sleep 1
printf 'kiss off\rINFO\r' > /dev/ttyS4
```

Oder Hostmode verlassen (siehe JHOST-0-Sequenz oben).

---

## 6. HyBBX / Produktion

```ini
device = /dev/ttyS4
baud = 19200
serial_line = 8n1
rts_dtr = yes
```

`rts_dtr = yes` hält DTR/RTS aktiv (Terminal „present“). Flow Control in Software **aus** (`crtscts` off), da KISS/Host das erwartet.

---

## Quellen (Links)

- [Landolt TNC2C Handbuch-Seite](https://www.landolt.de/info/afuinfo/tnc2c9k6.htm)
- [Landolt 9,8 MHz Umbau (Baud-Tabelle)](https://www.landolt.de/info/afuinfo/tnc2c9_8mhz.htm)
- [TF 2.6 Befehle (R. Zimmermann)](https://www.ralfzimmermann.de/tf26_2.html)
- [WA8DED Host Mode Guide](https://www.ir3ip.net/iw3fqg/doc/wa8ded.htm)
- [FlexPacket Linux (DC6AP)](https://gettoweb.de/amateurfunk/flexpacket-fuer-linux/)
- [Spaß am TNC2 — KISS/JHOST Reset](https://gettoweb.de/amateurfunk/spass-am-tnc2/)
- [Funkbasis: TNC2 Terminalmodus + Linux](https://funkbasis.de/viewtopic.php?t=51330)
- [Mikrocontroller.net: Packet Radio TNC2](https://www.mikrocontroller.net/topic/420656)
- [Serial TNCs in Linux (complete.org)](https://www.complete.org/serial-tncs-in-linux/)
- [BPQ32 RS232 / KISS Kabel](https://www.cantab.net/users/john.wiseman/Documents/BPQ32%20RS232%20Cabling.htm)
- [Xastir + Landolt TNC KISS](https://xastir.xastir.narkive.com/QjRgaQoX/with-tnc2-from-landolt)
