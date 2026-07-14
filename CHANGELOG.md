# Changelog · MAX25-Stack 1.5.0

All notable changes to MainAX25-Stack (MAX25-Stack) are documented here.

## [MAX25-Stack 1.5.0]

Version file `1.5.0`. Product label **MAX25-Stack-v1.5.0**.

### HyBBX boundary matrix

| Change | Detail |
|--------|--------|
| `[features] baycom=no` | Default in max25d INI examples |
| `[features] pccom=no` | Default in max25d INI examples |
| Device filter | BayCom/PC-COM entries filtered unless features enabled |
| CMake | BayCom tools still built; runtime opt-in via INI |

### Platform and topology matrix

| Change | Detail |
|--------|--------|
| One RF device per Linux host | Design rule in INI examples |
| FreeBSD scaffold | `max25_platform.py`, OSS sound-proxy, FreeBSD INI |
| Modular TCP/IP server | `modular_tcp_server.py` for Main/Secondary split |
| New INI templates | `max25d.main.ini.example`, `max25d.secondary-linux.ini.example`, `max25d.freebsd.ini.example` |

### Docs matrix

| Item | Detail |
|------|--------|
| Operator docs | Updated for v1.5 boundary |
| New | `V2.0.0-SCOPE.md`, `MODULAR-TCPIP-SERVER.md`, `MASTER-GUIDE.md` |

## [MAX25-Stack 1.0.0] — 2026-07-13

Version file `1.0.0`. Product label **MAX25-Stack-v1.0.0**.

### Active devices matrix

| Device | Standalone | HyBBX |
|--------|------------|-------|
| **tnc2c** | `max25-ctl start --hardware tncs --device tnc2c` | `packet_radio` |
| **baycom-ser12** | `max25-ctl start --hardware modems --device baycom-ser12` | `baycom` |
| **soft-crdop** | `max25-ctl start --hardware soft-modems` | `crdop` |

### Architecture matrix

| Item | Value |
|------|-------|
| AX.25 codec | In-tree `ax25_codec.py` via `kiss_bridge.py` |
| `MAX25_BUNDLE_AX25` | OFF default |
| `MAX25_BUILD_CRDOP` | ON default |
| Daemon | `max25d` — Linux supervisor, M25/1 |
| Client | `max25-terminal` / `max25-client` — sole official operator client |

### Deferred to v1.1+ matrix

| Item | Status |
|------|--------|
| `pktnc2`, `baycom-par96`, `baycom-kiss` | deferred |
| CRDOP amateur / dual workflows | INI templates ship |

## Related

| Goal | Doc |
|------|-----|
| Release gates | [RELEASE-READINESS.md](RELEASE-READINESS.md) |
| v1 scope | [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) |
