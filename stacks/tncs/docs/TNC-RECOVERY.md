# TNC recovery (software-first)

TheFirmware / TNC-2 class devices (Landolt TNC2C, PK-TNC2, TAPR TNC-2) can usually return to **host command mode** and **KISS** without a power cycle. Power-cycle with DTR held high is a **rescue fallback** only.

Shared implementation: `stacks/tncs/tnc_serial_recovery.py` (used by `tnc2c-host-reset`, `tnc2c-boot-wait`, and `max25d` `kiss_bridge`).

## When to use what

| Situation | First action | Rescue (if software fails) |
|-----------|--------------|----------------------------|
| Echo-only (`INFO` → `INFO`, no banner) | `./tnc2c-host-reset.sh` | `./tnc2c-boot-wait.sh` + power cycle while DTR high |
| Stuck in KISS / host (JHOST) | `./tnc2c-host-reset.sh --kiss` | Same boot-wait rescue |
| After `max25d` attach fails (`error-host`) | `./tnc2c-boot-wait.sh --recover-only` | Boot-wait + power cycle |
| PK-TNC2 (9600 8N1) | `./pktnc2-boot-wait.sh --recover-only` | `./pktnc2-boot-wait.sh` + power cycle |
| Cold boot, never saw `cmd:` | `./tnc2c-boot-wait.sh` (DTR before power-on) | Fix wiring (DTR/RTS, CTS bridge) |

## Software recovery ladder

Run with **DTR+RTS high** and the port open:

1. Passive listen (~1.5 s)
2. KISS return frame `0xC0 0xFF 0xC0`
3. JHOST 0 — 300× NUL + framed `JHOST 0\r`
4. `kiss off` + `INFO` — stop if firmware banner appears
5. 3× Ctrl-C + `RESTART` + `INFO`
6. Buffer flush `^Q^X` + `kiss off` + `INFO`

Success markers: `TheFirmware`, `NORD`, `Version 2.7`, `Checksum`, `cmd:`.

Then enter KISS: `kiss on` (TNC2C) or `auto` (`kiss on`, then ESC+`@K` if echo-only — PK-TNC2).

## Operator commands

```bash
cd stacks/tncs

# Software recovery (no power cycle)
./tnc2c-host-reset.sh              # terminal mode
./tnc2c-host-reset.sh --kiss       # terminal + KISS
./tnc2c-boot-wait.sh --recover-only

# PK-TNC2
./pktnc2-boot-wait.sh --recover-only

# Rescue: power cycle with DTR held (Landolt TNC2C cold-boot requirement)
./tnc2c-boot-wait.sh               # power OFF → ON while script runs
```

## MAX25 + HyBBX contract

| Layer | Responsibility |
|-------|----------------|
| `max25d` / boot-wait | DTR sequencing, software recovery, `kiss on` / `auto` |
| HyBBX `packet_radio` | Attach only — `kiss_entry = none` |
| Power cycle | Rescue when DTR was low at cold boot or hardware hang |

HyBBX INI (production): `kiss_entry = none`, `persist = 255` (CB CSMA), optional `[max25] check = yes`.

max25d runs `recover_terminal()` in `kiss_bridge.attach_session()` before `MYCALL` and KISS entry.

## Power-cycle rescue (only when needed)

Use when:

- Software ladder ends in echo-only or silence
- TNC was powered on **without** DTR high (Landolt TNC2C terminal detection)
- Suspected hardware hang

```bash
./tnc2c-boot-wait.sh
# While script listens: power OFF 10 s, power ON — keep script running (DTR stays high)
```

Do **not** close the serial port between boot-wait and HyBBX/max25d attach — DTR drop can return the TNC to echo mode.

## See also

- [TNC2C-OPERATIONS.md](TNC2C-OPERATIONS.md) — daily ops
- [HYBBX-TNC2C.md](HYBBX-TNC2C.md) — HyBBX attach
- [../../docs/PACKET-RADIO.md](../../docs/PACKET-RADIO.md) — serial profiles, CSMA
