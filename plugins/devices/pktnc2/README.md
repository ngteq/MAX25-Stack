# Device: PK-TNC2 / TNC-2 (TheFirmware)

**Status:** Planned — Unit B (Stabo + PK-TNC2).

| Parameter | Expected |
|-----------|----------|
| Port | TBD (`/dev/ttyUSB0`) |
| Host | 9600 8N1 |
| RF | 1200 AFSK CB |
| HyBBX | `tnc=tnc2`, `kiss_entry=auto` |

## When hardware arrives

1. Assign serial port in `pktnc2-serial.env`
2. Run `stacks/tncs/tnc2c-probe` to scan baud/parity
3. `./stacks/tncs/pktnc2-boot-wait.sh`
4. HyBBX with `share/hybbx/pktnc2-edge.ini.example`

See `stacks/tncs/research/tnc2c/ebay-227405716803.md`.
