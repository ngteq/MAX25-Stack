# max25-terminal · MAX25-Stack

Sole official operator client — text lines + F10 menu over M25/1.

## Canonical binary

| Path | Role |
|------|------|
| `/usr/local/bin/max25-terminal` | Install / PATH — **prefer** |
| `build*/bin/max25-terminal` | CMake output |
| `stacks/terminal/max25-terminal` | Tree copy after build (optional) |

**Never** `stacks/daemon/max25-terminal` — that path does not exist (daemon is `stacks/daemon/max25d`).

```bash
max25-terminal --help
# lists: -H -p -U -d/--device -v --probe …
```

`-d` / `--device` is **optional**: with max25d `[devices] default = max25e0`, the session already starts on that id. Use `-d` only to override, or type `SET DEVICE <id>` / F10 → **7**.

## Canonical connect (BayCom/based · bcpr)

```bash
# max25d already up (auto_start owns max25-bcprd)
max25-terminal -U /run/max25/modem.sock
# header DEVICE: max25e0 when default=max25e0
# F10 → 6  (CONNECT)   then   SEND …   or F10 → 4
```

## Connection matrix

| Mode | Target |
|------|--------|
| Unix socket | `/run/max25/modem.sock` |
| TCP | `127.0.0.1:7325` or remote host |
| Flags | `--ax25-ui` (default on) · `--no-ax25-ui` for plain SEND |

```bash
max25-terminal -U /run/max25/modem.sock
max25-terminal -T -H 127.0.0.1 -p 7325
# optional override after connect:
max25-terminal -U /run/max25/modem.sock -d max25e0
```

## Device selection

| Method | When |
|--------|------|
| max25d `[devices] default = …` | Session starts on that id — **no** `-d` needed |
| `-d` / `--device ID` | CLI `SET DEVICE` right after connect |
| Type `SET DEVICE <id>` | In the terminal prompt |
| F10 → **7** | Menu: Change DEVICE (TX target) |

`CONNECT` (F10 → **6**, or type `CONNECT`) attaches the **currently selected** device.

## Command matrix

| Command | Action |
|---------|--------|
| `SET DEVICE <id>` | Select RF backend |
| `GET DEVICES` | List enabled devices |
| `CONNECT` | Attach selected device |
| `SEND …` | Transmit payload |
| F10 menu | Device ops, status, bans |

## F10 menu

| Key | Action |
|-----|--------|
| 1 | CALLERID |
| 2 | CALLID |
| 3 | Status |
| 4 | Send line |
| 5 | RX only (Monitor) |
| 6 | Connection on/off (`CONNECT` / `DISCONNECT`) |
| 7 | Change DEVICE |
| 0 | Quit |

## Identity matrix

| Terminal field | AX.25 field |
|----------------|-------------|
| CALLERID | source address |
| CALLID | destination address |

## Related

| Goal | Doc |
|------|-----|
| M25/1 protocol | [MAX25-CLIENT.md](MAX25-CLIENT.md) |
| Operator runbook | [MAX25-OPERATOR-RUNBOOK.md](MAX25-OPERATOR-RUNBOOK.md) |
| BayCom/based (bcpr) | [BAYCOM.md](BAYCOM.md) |
| TX/RX release test | [TX-RX-TEST.md](TX-RX-TEST.md) |
