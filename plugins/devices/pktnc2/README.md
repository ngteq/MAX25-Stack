# Device: PK-TNC2

**Status:** Planned — probe serial port after hardware delivery.

PK-TNC2 / TNC-2 (TheFirmware) profile for HyBBX `packet_radio` with `tnc=tnc2`.

## Preparation

```bash
# After delivery: edit stacks/tncs/pktnc2-serial.env
./stacks/tncs/pktnc2-boot-wait.sh
```

HyBBX: `share/hybbx/pktnc2-edge.ini.example`

Reuses `tnc2c-probe` for port scan.
