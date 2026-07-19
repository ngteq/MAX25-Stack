# FreeBSD AX.25 port · MAX25-Stack 1.8.5-fallback_untested-upcoming#1

FreeBSD platform plan — no native kernel AX.25; userspace KISS/M25/1 only.

## Platform matrix

| Component | FreeBSD |
|-----------|---------|
| `max25d` + TNC/BayCom RF | scaffold (Linux-first v1) |
| `max25-terminal` | yes — remote to Linux `:7325` |
| CRDOP / OSS | yes — primary softmodem path |
| Kernel BayCom | no |

## Split deployment matrix

| Role | Typical host |
|------|--------------|
| FreeBSD Main | TCP/IP hub + CRDOP |
| Linux Secondary | TNC / BayCom RF backend |

## Scaffold matrix (v1.5.0)

| Item | Path |
|------|------|
| Platform detection | `max25_platform.py` |
| OSS sound-proxy | CRDOP stack |
| INI example | `share/max25/max25d.freebsd.ini.example` |

## Related

| Goal | Doc |
|------|-----|
| Platforms | [PLATFORMS.md](PLATFORMS.md) |
| CRDOP | [CRDOP.md](CRDOP.md) |
