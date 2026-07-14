# Modular TCP/IP server · MAX25-Stack 1.5.0

Main + Secondary TCP/IP topology service — DEV-Level 1.

## Topology matrix

| Role | Function |
|------|----------|
| Main | TCP/IP hub, coordinates secondaries |
| Secondary | RF backend + registers with Main |
| Cross-host | LAN `host:port` peers |

## Component matrix

| Item | Path |
|------|------|
| Service | `modular_tcp_server.py` |
| INI Main | `share/max25/max25d.main.ini.example` |
| INI Secondary | `share/max25/max25d.secondary-linux.ini.example` |

## Platform matrix

| Host | Role |
|------|------|
| FreeBSD | TCP/IP hub + CRDOP (documented split) |
| Linux | TNC / BayCom Secondary |

## Related

| Goal | Doc |
|------|-----|
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| FreeBSD | [FREEBSD-AX25.md](FREEBSD-AX25.md) |
