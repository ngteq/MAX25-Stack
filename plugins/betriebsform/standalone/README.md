# Operating mode: Standalone

Single-operator packet radio. One TNC or one BayCom modem online.

## Use cases

- Terminal `listen` / `call` on AX.25 ports
- TNC2C health checks and boot-wait before HyBBX
- Single BayCom modem via `baycom-pr-ctl start`

## Start

```bash
# Serial TNC (TNC2C)
./scripts/max25-ctl start --mode standalone --hardware tncs --device tnc2c

# BayCom modem
./scripts/max25-ctl start --mode standalone --hardware modems --device baycom-ser12
```

## HyBBX

Optional. When HyBBX runs, it opens the serial device or KISS PTY **after** the stack has prepared the hardware (boot-wait, driver load).

See `share/hybbx/standalone.ini.example`.
