# Master operator guide · MAX25-Stack 1.5.0

Linear guide: layer model, max25d, devices, M25/1, TNC recovery, HyBBX boundary.

## Layer matrix

| Layer | Component |
|-------|-----------|
| Operator UI | `max25-terminal` — F10 menu |
| Daemon | `max25d` — M25/1 `:7325` |
| HyBBX (external) | `packet_radio` / `baycom` / `crdop` |
| Hardware | `tncs` / `modems` / `soft-modems` |

## Host layout matrix

| Role | Count | Function |
|------|-------|----------|
| Main max25d | 1× | Stack hub, HyBBX attach, M25/1 |
| Secondary max25d | 0–5+ | One RF backend each |

## Start by device matrix

| Device | Command |
|--------|---------|
| TNC2C | `max25-ctl start --hardware tncs --device tnc2c` |
| BayCom SER12 | `max25-ctl start --hardware modems --device baycom-ser12` |
| CRDOP | `max25-ctl start --hardware soft-modems --device soft-crdop` |

## HyBBX boundary matrix

| MAX25 owns | HyBBX owns |
|------------|------------|
| Boot-wait, DTR/RTS, MYCALL, `kiss on` | KISS attach (`kiss_entry=none`) |
| BayCom kernel lifecycle | AX.25 UI, HBX bridge |
| CRDOP TCP 8515/8516 | User sessions, `/broadcast ax25` |
| M25/1 `:7325` | `[max25] check=yes` probe |

## Related

| Goal | Doc |
|------|-----|
| Host setup | [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md) |
| HyBBX | [HYBBX.md](HYBBX.md) |
