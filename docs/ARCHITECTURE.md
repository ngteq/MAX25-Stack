# Architecture · MAX25-Stack 1.8.5-fallback_untested-upcoming#1

Main AX.25 Stack — standalone packet-radio with HyBBX-compatible plugin boundaries.

## Layer model matrix

| Layer | Examples |
|-------|----------|
| Terminal | `max25-terminal`, `max25-client` |
| Daemon | `max25d` — M25/1, plugin lifecycle |
| Operating mode | `standalone`, `service`, `hybbx-host` |
| Hardware | `tncs`, `modems`, `soft-modems` |
| Device | `tnc2c`, `max25e0`, `soft-crdop` |
| Protocol | KISS, kernel hdlcdrv, CRDOP M25 host |

## DEV-Level matrix

| DEV-Level | Focus |
|-----------|-------|
| DEV-Level 1 (current) | Modular TCP/IP, Linux+FreeBSD compat, `max25d0` |
| DEV-Level 2 | Main+Secondary supervision, `max25-tun` |
| DEV-Level 3 | WebSocket gateway |
| DEV-Level 4 | CRDOP expansion |
| Later | AI/assistant — deferred |

## Platform split matrix

| Component | Linux | FreeBSD |
|-----------|-------|---------|
| `max25d` + RF (TNC/BayCom) | yes | scaffold |
| `max25-terminal` | yes | yes (remote) |
| CRDOP | ALSA | OSS |
| Kernel BayCom `bcsf0` | yes | no |

## Related

| Goal | Doc |
|------|-----|
| Platforms | [PLATFORMS.md](PLATFORMS.md) |
| v2 scope | [V2.0.0-SCOPE.md](V2.0.0-SCOPE.md) |
