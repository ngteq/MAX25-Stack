# Documentation index

Main AX.25 Stack (**MAX25**) — compact doc map for v1.0.

[README](../README.md) · [AGENTS](../AGENTS.md) · [CONTRIBUTING](../CONTRIBUTING.md)

## By role

| Role | Document |
|------|----------|
| **Master operator guide (synced)** | **[MASTER-GUIDE.md](MASTER-GUIDE.md)** — linear start |
| **Dual-TNC / AX25SRV** | [AX25SRV-OPERATOR-GUIDE.md](AX25SRV-OPERATOR-GUIDE.md) |
| Host setup | [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md) |
| **Unified device workflow** | [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) — TNC reference, all backends |
| Terminal operator | [MAX25-TERMINAL.md](MAX25-TERMINAL.md) |
| Browser terminal (Web UI) | [WEBSOCKET.md](WEBSOCKET.md) *(DEV-Level 3 — planned)* · [stacks/web/README.md](../stacks/web/README.md) |
| Client developer | [MAX25-CLIENT.md](MAX25-CLIENT.md) · [include/max25/protocol.md](../include/max25/protocol.md) |
| Terminal profiles | [share/clients/README.md](../share/clients/README.md) · [share/clients/index.yaml](../share/clients/index.yaml) |
| HyBBX integrator | [HYBBX.md](HYBBX.md) |
| BayCom / PC-COM operator | [BAYCOM.md](BAYCOM.md) · `share/baycom/` examples |
| Host / operator | [MAX25-OPERATOR-RUNBOOK.md](MAX25-OPERATOR-RUNBOOK.md) · [HARDWARE-ACCEPTANCE.md](HARDWARE-ACCEPTANCE.md) |
| **All devices (full list)** | [DEVICES-LIST-FULL.md](DEVICES-LIST-FULL.md) |
| AX.25 codec | [AX25-NATIVE-CODEC.md](AX25-NATIVE-CODEC.md) |
| Contributor | [DEVELOPMENT.md](DEVELOPMENT.md) · [PATHS.md](PATHS.md) |
| Virtual netdev **`max25d0`** (TUN, IPv4/IPv6) | [NETDEV.md](NETDEV.md) |
| v1 release | [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) |
| **v2 goals (rootless, auto setup)** | [V2.0.0-SCOPE.md](V2.0.0-SCOPE.md) — includes **DEV-Levels roadmap** |

## Technical reference

| Topic | Document |
|-------|----------|
| Architecture & plugins | [ARCHITECTURE.md](ARCHITECTURE.md) · [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) |
| AX.25 / KISS / TNC | [PACKET-RADIO.md](PACKET-RADIO.md) · [include/max25/packet-radio.md](../include/max25/packet-radio.md) |
| BayCom kernel modems | [BAYCOM.md](BAYCOM.md) |
| **CRDOP / MAX25-SoftModem** | [CRDOP.md](CRDOP.md) · [stacks/crdop/docs/INDEX.md](../stacks/crdop/docs/INDEX.md) · [stacks/crdop/README.md](../stacks/crdop/README.md) |
| Platforms | [PLATFORMS.md](PLATFORMS.md) |
| *BSD port plan | [FREEBSD-AX25.md](FREEBSD-AX25.md) — FreeBSD → OpenBSD → NetBSD |
| **Modular TCP/IP Servers Service** | [MODULAR-TCPIP-SERVER.md](MODULAR-TCPIP-SERVER.md) |
| Merge archive | [MERGE-REPORT.md](MERGE-REPORT.md) |

## Stack READMEs (link — do not duplicate here)

| Stack | Path |
|-------|------|
| TNC tools | [stacks/tncs/README.md](../stacks/tncs/README.md) |
| BayCom | [stacks/baycom-pr/README.md](../stacks/baycom-pr/README.md) |
| CRDOP | [CRDOP.md](CRDOP.md) · [stacks/crdop/docs/INDEX.md](../stacks/crdop/docs/INDEX.md) · [stacks/crdop/README.md](../stacks/crdop/README.md) |
| Daemon (`max25d`) | [stacks/daemon/README.md](../stacks/daemon/README.md) |
| Terminal | [stacks/terminal/README.md](../stacks/terminal/README.md) |
| Web UI | [stacks/web/README.md](../stacks/web/README.md) |

## Plugin registry

[plugins/README.md](../plugins/README.md) · `plugins/manifest.yaml`

```bash
./scripts/discover-plugins.sh          # hardware + device plugins
./scripts/discover-plugins.sh --json   # machine-readable
```

Discovery lists **hardware** and **device** entries only. Operating modes (`betriebsform/`) live in the manifest but are not discovery CLI output.
