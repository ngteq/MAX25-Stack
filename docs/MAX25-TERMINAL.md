# MAX25 Terminal

**The official MAX25 operator client** for live packet-radio sessions — text-based with an F10 menu. Operators and integrators connect through **`max25-terminal`** (symlink **`max25-client`**) to exchange traffic with modems via **`max25d`**. This is the only supported **session client** for TX/RX, monitor mode, and live CALLERID/CALLID changes.

**UI roadmap (for third-party planning):**

| Surface | Purpose | Status |
|---------|---------|--------|
| **`max25-terminal`** | Operator session — connect, send, monitor, F10 menu | **Current** — text-only; **no graphical UI planned for a long time** |
| **Web UI** | Browser-based stack administration and monitoring (alongside `max25d`) | **DEV-Level 3** (*ca.*); WebSocket scaffold only |

**WebSocket browser terminal:** scaffold in `stacks/web/` — **DEV-Level 3** (*ca.*, after TCP/IP + platform base). Design: [WEBSOCKET.md](WEBSOCKET.md). **Not production-ready in v1.0.0.**

Third parties may build their own M25/1 clients against [`include/max25/protocol.md`](../include/max25/protocol.md). Only `max25-terminal` is maintained as the official operator UI.

**GUI clients from developers are welcome and encouraged.** Qt, GTK, native desktop, mobile, or custom graphical frontends that speak M25/1 to `max25d` are a supported integration path. The core project does not ship a windowing operator GUI; third parties fill that role. Publish against `include/max25/protocol.md` and optional client profiles under `share/clients/`.

Development and connection to `max25d`: **[MAX25-CLIENT.md](MAX25-CLIENT.md)** · Protocol: [`include/max25/protocol.md`](../include/max25/protocol.md)

Standalone client for direct modem interaction. HyBBX-compatible look and behaviour; configuration and hardware lifecycle stay in **`max25d`**.

Per-modem terminal profiles (YAML): [`share/clients/`](../share/clients/README.md) — one file per device that needs settings beyond BayCom `baycom-pr.ini` catalog references.

## Binaries

| Binary | Symlink | Role |
|--------|---------|------|
| `max25d` | — | **Mainstream OS only** — Linux/KLinux now; see [PLATFORMS.md](PLATFORMS.md) |
| `max25-terminal` | `max25-client` | **v1 ready** — operator UI; local or remote M25/1 to `max25d` |

The operator talks to the **modem** through the terminal; **`max25d` on Linux** owns hardware and BayCom.

## Platform split

| Where | What runs |
|-------|-----------|
| **Linux / KLinux** (`max25d` priority 1) | `max25d` + optional local `max25-terminal` |
| **FreeBSD** (DEV-Level 1) | `max25-terminal` → FreeBSD `max25d` (Main/TCP/IP + minimal CRDOP) |
| **OpenBSD / NetBSD** | after FreeBSD works |
| **macOS / Windows** | `max25-terminal` → remote or local `max25d` when those tiers ship |
| **Smaller systems** (AmigaOS) | `max25-terminal` or reduced M25/1 client — **no** `max25d` |

Full port order: [PLATFORMS.md](PLATFORMS.md). Transport: TCP port **7325** (or Unix socket on local Linux).

**AmigaOS:** `stacks/terminal/amiga/` — TCP-only, no F10/ncurses menu parity. MS-DOS / FreeDOS / legacy DOS: **not** a client target.

## Client UI policy

### Operator client (`max25-terminal`) — long-term text-only

The session client stays a **terminal program**, not a desktop or browser application:

- Text-only (TTY / ncurses / ANSI fallback) — **no windowing GUI**
- **F10** menu, number keys **0–9** — no function-key navigation beyond F10
- HyBBX palette only (light gray on black)
- See [MAX25-CLIENT.md](MAX25-CLIENT.md#ui-contract-long-term-stable) for the binding contract

A graphical client (Qt, GTK, native windows, or similar) is **not** on the near- or mid-term roadmap for `max25-terminal`. Integrators should assume **years** of text-only operation for live modem sessions.

### Web UI — separate, DEV-Level 3 (*ca.*)

A **Web UI** (browser access to `max25d` for status, configuration overview, or remote administration) is scaffolded on the hyBBX reverse-proxy pattern. Production delivery is **DEV-Level 3** — after modular TCP/IP + Linux/FreeBSD compat ([V2.0.0-SCOPE.md](V2.0.0-SCOPE.md#dev-levels-roadmap-stack-wide)). It serves a different role than the operator client:

- **Does not** replace `max25-terminal` for live TX/RX or AX.25 UI sessions
- **Does not** change the M25/1 client contract or F10 menu model
- **Current state:** scaffold only (`stacks/web/`) — see [WEBSOCKET.md](WEBSOCKET.md)

Until the WebSocket stack is released, all operator workflows documented here use `max25-terminal` only.

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
│ 7  Change DEVICE (TX target)        │
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

### `SET DEVICE` (session target)

On Linux, `max25d` runs **one** RF backend per host. `SET DEVICE <id>` must match that configured id (or `[devices] default`). Legacy multi-id INI templates still parse but are **deprecated** for new sites.

| Method | Example |
|--------|---------|
| F10 menu | **`7`** → enter device id (`tnc2c`, `baycom-ser12`, …) |
| CLI flag | `max25-terminal -d tnc2c -U /run/max25/modem.sock` |
| M25/1 text | `SET DEVICE tnc2c` (protocol — any M25/1 client) |

The header line shows the active **DEVICE** id. `GET DEVICES` lists enabled ids ([protocol.md](../include/max25/protocol.md)).

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

In **hybbx-host** operating mode: `max25d` prepares hardware; HyBBX attaches via `share/hybbx/*.ini.example`. MAX25 Terminal remains for local modem debug and live ID changes.

## Out of scope (operator client)

- Graphical windowing UI for `max25-terminal` (long-term — text client remains canonical)
- A second official session client or alternative TTY stack
- Raw serial client setup in the client process
- Multi-colour UI / themes / graphical frontends for the terminal
- Function-key menu navigation (except F10 to toggle menu)

The planned **Web UI** (WebSocket browser terminal) is in development — see [WEBSOCKET.md](WEBSOCKET.md). It does not supersede this client when released.

## See also

- [docs/README.md](README.md) — doc index
- [PACKET-RADIO.md](PACKET-RADIO.md) — AX.25 / KISS technical reference
- [MAX25-CLIENT.md](MAX25-CLIENT.md) — develop & connect the official client
- [ARCHITECTURE.md](ARCHITECTURE.md) — stack layers
- [HYBBX.md](HYBBX.md) — attach contract
- [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) — release scope
