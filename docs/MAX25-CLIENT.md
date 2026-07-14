# MAX25 Client — Development & Connection to max25d

This document describes **how the official MAX25 terminal client** (`max25-terminal`, symlink `max25-client`) is developed, tested, and connected to **`max25d`**.

## The one official client

MAX25 has **exactly one** operator client:

| Binary | Symlink | Status |
|--------|---------|--------|
| `max25-terminal` | `max25-client` | **v1 ready** — mainstream OS + AmigaOS (reduced) |

There is **no second official operator client** from the MAX25 core — `max25-terminal` stays text-only. **Third-party GUI clients are welcome** (see below). For the foreseeable future the official client stays:

- **text-only** (TTY / ncurses / ANSI fallback)
- **F10 menu** with number keys `0`–`9`
- **live CALLERID / CALLID**
- optional **`--ax25-ui`**
- optional **TCP auth** (`-P` / `MAX25_TCP_PASSWORD`)

A **browser terminal** (WebSocket → M25/1) is **DEV-Level 3** (*ca.*) — scaffold in `stacks/web/`; see [WEBSOCKET.md](WEBSOCKET.md). It will **not** replace `max25-terminal` for operator sessions.

All client changes to the **official** program go into **this one binary** in `stacks/terminal/`. The M25/1 protocol to `max25d` is the stable binding contract.

### Third-party and GUI clients (welcome)

MAX25 does **not** plan an official Qt/GTK/windowing operator client. **Third-party GUI clients are explicitly welcome** — implement any graphical or rich UI against [M25/1](../include/max25/protocol.md) (TCP `:7325`, Unix socket, optional `tcp_password` auth).

| Client type | Maintainer | Status |
|-------------|------------|--------|
| `max25-terminal` | MAX25 core | Official — text + F10 |
| GUI / desktop / mobile | **Third-party developers** | **Encouraged** — protocol-bound |
| Browser (WebSocket) | MAX25 (`stacks/web/`) | **DEV-Level 3** (*ca.*) |

Contributors may add example client profiles under `share/clients/` (YAML schema v1). Do not bypass `max25d` to touch serial, KISS PTY, or sound hardware directly.

Operator documentation (usage, menu): [MAX25-TERMINAL.md](MAX25-TERMINAL.md).

---

## Role split

```
Operator
   │
   ▼
max25-terminal / max25-client     ← UI, input, display (all platforms)
   │  M25/1 (TCP or Unix)
   ▼
max25d                            ← config, plugins, hardware (Linux only)
   │
   ▼
TNC / BayCom / CRDOP
```

| Responsibility | `max25-terminal` | `max25d` |
|----------------|------------------|----------|
| Serial / KISS / kernel modem | **no** | **yes** |
| Plugin lifecycle (boot-wait, BayCom, crdopc) | **no** | **yes** |
| Operator input & RX display | **yes** | **no** |
| CALLERID / CALLID (live, session) | sends `SET …` | stores & uses for TX |
| AX.25 UI mode | `--ax25-ui` → `SET AX25_UI` | formats/forwards TX |
| INI configuration | connection target only (host/port/password) | `max25d.ini` |

The client **never** opens `/dev/tty*` or sound cards directly. All modem-related work goes through `max25d`.

---

## Transport & connection setup

### Endpoints (defaults)

| Transport | Address | When |
|-----------|---------|------|
| **TCP** | `Host:7325` | Remote (Windows, macOS, *BSD, Linux, AmigaOS) |
| **Unix** | `/run/max25/modem.sock` | Local Linux terminal (preferred when available) |

Without root, `/run/max25/modem.sock` may be unavailable — set `MAX25_UNIX` to a writable path or connect via TCP **7325**.

### Environment variables

| Variable | Meaning | Default |
|----------|---------|---------|
| `MAX25_HOST` | TCP target host | `127.0.0.1` |
| `MAX25_PORT` | TCP port | `7325` |
| `MAX25_UNIX` | Unix socket path | `/run/max25/modem.sock` |
| `MAX25_TCP_PASSWORD` | Plain-text TCP auth password | (empty) |

### CLI (reference implementation)

```bash
max25-terminal -H 192.168.1.10 -p 7325
max25-terminal -T -H linux-host.local -p 7325 -P changeme
max25-terminal -U /run/max25/modem.sock
max25-terminal --ax25-ui -v
max25-terminal --probe -T -H 127.0.0.1 -p 7325
```

**Connection order:** try Unix socket first (unless `--tcp-only` / `-T`), then TCP.

### Handshake on connect

When `tcp_password` is set, **TCP clients** receive `AUTH required` first; Unix socket clients skip auth.

Without auth:

```
OK
STATUS hardware=tncs device=tnc2c mode=standalone callerid=CB-0 callid=QST ax25_ui=on connected=no stack=running
```

With TCP auth:

```
AUTH required
AUTH <password>
OK
STATUS hardware=…
```

The client must:

1. read handshake lines with a **line buffer** (multiple `\n` may arrive in one `read()`)
2. parse `STATUS` and update the header line
3. optionally send `CONNECT` before `SEND` is allowed

Full reference: [`include/max25/protocol.md`](../include/max25/protocol.md).

---

## M25/1 protocol

Short overview: **line-oriented UTF-8**, one command per line, terminated with `\n`. No JSON, no binary framing.

### Client → daemon

| Command | Effect |
|---------|--------|
| `PING` | Keepalive → `OK` |
| `GET STATUS` | → `STATUS …` then `OK` |
| `SET CALLERID <id>` | Live source callsign (uppercase) |
| `SET CALLID <id>` | Live destination callsign |
| `SET AX25_UI on\|off` | AX.25 UI mode |
| `SET DEVICE <id>` | Select TX target (`SELECT DEVICE` alias) |
| `GET DEVICES` | List enabled devices |
| `CONNECT` | Attach session → `EVENT connected`, `OK` |
| `DISCONNECT` | Detach session → `EVENT disconnected`, `OK` |
| `SEND <text>` | Send line (remainder of line after `SEND `) |
| `MONITOR on\|off` | RX only (no `SEND`) |

### Daemon → client

| Line | Meaning |
|------|---------|
| `OK` | Command succeeded |
| `ERR <msg>` | Command rejected |
| `STATUS hardware=… device=… devices=… mode=… callerid=… callid=… ax25_ui=on\|off connected=yes\|no stack=…` | State snapshot |
| `DEVICE id=… serial=… stack=… enabled=…` | One device (`GET DEVICES`) |
| `RX device=<id> <text>` | Received line from device `<id>` |
| `RX <text>` | Loopback TX echo (no serial) |
| `EVENT connected` / `EVENT disconnected` | Session events |

### Typical dialogues

**Query status:**

```
C: GET STATUS
D: STATUS hardware=tncs device=tnc2c mode=standalone callerid=CB-0 callid=QST ax25_ui=on connected=yes stack=running
D: OK
```

**Change live ID:**

```
C: SET CALLERID DG1ABC
D: OK
```

**Send (after CONNECT):**

```
C: SEND 73 to all
D: RX [AX25 UI DG1ABC>QST] 73 to all    ← echo to sending client
D: OK
```

Other connected clients receive the same `RX` line.

**Error:**

```
C: SEND test
D: ERR not connected
```

### CALLSIGN validation

Matches AX.25 address rules (see [PACKET-RADIO.md](PACKET-RADIO.md)):

- Call body: **1–6** characters `A–Z`, `0–9`
- Optional SSID: **`-0` … `-15`**
- Input is normalized to **uppercase**

Invalid `SET CALLERID` / `SET CALLID` → `ERR invalid CALLERID` / `ERR invalid CALLID`; previous value is kept.

### Implementation notes (important)

1. **Line buffer:** Never assume one `read()` equals one protocol line. Reference: `LineReader` in `stacks/daemon/test_proto.py`, byte-by-byte read in `stacks/terminal/max25_proto.c`.

2. **One reader per socket:** Either one event loop reads all lines, or synchronous `command()` calls — **do not** read from the same FD in two places in parallel.

3. **`RX` during `command()`:** `max25_client_command()` ignores interim `RX …` and `EVENT …` lines until `OK`/`ERR`.

4. **`SEND` order:** Daemon responds to `SEND` with `RX …` **before** `OK`. Tests and clients must expect both lines.

5. **`connected` is session state:** Without `CONNECT`, `SEND` fails. The reference client calls `CONNECT` automatically on start.

---

## Source layout (`stacks/terminal/`)

| File | Role |
|------|------|
| `max25_terminal.c` | `main`, CLI, session loop, menu actions |
| `max25_proto.c` / `.h` | Socket connect, M25/1 commands, STATUS parser, TCP auth |
| `max25_ui.c` / `.h` | ncurses menu, HyBBX palette, prompts |
| `amiga/` | Reduced AmigaOS TCP client (no ncurses menu) |
| `Makefile` | Build, `max25-client` symlink |

### Reference API (`max25_proto.h`)

```c
int max25_client_connect(const char *host, unsigned port, const char *unix_path,
                         int tcp_only, const char *tcp_password,
                         max25_client_t **out, max25_status_t *initial_status);
int max25_client_command(max25_client_t *client, const char *cmd,
                         char *reply, size_t reply_sz);
int max25_client_read_line(max25_client_t *client, char *line, size_t line_sz);
int max25_client_parse_status(const char *line, max25_status_t *status);
int max25_valid_callsign(const char *value);
```

Session loop in `max25_terminal.c`:

- `poll()` on STDIN + daemon socket
- daemon lines: `RX …` → display
- TTY: type lines → `SEND …`
- **F10** → toggle menu (ncurses: `KEY_F(10)`)

---

## UI contract (long-term stable)

These rules do **not** change for the foreseeable future:

| Element | Rule |
|---------|------|
| Display | Text only — ncurses when TTY, otherwise ANSI/plain stdout |
| Palette | Black + light gray (`\033[37;40m`) — HyBBX-aligned |
| Menu key | **F10** opens/closes |
| Menu selection | **Digits 0–9**, no other function keys |
| Header | `MAX25 Terminal  CALLERID: …  CALLID: …` |
| Menu entries | see [MAX25-TERMINAL.md](MAX25-TERMINAL.md#f10-menu) |
| Color themes / GUI in **official** client | **out of scope** — use third-party GUI via M25/1 |
| Official web terminal | [WEBSOCKET.md](WEBSOCKET.md) — in development |
| Raw serial in client | **forbidden** |

Menu contents and numbers are part of the product — new features belong in the existing F10 menu, not in parallel UIs.

---

## Development workflow

### Build

```bash
./scripts/build.sh
# Produces: build/bin/max25-terminal
# Symlink: build/bin/max25-client -> max25-terminal (after cmake --install)
```

Linux dependency: `libncurses-dev` (or ncurses via pkg-config).

AmigaOS cross-build:

```bash
make amiga-terminal
# or: scripts/build-amiga-terminal.sh  (SDK: /opt/amiga)
```

### Start daemon for tests

```bash
# Without hardware (protocol only):
./stacks/daemon/max25d --no-stack -c share/max25/max25d.ini.example

# With stack auto-start:
./stacks/daemon/max25d -c share/max25/max25d.ini.example
```

### Connect terminal

```bash
./stacks/terminal/max25-terminal -H 127.0.0.1 -p 7325 --ax25-ui -v
./stacks/terminal/max25-terminal -T -H 127.0.0.1 -p 7325 -P changeme --probe
```

### Automated protocol tests

```bash
python3 stacks/daemon/test_proto.py && python3 stacks/daemon/test_auth.py
bash stacks/terminal/test-terminal.sh
./scripts/release-check.sh             # full gates including both stacks
```

### Manual protocol test (e.g. with netcat)

```bash
nc 127.0.0.1 7325
# OK and STATUS arrive automatically (or AUTH required if tcp_password set)
GET STATUS
SET CALLERID CB-0
CONNECT
SEND Hello
DISCONNECT
```

---

## Checklist for client developers

Before merge / release of the terminal:

- [ ] Handshake: `OK` + `STATUS` (or `AUTH` flow) read with correct buffering
- [ ] `CONNECT` before first `SEND`
- [ ] `SET CALLERID` / `SET CALLID` with validation; header updated live
- [ ] F10 menu: entries 0–6 as specified
- [ ] `RX` lines displayed; `poll`/event loop does not block
- [ ] Remote TCP and local Unix socket tested
- [ ] TCP auth tested when `tcp_password` is set
- [ ] `--ax25-ui` sets `SET AX25_UI on` on the daemon
- [ ] No direct hardware access in the client
- [ ] `./scripts/release-check.sh` green

---

## What not to build (official client)

| Not wanted in **core** | Instead |
|------------------------|---------|
| Second **official** text client | extend `max25-terminal` |
| Official Qt/GTK windowing GUI | **third-party** GUI via M25/1 (welcome) |
| Own serial/KISS in any client | `max25d` + M25/1 |
| Parallel protocol | M25/1 only — document extensions with version |
| Function-key menu (F1–F9) | digit keys in F10 menu |

---

## Daemon side (connection from max25d’s view)

`max25d` (`stacks/daemon/max25d`) implements the server:

- listens on TCP (`max25d.ini` → `[network] tcp_port`) and optional Unix
- one thread per client (`client_thread`)
- shared `DaemonState` (CALLERID/CALLID global for all clients)
- one device backend per enabled `[devices]` id on each Linux host (target: **one** id): `kiss-serial`, `baycom-kiss`, `kiss-raw-serial`, `crdop-tcp`
- plain-text TCP auth when `tcp_password` is set

Configuration: `share/max25/max25d.ini.example`, systemd: `share/max25/max25d.service.example`.

**Host layout:** Main + optional Secondaries — [ARCHITECTURE.md](ARCHITECTURE.md#host-layout--main--secondaries). Configure `[devices]` per `max25d` instance. M25/1 `SET DEVICE`, `GET DEVICES`, and `RX device=<id> …` remain valid for session routing.

**Note:** Hardware TX/RX bridge (KISS/serial) is server-side; the client contract (`SEND` / `RX`) stays stable.

Planned daemon extensions (do **not** change the text UI contract):

- real modem RX lines as `RX …` instead of loopback echo (KISS bridge matures)

**HyBBX:** Plugin lifecycle stays in HyBBX — `max25d` does not load HyBBX plugins.

---

## See also

- [PACKET-RADIO.md](PACKET-RADIO.md) — AX.25 / KISS / TNC / BayCom
- [MAX25-TERMINAL.md](MAX25-TERMINAL.md) — operator view, menu, usage
- [include/max25/protocol.md](../include/max25/protocol.md) — M25/1 protocol reference
- [PLATFORMS.md](PLATFORMS.md) — Linux-only daemon, cross-platform client
- [ARCHITECTURE.md](ARCHITECTURE.md) — layer model
- [DEVELOPMENT.md](DEVELOPMENT.md) — toolchain & repo conventions
