# Device: Landolt TNC2C

**Status:** Active (v1).

| Parameter | Value |
|-----------|-------|
| Serial | `/dev/ttyUSB0` or `/dev/ttyS4` (site-specific) |
| Host line | 19200 8N1, RTS+DTR |
| RF | 2400 AFSK |
| HyBBX | `tnc=tnc2c`, `protocol=kiss` |

## Boot sequence

DTR must be high during power-on:

```bash
./stacks/tncs/tnc2c-boot-wait.sh
./stacks/tncs/tnc2c-integration-test.sh
```

HyBBX INI: `share/hybbx/tnc2c-edge.ini.example`

## Safety

No `kiss on` or TX tests without dummy load when antenna connected.
