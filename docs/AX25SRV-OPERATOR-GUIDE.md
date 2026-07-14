# AX25SRV operator guide · MAX25-Stack 1.5.0

MAX25 side of dual-TNC standalone Main — prep before HyBBX attach.

## Responsibility matrix

| Phase | MAX25 | HyBBX |
|-------|-------|-------|
| TNC cold boot | boot-wait / max25d | — |
| MYCALL, `kiss on` | max25d | — |
| M25/1 listen | `:7325` | `[max25] check=yes` |
| KISS in operation | prep complete before HyBBX | attach `kiss_entry=none` |

## Pre-flight matrix

| # | Check |
|---|-------|
| 1 | `tnc2c-boot-wait.sh` or max25d device map |
| 2 | One process per `/dev/tty*` |
| 3 | `ss -ltn | grep 7325` before HyBBX start |
| 4 | INI: `serial_watch=yes`, recovery flags per site |

## Dual-TNC matrix

| TNC | Device key | Notes |
|-----|------------|-------|
| Primary | `tnc2c` or `[devices]` entry | unique serial path |
| Secondary | second `[devices]` entry | unique `link_id` in HyBBX |

## Related

| Goal | Doc |
|------|-----|
| HyBBX guide | HyBBX `docs/AX25SRV-OPERATOR-GUIDE.md` |
| Packet radio | [PACKET-RADIO.md](PACKET-RADIO.md) |
