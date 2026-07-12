# MAX25 Terminal

**The official MAX25 operator client** — text-based with an F10 menu. There is no second client; this UI concept stays unchanged for the foreseeable future.

Development and connection to `max25d`: **[MAX25-CLIENT.md](MAX25-CLIENT.md)** · Protocol: [`include/max25/protocol.md`](../include/max25/protocol.md)

Standalone client for direct modem interaction. HyBBX-compatible look and behaviour; configuration and hardware lifecycle stay in **`max25d`**.

## Binaries

| Binary | Symlink | Role |
|--------|---------|------|
| `max25d` | — | **Linux only** — config, plugins, boot-wait, BayCom, KISS/PTY, device owner |
| `max25-terminal` | `max25-client` | **v1 ready** — operator UI; connects to `max25d` on Linux |

The operator talks to the **modem** through the terminal; **`max25d` on Linux** owns hardware and BayCom.

## Platform split

| Where | What runs |
|-------|-----------|
| **Linux** | `max25d` + optional local `max25-terminal` |
| **Windows, macOS, *BSD, AmigaOS** | `max25-terminal` only → remote Linux `max25d` |

Transport: TCP to Linux host (default port **7325**), not raw serial on the client machine. Unix socket optional for local Linux terminal only (`/run/max25/modem.sock`).

**AmigaOS:** reduced text client in `stacks/terminal/amiga/` — TCP-only, no F10/ncurses menu parity.

## UI stability (long-term)

- Text-only (TTY / ncurses / ANSI fallback) — **no GUI, no web UI**
- **F10** menu, number keys **0–9** — no function-key navigation beyond F10
- HyBBX palette only (light gray on black)
- See [MAX25-CLIENT.md](MAX25-CLIENT.md#ui-contract-long-term-stable) for the binding contract

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
| TX | Lines → AX.25 UI frames (`CALLERID`→source, `CALLID`→dest); see [PACKET-RADIO.md](PACKET-RADIO.md) |
| RX | UI payload decode to display |

Traffic pacing and line width follow HyBBX `client_display` conventions.

## F10 menu

**`F10`** — open menu (overlay). **`F10`** or **`Esc`** — close, return to modem session.

Menu items are chosen with **number keys** `0`–`9`, not function keys.

```
┌─ MAX25 Terminal ────────────────────┐
│ CALLERID: CB-0    CALLID: QST       │
├─────────────────────────────────────┤
│ 1  Change CALLERID (live)           │
│ 2  Change CALLID (live)             │
│ 3  Status                           │
│ 4  Send line                        │
│ 5  RX only (Monitor)                │
│ 6  Connection on/off                │
│ 0  Quit client                      │
└─────────────────────────────────────┘
Pick a number · F10 closes
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

Validation: AX.25 address rules — 1–6 call characters, optional SSID `-0`…`-15` ([PACKET-RADIO.md](PACKET-RADIO.md)). Invalid input keeps the previous value.

Default persistence: **session only**. Optional “save to profile” may write `share/max25/*.ini` later.

## Architecture

```
Operator
   │
   ▼
max25-terminal (max25-client)
   │  F10 menu · CALLERID/CALLID · --ax25-ui
   │  TCP (remote) or unix socket (local Linux)
   ▼
max25d  (Linux host only)
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

In **hybbx-edge** operating mode: `max25d` prepares hardware; HyBBX attaches via `share/hybbx/*.ini.example`. MAX25 Terminal remains for local modem debug and live ID changes.

## Out of scope (terminal — long-term)

- Second client binary or alternative UI stack
- Raw serial/minicom-style setup in the client
- Multi-colour UI / themes / graphical frontends
- Function-key menu navigation (except F10 to toggle menu)

## See also

- [docs/README.md](README.md) — doc index
- [PACKET-RADIO.md](PACKET-RADIO.md) — AX.25 / KISS technical reference
- [MAX25-CLIENT.md](MAX25-CLIENT.md) — develop & connect the official client
- [ARCHITECTURE.md](ARCHITECTURE.md) — stack layers
- [HYBBX.md](HYBBX.md) — attach contract
- [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) — release scope
