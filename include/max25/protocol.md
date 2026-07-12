# M25/1 — MAX25 Terminal ↔ max25d protocol

**Version:** M25/1 (stable for `max25-terminal` / `max25-client`)

Line-oriented UTF-8 text. One command or response per line, terminated by `\n` (LF). Optional `\r` before `\n` is stripped by the daemon.

Developer guide: [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md)

---

## Transport

| Method | Default | Override |
|--------|---------|----------|
| TCP | `0.0.0.0:7325` | `max25d.ini` `[network]`, env `MAX25_HOST` / `MAX25_PORT` |
| Unix stream | `/run/max25/modem.sock` | `max25d.ini`, env `MAX25_UNIX`; without root use a writable path or TCP |

The official client tries Unix first (if configured), then TCP.

---

## Connection handshake

On connect, **the daemon sends first** (client must not send before reading).

### Without TCP auth (`tcp_password` empty)

```
OK
STATUS hardware=<hw> device=<selected> devices=<id1,id2,...> mode=<mode> callerid=<id> callid=<id> ax25_ui=on|off connected=yes|no stack=<state> serial=<state>
```

### With TCP auth (`[network] tcp_password` set — **TCP only**)

Unix socket clients skip auth (local trust).

```
AUTH required
AUTH <password>
OK
STATUS hardware=…
```

Client sends the password as a single line: `AUTH <password>` (plain text, v1).

Wrong or missing password → `ERR auth failed` and the connection closes.

| Client flag | Env |
|-------------|-----|
| `-P`, `--password` | `MAX25_TCP_PASSWORD` |

`<state>` for `stack=` is typically `running`, `stopped`, or `error`.

Implementations **must buffer** incomplete lines across `read()` calls.

---

## Client → daemon commands

| Command | Description |
|---------|-------------|
| `PING` | Keepalive |
| `GET STATUS` | Query state → `STATUS …` then `OK` |
| `GET DEVICES` | List enabled devices → one `DEVICE …` line each, then `OK` |
| `SET DEVICE <id>` | Select TX target device for this session (`SELECT DEVICE` alias) |
| `SET CALLERID <id>` | Live source callsign (uppercase) |
| `SET CALLID <id>` | Live destination callsign |
| `SET AX25_UI on\|off` | Toggle AX.25 UI framing for TX |
| `CONNECT` | Attach modem session on all enabled devices (required before `SEND`) |
| `DISCONNECT` | Detach session (daemon keeps running) |
| `SEND <text>` | Transmit line on session-selected device — payload is remainder of line after `SEND ` (may be empty) |
| `MONITOR on\|off` | RX-only mode (`SEND` → `ERR monitor-only`) |
| `BAN <callsign>` | Block AX.25 source — incoming UI frames dropped silently |
| `UNBAN <callsign>` | Remove source from ban list |
| `BANS` | List banned callsigns → one `BAN …` line each, then `OK` |

Command keywords are case-sensitive except `SET AX25_UI` flags (`on`/`off` case-insensitive).

### CALLSIGN rules

AX.25 address text (see [docs/PACKET-RADIO.md](../../docs/PACKET-RADIO.md)):

- Call body: **1–6** chars `A–Z` `0–9`
- SSID: optional `-0` … `-15`

Invalid `SET CALLERID` / `SET CALLID` → `ERR invalid CALLERID` / `ERR invalid CALLID`.

---

## Daemon → client responses

| Line | Meaning |
|------|---------|
| `OK` | Command succeeded |
| `ERR <message>` | Command failed |
| `STATUS hardware=… device=… devices=… mode=… callerid=… callid=… ax25_ui=… connected=… stack=… serial=…` | State snapshot |
| `DEVICE id=… hardware=… serial=… stack=… enabled=…` | One enabled device (`GET DEVICES`) |
| `RX device=<id> <text>` | Received traffic from `<id>` for display |
| `RX <text>` | Loopback TX echo (no serial) or legacy single-device |
| `EVENT connected` | Session attached (`CONNECT`) |
| `EVENT disconnected` | Session detached (`DISCONNECT`) |

### Multi-line command replies

| Command | Response sequence |
|---------|-------------------|
| `PING` | `OK` |
| `GET STATUS` | `STATUS …` → `OK` |
| `GET DEVICES` | `DEVICE …` (one per enabled id) → `OK` |
| `SET DEVICE <id>` / `SELECT DEVICE <id>` | `OK` or `ERR unknown device: …` |
| `SET CALLERID` / `SET CALLID` / `SET AX25_UI` / `MONITOR` | `OK` or `ERR …` |
| `CONNECT` | `EVENT connected` → `OK` |
| `DISCONNECT` | `EVENT disconnected` → `OK` |
| `SEND <text>` | `RX device=<id> <framed>` → `OK` (sender); other clients get `RX …` only |

With `ax25_ui=on`, framed text looks like: `[AX25 UI <callerid>><callid>] <payload>`.

### Errors

| Condition | Response |
|-----------|----------|
| Unknown command | `ERR unknown command: <word>` |
| `SEND` without `CONNECT` | `ERR not connected` |
| `SEND` in monitor mode | `ERR monitor-only` |
| Invalid UTF-8 line | `ERR invalid utf-8` |

---

## Session model

- `max25d` holds **global** `callerid`, `callid`, `ax25_ui` for all clients.
- `device=` in `STATUS` is the **session TX target** (default: `[devices] default=` or first enabled).
- `devices=` lists all enabled device ids (comma-separated).
- `connected` is per-daemon-session state (shared across clients in current implementation).
- `MONITOR` is per-daemon global flag in current implementation.
- Hardware lifecycle (`stack=running`) is owned by `max25d` per device, not the terminal.
- Each enabled device owns one serial port exclusively (one `KissBridge` each).

## Multi-device configuration

`max25d.ini` `[devices]` section (see `share/max25/max25d.ini.example`):

```ini
[devices]
default = tnc2c
tnc2c = /dev/ttyS4
pktnc2 = /dev/ttyS5
```

Legacy single-device configs (`[daemon] device=` + optional `[serial]`) remain valid.

Per-device serial overrides: `[serial.<id>]` sections (baud, line, dtr_rts, kiss_entry).

---

## Example session

```
← OK
← STATUS hardware=tncs device=tnc2c devices=tnc2c,pktnc2 mode=standalone callerid=CB-0 callid=QST ax25_ui=on connected=no stack=stopped
→ SET DEVICE tnc2c
← OK
→ CONNECT
← EVENT connected
← OK
→ SET CALLERID DG1ABC
← OK
→ SEND 73
← RX device=tnc2c [AX25 UI DG1ABC>QST] 73
← OK
→ GET STATUS
← STATUS hardware=tncs device=tnc2c devices=tnc2c,pktnc2 mode=standalone callerid=DG1ABC callid=QST ax25_ui=on connected=yes stack=stopped
← OK
→ DISCONNECT
← EVENT disconnected
← OK
```

(`→` client, `←` daemon)

---

## Reference code

| Component | Path |
|-----------|------|
| C client library | `stacks/terminal/max25_proto.c` |
| Terminal UI | `stacks/terminal/max25_terminal.c` |
| Daemon server | `stacks/daemon/max25d` |
| Offline smoke test | `stacks/daemon/test_proto.py` |
| Multi-device tests | `stacks/daemon/test_multi_device.py` |

---

## Stability

M25/1 is the long-term binding contract for **`max25-terminal` only**. New features should extend this protocol with documented, backward-compatible lines — not introduce a parallel client protocol.
