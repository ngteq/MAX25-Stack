# Device: Landolt TNC2C

**Status:** Active on AX25SRV (Unit A).

| Parameter | Value |
|-----------|-------|
| Port | `/dev/ttyS4` |
| Host | 19200 8N1, RTS+DTR |
| RF | 2400 AFSK (TCM3105), CB K24 |
| HyBBX | `tnc=tnc2c`, `protocol=kiss` |

## Boot sequence

DTR must be high during power-on or TNC enters echo mode:

```bash
./stacks/tncs/tnc2c-boot-wait.sh   # power cycle while running
./stacks/tncs/tnc2c-integration-test.sh
```

## Safety

Never `kiss on` or `--tx` without dummyload when antenna connected.
