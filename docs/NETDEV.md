# Virtual netdev max25d0 · MAX25-Stack 1.5.0

TUN interface plan for modular TCP/IP — DEV-Level 1/2.

## Interface matrix

| Item | Value |
|------|-------|
| TUN name | `max25d0` (Linux) |
| Purpose | IPv4/IPv6 over AX.25 path |
| Status | planned / scaffold |
| Sidecar | `max25-tun` (DEV-Level 2) |

## Relation matrix

| Component | Role |
|-----------|------|
| max25d | KISS/device backends |
| max25d0 | IP encapsulation endpoint |
| modular TCP/IP server | Main/Secondary split |

## Related

| Goal | Doc |
|------|-----|
| Modular TCP/IP | [MODULAR-TCPIP-SERVER.md](MODULAR-TCPIP-SERVER.md) |
| v2 scope | [V2.0.0-SCOPE.md](V2.0.0-SCOPE.md) |
