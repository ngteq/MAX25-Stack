# TNC2C operations

Landolt TNC2C on a serial port — software recovery, boot-wait rescue, verify, HyBBX attach.

## Prerequisites

- Port free: no HyBBX or other userspace serial owner on the TNC serial device
- `tnc2c-serial.env` matches your wiring (device, baud, line format)
- DTR+RTS asserted while talking to the TNC (boot-wait and host-reset do this)

## Normal prep (max25d / HyBBX)

Production path: `max25d` with `auto_start` runs boot-wait and software recovery before KISS attach.

```bash
./scripts/max25-ctl start --hardware tncs --device tnc2c
# or: sudo max25d -c /etc/max25/max25d.ini
```

Manual recovery without power cycle:

```bash
cd stacks/tncs
./tnc2c-host-reset.sh --kiss
# or: ./tnc2c-boot-wait.sh --recover-only
```

Full ladder and rescue rules: [TNC-RECOVERY.md](TNC-RECOVERY.md).

## Boot-wait (rescue — power cycle)

Use when software recovery fails or the TNC was cold-started without DTR high:

```bash
cd stacks/tncs
./tnc2c-boot-wait.sh
```

Power cycle the TNC while the script holds DTR+RTS. Expect `OK: HOST` when successful.

## Verify

```bash
./tnc2c-integration-test.sh
./tnc2c-health.sh
```

Integration test runs boot-wait + verify in one process so DTR does not drop between steps.

## HyBBX

1. MAX25 prep complete (boot-wait or `max25d` auto_start with recovery).
2. Merge `share/hybbx/tnc2c-host.ini.example` into Secondary `hybbx.ini` — **`kiss_entry = none`** (MAX25 owns KISS entry).
3. Do not run another userspace serial client on the same device while HyBBX is active.

See [HYBBX-TNC2C.md](HYBBX-TNC2C.md) and [../../docs/HYBBX.md](../../docs/HYBBX.md).

## Recovery

| Symptom | Action |
|---------|--------|
| Echo only, no `cmd:` | `./tnc2c-host-reset.sh` then `./tnc2c-boot-wait.sh --recover-only` |
| Still echo-only / silent | **Rescue:** `./tnc2c-boot-wait.sh` + power cycle (DTR high) |
| `max25d` reports `error-host` | Stop other serial owners; run `--recover-only`; restart max25d |
| Port busy | Stop HyBBX or other serial owner; check `fuser` on device |
| Wrong baud | Fix `tnc2c-serial.env` and retry |
