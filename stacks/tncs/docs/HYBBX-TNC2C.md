# HyBBX + TNC2C

MAX25 prepares the TNC; HyBBX opens KISS after boot-wait.

## Flow

```
max25-ctl start --hardware tncs --device tnc2c   # boot-wait, DTR
        ↓
HyBBX Secondary starts packet_radio plugin
        ↓
KISS on serial → AX.25 sessions
```

## Preparation (MainAX25)

```bash
./scripts/max25-ctl start --hardware tncs --device tnc2c
```

One process per serial port — stop minicom and other TNC tools before HyBBX starts.

## HyBBX INI

Merge `share/hybbx/tnc2c-edge.ini.example` into Secondary `hybbx.ini`:

```ini
[transport.packet_radio1]
tnc = tnc2c
device = /dev/ttyUSB0
baud = 19200
serial_line = 8n1
rts_dtr = yes
kiss_on_startup = yes
```

Set `device`, callsign, and frequency for your station.

## Checks

- Boot-wait returned host mode
- `fuser` on device is empty before HyBBX start
- Log shows KISS active on the expected port

Full contract: [docs/HYBBX.md](../../docs/HYBBX.md)
