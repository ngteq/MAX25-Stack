# max25-terminal · MAX25-Stack 1.5.0

Sole official operator client — text lines + F10 menu over M25/1.

## Connection matrix

| Mode | Target |
|------|--------|
| Unix socket | `/run/max25/modem.sock` |
| TCP | `127.0.0.1:7325` or remote host |
| Flags | `--ax25-ui` for live AX.25 display |

## Command matrix

| Command | Action |
|---------|--------|
| `SET DEVICE <id>` | Select RF backend |
| `CONNECT` | Attach to device |
| `SEND` | Transmit payload |
| F10 menu | Device ops, status, bans |

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
