# TNC recovery (software-first)

TheFirmware / TNC-2 class devices (Landolt TNC2C, PK-TNC2, TAPR TNC-2) can usually return to **host command mode** and **KISS** without a power cycle. Power-cycle with DTR held high is a **rescue fallback** only.

Shared implementation: `stacks/tncs/tnc_serial_recovery.py` (used by `tnc2c-host-reset`, `tnc2c-boot-wait`, and `max25d` `kiss_bridge`).

## When to use what

| Situation | First action | Rescue (if software fails) |
|-----------|--------------|----------------------------|
| Echo-only (`INFO` → `INFO`, no banner) | `max25d` serial watch / `./tnc2c-host-reset.sh` | `./tnc2c-boot-wait.sh` only if cold-boot without DTR |
| After `max25d` prep `error-host` | Auto boot-wait escalate (power OFF 10s → ON) | `./tnc2c-boot-wait.sh` if escalate disabled |
| PK-TNC2 (9600 8N1) | `./pktnc2-boot-wait.sh --recover-only` | `./pktnc2-boot-wait.sh` + power cycle |
| Cold boot, never saw `cmd:` | `./tnc2c-boot-wait.sh` (DTR before power-on) | Fix wiring (DTR/RTS, CTS bridge) |

## Software recovery ladder

Run with **DTR+RTS high** and the port open:

1. Passive listen (~1.5 s) + **DTR settle 2 s** after open (max25d)
2. KISS return `0xC0 0xFF 0xC0` + ESC+`@K`
3. JHOST 0 — 300× NUL + framed `JHOST 0\r`
4. Buffer flush `^Q^X`
5. `kiss off` + `INFO` (also combined `kiss off`+`INFO`)
6. 3× Ctrl-C + `RESTART` / `@RESTART` + INFO
7. ESC E 0 + second RESTART round + final flush

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

max25d runs `recover_terminal()` in `kiss_bridge.stabilize_session()` before `MYCALL` and KISS entry. The KISS RX thread starts **only after** successful stabilization (avoids a race where RX consumes recovery replies).

### max25d serial watch (automatic)

When `[stack] serial_watch = yes` and `stack_recover_only = yes` (default), max25d **opens the TNC serial port itself** — no `boot-wait` subprocess (avoids port conflict). Recovery runs inline via `stabilize_session`.

| INI key | Default | Role |
|---------|---------|------|
| `serial_watch` | yes | Enable periodic probe + auto-repair |
| `serial_watch_interval` | 60 | Seconds between health probes |
| `serial_repair_cooldown` | 20 | Minimum gap between repair attempts |
| `stack_recover_only` | yes | Daemon start uses `--recover-only` (no power cycle) |
| `stack_retry_interval` | 120 | Retry failed stack prep with recover-only |
| `serial_bootwait_escalate` | yes | Escalate to boot-wait after repeated inline failures |
| `serial_bootwait_escalate_after` | 3 | Inline `error-host` failures before boot-wait |
| `serial_bootwait_escalate_cooldown` | 300 | Minimum seconds between boot-wait escalations |

Triggers: initial prep `error-host` (immediate boot-wait escalate), periodic interval, `error-host` / `error-kiss` / `error-tx` / `error-io`, failed TX (one auto-retry). Serial watch still escalates after `serial_bootwait_escalate_after` consecutive inline failures if prep did not already escalate.

## Firmware RX diagnostics (max25d / boot-wait)

On each recovery step, logs include byte count, matched firmware markers (`TheFirmware`, `cmd:`, …), and a printable preview. On failure:

- `recovery: firmware assessment — …` — classified state (silent, echo-only, binary/KISS, non-banner text)
- `recovery: RX capture — …` — full accumulated RX summary with hex snippet

Use these lines to distinguish **DTR/cold-boot** (echo-only, 0 B passive) from **wrong baud/line** (garbage/binary) from **stuck KISS** (binary frames, no `cmd:`).

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
