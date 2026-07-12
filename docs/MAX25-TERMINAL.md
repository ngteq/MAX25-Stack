# MAX25 Terminal

Standalone client for direct modem interaction. HyBBX-compatible look and behaviour; configuration and hardware lifecycle stay in **`max25d`**.

## Binaries

| Binary | Symlink | Role |
|--------|---------|------|
| `max25d` | — | Daemon — config, plugins, boot-wait, KISS/PTY, device owner |
| `max25-terminal` | `max25-client` | Operator UI — modem channel only |

Operator talks to the **modem** through the terminal; everything else is **`max25d`**.

## Visual style (HyBBX-aligned)

- **Text-first**, ncurses when TTY allows
- **Palette:** black background, light gray text — same as HyBBX (`\033[37;40m`)
- No colour themes beyond light gray on black
- Fallback without ncurses: plain stdout + HyBBX ANSI palette

Derived from [hybbx-terminal](https://github.com/ngteq/hyBBX) (`src/clients/hybbx_terminal.c`, `include/hybbx/terminal.h`).

## AX.25 UI

Supports **`--ax25-ui`** (from hybbx-terminal):

| Direction | Behaviour |
|-----------|-----------|
| TX | Lines → AX.25 UI frames (uses live CALLERID / CALLID) |
| RX | TERMINAL and AX.25 UI decode to display |

Traffic pacing and line width follow HyBBX `client_display` conventions.

## F10 menu

**`F10`** — open menu (overlay). **`F10`** or **`Esc`** — close, return to modem session.

Menu points are chosen with **number keys** `0`–`9`, not function keys.

```
┌─ MAX25 Terminal ────────────────────┐
│ CALLERID: CB-0    CALLID: QST       │
├─────────────────────────────────────┤
│ 1  CALLERID ändern (live)           │
│ 2  CALLID ändern (live)             │
│ 3  Status                           │
│ 4  Zeile senden                     │
│ 5  Nur RX (Monitor)                 │
│ 6  Verbindung an/aus                │
│ 0  Client beenden                   │
└─────────────────────────────────────┘
Ziffer wählen · F10 schließt
```

### Live IDs

| Field | Meaning | AX.25 |
|-------|---------|-------|
| **CALLERID** | Own station ID | Source (`mycall`) |
| **CALLID** | Called station | Destination (`dest`) |

Changes apply **immediately** to the next transmit — no `max25d` restart.

1. Press **`1`** or **`2`**
2. Type new value in the prompt line
3. **`Enter`** — active; header line updates

Validation: AX.25 callsign rules (A–Z, 0–9, `-`; SSID optional). Invalid input keeps the previous value.

Default persistence: **session only**. Optional “save to profile” may write `share/max25/*.ini` later.

## Architecture

```
Operator
   │
   ▼
max25-terminal (max25-client)
   │  F10 menu · CALLERID/CALLID · --ax25-ui
   │  local socket (e.g. unix:///run/max25/modem.sock)
   ▼
max25d
   │  plugins · serial/KISS · config
   ▼
TNC / BayCom / CRDOP
```

`max25d` owns the serial port and device prep. The terminal never opens raw `/dev/tty*` in normal mode.

## Relation to HyBBX

| Component | HyBBX | MAX25 |
|-----------|-------|-------|
| Sessions / BBS | `hybbx` daemon | external consumer |
| Circuit client | `hybbx-terminal` → HBX :7323 | `max25-terminal` → `max25d` socket |
| Palette / text UI | `hybbx/terminal.h` | shared convention |
| Hardware prep | `packet_radio` plugin | `max25d` + stacks |

In **hybbx-edge** Betriebsform: `max25d` prepares hardware; HyBBX attaches via `share/hybbx/*.ini.example`. MAX25 Terminal remains for local modem debug and live ID changes.

## Out of scope (v1 terminal)

- Raw serial/minicom-style setup in the client
- Multi-colour UI
- Function-key menu navigation (except F10 to toggle menu)

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md) — stack layers
- [HYBBX.md](HYBBX.md) — attach contract
- [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) — current release scope (terminal planned post-v1.0.0)
