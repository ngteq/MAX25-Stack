# Operating mode: HyBBX Host

Secondary RF host on a HyBBX **Secondary** node. MAX25 prepares hardware; HyBBX bridges AX.25 to Main over HBX.

## Workflow

1. MAX25 device prep (boot-wait, `baycom-pr-ctl start`, or `crdopc`)
2. Merge `share/hybbx/*-host.ini.example` into Secondary `hybbx.ini`
3. Start HyBBX Secondary

## Per device

| Device | MAX25 prep | HyBBX plugin |
|--------|------------|--------------|
| TNC2C | `tnc2c-boot-wait.sh` | `packet_radio` |
| BayCom SER12 | `baycom-pr-ctl start` | `baycom` |
| CRDOP | `crdopc` running | `crdop` |

Contract: [docs/HYBBX.md](../../docs/HYBBX.md)
