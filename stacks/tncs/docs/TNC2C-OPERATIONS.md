# TNC2C operations

Landolt TNC2C on a serial port — boot-wait, verify, HyBBX attach.

## Prerequisites

- Port free: no HyBBX or other userspace serial owner on the TNC serial device
- `tnc2c-serial.env` matches your wiring (device, baud, line format)

## Boot-wait (host mode)

```bash
cd stacks/tncs
./tnc2c-boot-wait.sh
```

Power cycle the TNC while DTR is asserted. Expect `OK: HOST` when successful.

## Verify

```bash
./tnc2c-integration-test.sh
./tnc2c-health.sh
```

## HyBBX

1. Complete boot-wait on the TNC port.
2. Start HyBBX Secondary with `share/hybbx/tnc2c-edge.ini.example` merged into `hybbx.ini`.
3. Do not run another userspace serial client on the same device while HyBBX is active.

See [HYBBX-TNC2C.md](HYBBX-TNC2C.md) and [../../docs/HYBBX.md](../../docs/HYBBX.md).

## Recovery

| Symptom | Action |
|---------|--------|
| Echo only, no `cmd:` | Re-run boot-wait with power cycle |
| Port busy | Stop HyBBX or other serial owner; check `fuser` on device |
| Wrong baud | Fix `tnc2c-serial.env` and retry |
