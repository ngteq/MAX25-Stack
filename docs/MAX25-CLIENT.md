# MAX25 Client — Entwicklung & Anbindung an max25d

Dieses Dokument beschreibt, **wie der offizielle MAX25-Terminal-Client** (`max25-terminal`, Symlink `max25-client`) entwickelt, getestet und an **`max25d`** angebunden wird.

## Der eine offizielle Client

MAX25 hat **genau einen** Operator-Client:

| Binary | Symlink | Status |
|--------|---------|--------|
| `max25-terminal` | `max25-client` | **v1 ready** (Linux/*BSD/macOS/Windows) |

Es ist **kein zweiter Client** vorgesehen — weder GUI, noch Web, noch ein alternatives TTY-Programm. Der Client bleibt auf absehbare Zeit:

- **rein textbasiert** (TTY / ncurses / ANSI-Fallback)
- **F10-Menü** mit Zifferntasten `0`–`9`
- **live CALLERID / CALLID**
- optional **`--ax25-ui`**

Änderungen am Client betreffen **dieses eine Programm** in `stacks/terminal/`. Das M25/1-Protokoll zu `max25d` ist der stabile Anbindungsvertrag.

Operator-Dokumentation (Bedienung, Menü): [MAX25-TERMINAL.md](MAX25-TERMINAL.md).

---

## Rollenverteilung

```
Operator
   │
   ▼
max25-terminal / max25-client     ← UI, Eingabe, Anzeige (alle Plattformen)
   │  M25/1 (TCP oder Unix)
   ▼
max25d                            ← Config, Plugins, Hardware (nur Linux)
   │
   ▼
TNC / BayCom / CRDOP
```

| Verantwortung | `max25-terminal` | `max25d` |
|---------------|------------------|----------|
| Seriellport / KISS / Kernel-Modem | **nein** | **ja** |
| Plugin-Lifecycle (boot-wait, BayCom, crdopc) | **nein** | **ja** |
| Operator-Eingabe & RX-Anzeige | **ja** | **nein** |
| CALLERID / CALLID (live, Session) | sendet `SET …` | speichert & nutzt für TX |
| AX.25-UI-Modus | `--ax25-ui` → `SET AX25_UI` | formatiert/weiterleitet TX |
| Konfiguration INI | nur Verbindungsziel (Host/Port) | `max25d.ini` |

Der Client **öffnet niemals** `/dev/tty*` oder Soundkarten direkt. Alles Modem-bezogene läuft über `max25d`.

---

## Transport & Verbindungsaufbau

### Endpunkte (Standard)

| Transport | Adresse | Wann |
|-----------|---------|------|
| **TCP** | `Host:7325` | Remote (Windows, macOS, *BSD, Linux) |
| **Unix** | `/run/max25/modem.sock` | Lokaler Linux-Terminal (bevorzugt, wenn vorhanden) |

Ohne root-Rechte fällt `max25d` auf `/tmp/max25/modem.sock` zurück.

### Umgebungsvariablen

| Variable | Bedeutung | Default |
|----------|-----------|---------|
| `MAX25_HOST` | TCP-Zielhost | `127.0.0.1` |
| `MAX25_PORT` | TCP-Port | `7325` |
| `MAX25_UNIX` | Unix-Socket-Pfad | `/run/max25/modem.sock` |

### CLI (Referenzimplementierung)

```bash
max25-terminal -H 192.168.1.10 -p 7325
max25-terminal -U /run/max25/modem.sock
max25-terminal --ax25-ui -v
```

**Verbindungsreihenfolge:** zuerst Unix-Socket versuchen (wenn `-U` gesetzt), sonst TCP.

### Handshake beim Connect

Nach `accept()` sendet `max25d` **ohne Client-Anfrage** zwei Zeilen:

```
OK
STATUS hardware=tncs device=tnc2c mode=standalone callerid=CB-0 callid=QST ax25_ui=on connected=no stack=running
```

Der Client muss:

1. beide Zeilen lesen (mit **Zeilenpuffer** — mehrere `\n` können in einem `read()` ankommen)
2. `STATUS` parsen und Header-Zeile aktualisieren
3. optional `CONNECT` senden, bevor `SEND` erlaubt ist

---

## M25/1-Protokoll

Vollständige Referenz: [`include/max25/protocol.md`](../include/max25/protocol.md).

Kurzüberblick: **zeilenorientiertes UTF-8**, eine Anweisung pro Zeile, mit `\n` abgeschlossen. Kein JSON, kein Binary-Framing.

### Client → Daemon

| Befehl | Wirkung |
|--------|---------|
| `PING` | Keepalive → `OK` |
| `GET STATUS` | → `STATUS …` dann `OK` |
| `SET CALLERID <id>` | Live-Quellrufzeichen (uppercase) |
| `SET CALLID <id>` | Live-Zielrufzeichen |
| `SET AX25_UI on\|off` | AX.25-UI-Modus |
| `CONNECT` | Session an → `EVENT connected`, `OK` |
| `DISCONNECT` | Session aus → `EVENT disconnected`, `OK` |
| `SEND <text>` | Zeile senden (Rest der Zeile nach `SEND `) |
| `MONITOR on\|off` | Nur RX (kein `SEND`) |

### Daemon → Client

| Zeile | Bedeutung |
|-------|-----------|
| `OK` | Befehl erfolgreich |
| `ERR <msg>` | Fehler (Befehl abgelehnt) |
| `STATUS hardware=… device=… mode=… callerid=… callid=… ax25_ui=on\|off connected=yes\|no stack=…` | Zustand |
| `RX <text>` | Empfangene Zeile zur Anzeige |
| `EVENT connected` / `EVENT disconnected` | Session-Events |

### Typische Dialoge

**Status abfragen:**

```
C: GET STATUS
D: STATUS hardware=tncs device=tnc2c mode=standalone callerid=CB-0 callid=QST ax25_ui=on connected=yes stack=running
D: OK
```

**Live-ID ändern:**

```
C: SET CALLERID DG1ABC
D: OK
```

**Senden (nach CONNECT):**

```
C: SEND 73 an alle
D: RX [AX25 UI DG1ABC>QST] 73 an alle    ← Echo an sendenden Client
D: OK
```

Andere verbundene Clients erhalten dieselbe `RX`-Zeile (ohne doppeltes Echo beim Sender).

**Fehler:**

```
C: SEND test
D: ERR not connected
```

### CALLSIGN-Validierung

Entspricht AX.25-Adressregeln (siehe [PACKET-RADIO.md](PACKET-RADIO.md)):

- Rufzeichen-Körper: **1–6** Zeichen `A–Z`, `0–9`
- SSID optional: **`-0` … `-15`**
- Eingabe wird **uppercase** normalisiert

Ungültige `SET CALLERID` / `SET CALLID` → `ERR invalid CALLERID` bzw. `ERR invalid CALLID`; alter Wert bleibt.

### Implementierungshinweise (wichtig)

1. **Zeilenpuffer:** Niemals ein `read()` = eine Protokollzeile annehmen. Referenz: `LineReader` in `stacks/daemon/test_proto.py`, Byte-für-Byte-Lesen in `stacks/terminal/max25_proto.c`.

2. **Ein Leser pro Socket:** Entweder ein Event-Loop liest alle Zeilen, oder synchrone `command()`-Aufrufe — **nicht** parallel zwei Stellen auf demselben FD lesen.

3. **`RX` während `command()`:** `max25_client_command()` ignoriert Zwischenzeilen `RX …` und `EVENT …` bis `OK`/`ERR` kommt.

4. **`SEND`-Reihenfolge:** Daemon antwortet auf `SEND` mit `RX …` **vor** `OK`. Tests und Client müssen beide Zeilen erwarten.

5. **`connected` ist Session-State:** Ohne `CONNECT` schlägt `SEND` fehl. Referenz-Client ruft `CONNECT` beim Start automatisch auf.

---

## Quellcode-Layout (`stacks/terminal/`)

| Datei | Aufgabe |
|-------|---------|
| `max25_terminal.c` | `main`, CLI, Session-Loop, Menü-Aktionen |
| `max25_proto.c` / `.h` | Socket-Connect, M25/1-Befehle, STATUS-Parser |
| `max25_ui.c` / `.h` | ncurses-Menü, HyBBX-Palette, Prompts |
| `Makefile` | Build, `max25-client`-Symlink |

### Referenz-API (`max25_proto.h`)

```c
int max25_client_connect(const char *host, unsigned port, const char *unix_path,
                         max25_client_t **out);
int max25_client_command(max25_client_t *client, const char *cmd,
                         char *reply, size_t reply_sz);
int max25_client_read_line(max25_client_t *client, char *line, size_t line_sz);
int max25_client_parse_status(const char *line, max25_status_t *status);
int max25_valid_callsign(const char *value);
```

Session-Loop in `max25_terminal.c`:

- `poll()` auf STDIN + Daemon-Socket
- Daemon-Zeilen: `RX …` → Anzeige
- TTY: Zeilen eingeben → `SEND …`
- **F10** → Menü ein/aus (ncurses: `KEY_F(10)`)

---

## UI-Vertrag (langfristig stabil)

Diese Vorgaben ändern sich **nicht** auf absehbare Zeit:

| Element | Vorgabe |
|---------|---------|
| Darstellung | Text only — ncurses wenn TTY, sonst ANSI/plain stdout |
| Palette | Schwarz + hellgrau (`\033[37;40m`) — HyBBX-konform |
| Menü-Taste | **F10** öffnet/schließt |
| Menü-Auswahl | **Ziffern 0–9**, keine weiteren Funktionstasten |
| Header | `MAX25 Terminal  CALLERID: …  CALLID: …` |
| Menüeinträge | siehe [MAX25-TERMINAL.md](MAX25-TERMINAL.md#f10-menu) |
| Farb-Themes / GUI / Web | **out of scope** |
| Raw-Serial im Client | **verboten** |

Menü-Inhalte und Nummern sind Teil des Produkts — neue Features gehören ins bestehende F10-Menü, nicht in parallele UIs.

---

## Entwicklungsworkflow

### Bauen

```bash
make -C stacks/terminal all
# Erzeugt: stacks/terminal/max25-terminal
# Symlink: stacks/terminal/max25-client -> max25-terminal
```

Abhängigkeit Linux: `libncurses-dev` (oder ncurses via pkg-config).

### Daemon für Tests starten

```bash
# Ohne Hardware (nur Protokoll):
./stacks/daemon/max25d --no-stack -c share/max25/max25d.ini.example

# Mit Stack-Auto-Start:
./stacks/daemon/max25d -c share/max25/max25d.ini.example
```

### Terminal anbinden

```bash
./stacks/terminal/max25-terminal -H 127.0.0.1 -p 7325 --ax25-ui -v
```

### Automatische Protokoll-Tests

```bash
make -C stacks/daemon smoke    # test_proto.py — M25/1 ohne Terminal-UI
make -C stacks/terminal test   # Binary + Symlink vorhanden
make release-check             # Gesamt-Gates inkl. beider Stacks
```

### Manueller Protokoll-Test (z. B. mit netcat)

```bash
nc 127.0.0.1 7325
# OK und STATUS kommen automatisch
GET STATUS
SET CALLERID CB-0
CONNECT
SEND Hello
DISCONNECT
```

---

## Checkliste für Client-Entwickler

Vor Merge / Release des Terminals:

- [ ] Handshake: `OK` + `STATUS` nach Connect korrekt gepuffert gelesen
- [ ] `CONNECT` vor erstem `SEND`
- [ ] `SET CALLERID` / `SET CALLID` mit Validierung; Header live aktualisiert
- [ ] F10-Menü: Einträge 0–6 wie spezifiziert
- [ ] `RX`-Zeilen werden angezeigt; `poll`/Event-Loop blockiert nicht
- [ ] Remote-TCP und lokaler Unix-Socket getestet
- [ ] `--ax25-ui` setzt `SET AX25_UI on` am Daemon
- [ ] Kein direkter Hardware-Zugriff im Client
- [ ] `make release-check` grün

---

## Was nicht zu bauen ist

| Nicht gewünscht | Stattdessen |
|-----------------|-------------|
| Zweiter Client (GUI, Web, minicom-Fork) | `max25-terminal` erweitern |
| Eigenes Serial/KISS im Client | `max25d` + M25/1 |
| Paralleles Protokoll | Nur M25/1 — Erweiterungen versioniert dokumentieren |
| Funktionstasten-Menü (F1–F9) | Zifferntasten im F10-Menü |

---

## Daemon-Seite (Anbindung aus Sicht max25d)

`max25d` (`stacks/daemon/max25d`) implementiert den Server:

- lauscht TCP (`max25d.ini` → `[network] tcp_port`) und optional Unix
- ein Thread pro Client (`client_thread`)
- gemeinsamer `DaemonState` (CALLERID/CALLID global für alle Clients)

Konfiguration: `share/max25/max25d.ini.example`, systemd: `share/max25/max25d.service.example`.

**Hinweis:** Hardware-TX/RX-Brücke (KISS/Serial) wird serverseitig ausgebaut; der Client-Vertrag (`SEND` / `RX`) bleibt dabei stabil.

Geplante Daemon-Erweiterungen (ändern **nicht** den Text-UI-Vertrag):

- ~~Authentifizierung für Remote-TCP~~ — **v1:** plain-text `AUTH` auf TCP (`tcp_password` in `max25d.ini`)
- echte Modem-RX-Zeilen als `RX …` statt Loopback-Echo

**HyBBX:** Plugin-Lifecycle bleibt in HyBBX selbst — `max25d` braucht keinen HyBBX-Plugin-Loader; MAX25 nutzt `max25-ctl` + eigene Plugin-YAMLs nur als Dokumentation/Manifest.

---

## Siehe auch

- [PACKET-RADIO.md](PACKET-RADIO.md) — AX.25 / KISS / TNC / BayCom
- [MAX25-TERMINAL.md](MAX25-TERMINAL.md) — Operator-Ansicht, Menü, Bedienung
- [PACKET-RADIO.md](PACKET-RADIO.md) — AX.25, KISS, TNC, BayCom
- [include/max25/protocol.md](../include/max25/protocol.md) — M25/1-Protokollreferenz
- [PLATFORMS.md](PLATFORMS.md) — Linux-only Daemon, Client cross-platform
- [ARCHITECTURE.md](ARCHITECTURE.md) — Schichtenmodell
- [DEVELOPMENT.md](DEVELOPMENT.md) — Toolchain & Repo-Konventionen
