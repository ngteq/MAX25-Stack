# max25-client / M25/1 · MAX25-Stack 1.5.0

M25/1 text protocol reference for client developers.

## Protocol matrix

| Item | Value |
|------|-------|
| Transport | TCP `:7325` or Unix socket |
| Framing | line-oriented text commands |
| Spec | `include/max25/protocol.md` |
| Codec | in-tree — no kernel AX.25 required |

## Session matrix

| Phase | Commands |
|-------|----------|
| Select device | `SET DEVICE`, `LIST DEVICES` |
| Connect | `CONNECT`, `DISCONNECT` |
| Transfer | `SEND`, status queries |
| Ban list | `BAN`, `UNBAN`, `BANS` |

## Client profile matrix

| Item | Path |
|------|------|
| Profiles | `share/clients/` |
| Index | `share/clients/index.yaml` |
| Official client | `max25-terminal` only |

## Related

| Goal | Doc |
|------|-----|
| Terminal operator | [MAX25-TERMINAL.md](MAX25-TERMINAL.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
