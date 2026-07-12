# Documentation index

Main AX.25 Stack (**MAX25**) — compact doc map for v1.0.

[README](../README.md) · [AGENTS](../AGENTS.md) · [CONTRIBUTING](../CONTRIBUTING.md)

## By role

| Role | Document |
|------|----------|
| Edge deploy | [LINUX-EDGE-SETUP.md](LINUX-EDGE-SETUP.md) |
| Terminal operator | [MAX25-TERMINAL.md](MAX25-TERMINAL.md) |
| Client developer | [MAX25-CLIENT.md](MAX25-CLIENT.md) · [include/max25/protocol.md](../include/max25/protocol.md) |
| HyBBX integrator | [HYBBX.md](HYBBX.md) |
| Contributor | [DEVELOPMENT.md](DEVELOPMENT.md) |
| v1 release | [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) |

## Technical reference

| Topic | Document |
|-------|----------|
| Architecture & plugins | [ARCHITECTURE.md](ARCHITECTURE.md) |
| AX.25 / KISS / TNC / BayCom | [PACKET-RADIO.md](PACKET-RADIO.md) · [include/max25/packet-radio.md](../include/max25/packet-radio.md) |
| Platforms | [PLATFORMS.md](PLATFORMS.md) |
| *BSD deferred | [FREEBSD-AX25.md](FREEBSD-AX25.md) |
| Merge archive | [MERGE-REPORT.md](MERGE-REPORT.md) |

## Stack READMEs (link — do not duplicate here)

| Stack | Path |
|-------|------|
| TNC tools | [stacks/tncs/README.md](../stacks/tncs/README.md) |
| BayCom | [stacks/baycom-pr/README.md](../stacks/baycom-pr/README.md) |
| CRDOP | [stacks/crdop/README.md](../stacks/crdop/README.md) |
| Daemon (`max25d`) | [stacks/daemon/README.md](../stacks/daemon/README.md) |
| Terminal | [stacks/terminal/README.md](../stacks/terminal/README.md) |

## Plugin registry

[plugins/README.md](../plugins/README.md) · `plugins/manifest.yaml`

```bash
./scripts/discover-plugins.sh          # hardware + device plugins
./scripts/discover-plugins.sh --json   # machine-readable
```

Discovery lists **hardware** and **device** entries only. Operating modes (`betriebsform/`) live in the manifest but are not discovery CLI output.
