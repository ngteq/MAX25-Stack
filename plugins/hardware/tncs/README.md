# Hardware: TNCs

Serial and USB Terminal Node Controllers. Merged from **TNCs-Stack**.

## Stack location

`stacks/tncs/` — tools, docs, HyBBX INI snippets, research.

## HyBBX

Use HyBBX `packet_radio` plugin with `tnc=` profile per device.

| Device | `tnc=` | Serial |
|--------|--------|--------|
| TNC2C | `tnc2c` | 19200 8N1, RTS/DTR |
| PK-TNC2 | `tnc2` | 9600/2400 8N1 |

## Build & test

```bash
make -C stacks/tncs all
make -C stacks/tncs integration
```

## Operator docs

- `stacks/tncs/docs/TNC-INVENTORY.md`
- `stacks/tncs/docs/TNC2C-OPERATIONS.md`
- `stacks/tncs/docs/HYBBX-TNC2C.md`
