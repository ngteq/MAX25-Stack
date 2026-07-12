# Hardware: TNCs

Serial and USB Terminal Node Controllers. Merged from **TNCs-Stack** (`stacks/tncs/`).

## HyBBX

`packet_radio` plugin with `tnc=` profile per device.

| Device | `tnc=` | Serial |
|--------|--------|--------|
| TNC2C | `tnc2c` | 19200 8N1, RTS/DTR |
| PK-TNC2 | `tnc2` | 9600/2400 8N1 (planned) |

## Build & test

```bash
./scripts/build.sh
./stacks/tncs/tnc2c-integration-test.sh   # with hardware
```

## Docs

- [stacks/tncs/README.md](../../stacks/tncs/README.md)
- [stacks/tncs/docs/TNC2C-OPERATIONS.md](../../stacks/tncs/docs/TNC2C-OPERATIONS.md)
- [stacks/tncs/docs/TNC2C-REFERENCE.md](../../stacks/tncs/docs/TNC2C-REFERENCE.md)
