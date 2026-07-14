# Platforms · MAX25-Stack 1.5.0

Supported and planned platforms for max25d and max25-terminal.

## Component matrix

| Component | Linux | FreeBSD | Other |
|-----------|-------|---------|-------|
| `max25d` (full RF) | yes | scaffold | planned |
| `max25-terminal` | yes | yes | AmigaOS, macOS, Windows |
| CRDOP | ALSA | OSS | — |
| BayCom kernel | yes | no | — |

## Priority matrix

| Priority | Platform |
|----------|----------|
| 1 | Linux/KLinux (full) |
| 2 | FreeBSD server + CRDOP |
| 3 | OpenBSD → NetBSD → macOS → Windows |

## Interface name matrix

| Item | Linux name |
|------|------------|
| TUN (when shipped) | `max25d0` |
| BayCom netdev | `bcsf0` |

## Related

| Goal | Doc |
|------|-----|
| FreeBSD plan | [FREEBSD-AX25.md](FREEBSD-AX25.md) |
| v2 scope | [V2.0.0-SCOPE.md](V2.0.0-SCOPE.md) |
