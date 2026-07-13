# HyBBX + TNC2C

MAX25 prepares the TNC (recovery + KISS entry); HyBBX attaches with **`kiss_entry = none`**.

## Flow

```
max25d auto_start / max25-ctl start --hardware tncs --device tnc2c
        ↓  (software recovery + kiss on)
HyBBX Secondary starts packet_radio plugin (attach-only)
        ↓
KISS on serial → AX.25 sessions
```

Software recovery without power cycle: [TNC-RECOVERY.md](TNC-RECOVERY.md).

## Preparation (MAX25)

```bash
./scripts/max25-ctl start --hardware tncs --device tnc2c
# Production: max25d with [stack] auto_start = yes
```

One process per serial port — stop other userspace serial owners before HyBBX starts.

## HyBBX INI

Merge `share/hybbx/tnc2c-host.ini.example` or `stacks/tncs/hybbx-tnc2c.ini` into Secondary `hybbx.ini`:

```ini
[transport.packet_radio1]
tnc = tnc2c
device = /dev/ttyUSB0
baud = 19200
serial_line = 8n1
rts_dtr = yes
kiss_entry = none
persist = 255

[max25]
check = yes
```

Set `device`, callsign, and frequency for your station.

For HyBBX **without** max25d (standalone), use `kiss_entry = kiss_on` or `auto` instead — HyBBX runs its own recovery before KISS entry.

## Checks

- MAX25 prep returned host/KISS ready (boot-wait OK or max25d `ready`)
- `fuser` on device is empty before HyBBX start (max25d holds port in production)
- Log shows KISS active on the expected port

Full contract: [docs/HYBBX.md](../../docs/HYBBX.md)
