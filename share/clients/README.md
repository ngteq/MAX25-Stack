# Terminal client profiles (YAML)

Per-modem **max25-terminal** profiles for devices that need settings beyond a BayCom `baycom-pr.ini` catalog reference.

| Who reads this | Purpose |
|----------------|---------|
| **max25-terminal** | Connection target, default `SET DEVICE`, session IDs, UI pacing |
| **Operator** | Pick a profile: `max25-terminal -d tnc2c -U /run/max25/modem.sock` (device id from YAML `device.id`) |
| **max25d** | **Not** loaded from here — use `max25d.ini`, `baycom-pr.ini`, or env files |

## BayCom kernel modems — client YAML as operator reference

SER12 and PAR96 catalog entries in `stacks/baycom-pr/config/modems.ini` run **directly** via `baycom-pr.ini`:

```ini
[modem.a]
catalog = albrecht-pc-com
serial = /dev/ttyS0
```

Hardware is configured in `baycom-pr.ini`, not serial env. [`baycom-ser12.yaml`](baycom-ser12.yaml) mirrors the TNC client-profile pattern: connection defaults, `SET DEVICE` id, and pointers to `baycom-pr.ini` / `max25d.ini` — **not** loaded by `max25d`.

Terminal clients attach to **max25d** (KISS PTY) after `baycom-pr-ctl start`. See [docs/BAYCOM.md](../../docs/BAYCOM.md) and [docs/PLUGINS-DEVICE-MODEL.md](../../docs/PLUGINS-DEVICE-MODEL.md).

Registry of all catalog IDs (with and without client YAML): [`index.yaml`](index.yaml).

## Schema (`schema_version: 1`)

```yaml
schema_version: 1
id: tnc2c                    # max25d device id or catalog id
label: Human name
type: client-profile         # client-profile | catalog-only

connection:                  # terminal → max25d (never raw serial)
  host: 127.0.0.1
  port: 7325
  unix_socket: /run/max25/modem.sock

device:                      # M25/1 SET DEVICE on connect
  id: tnc2c
  hardware: tncs

session:                     # optional defaults (SET CALLERID / CALLID / AX25_UI)
  callerid: CB-0
  callid: QST
  ax25_ui: true

terminal:                    # HyBBX-aligned UI
  pacing_baud: 2400
  line_width: 80
  payload_max: 256

max25d:                      # pointers for daemon/site config (informational)
  ini_example: share/max25/max25d.ini.example
  device_section: serial.tnc2c
  env_file: stacks/tncs/tnc2c-serial.env
  boot_wait: stacks/tncs/tnc2c-boot-wait.sh

serial:                      # max25d-owned serial (client does not open)
  default_device: /dev/ttyS4
  baud: 19200
  line: 8n1
  dtr_rts: true
  kiss_entry: kiss_on
```

KISS-async and CRDOP profiles use `serial:` or `crdop:` instead of BayCom catalog fields.

## Files

| File | Modem / device |
|------|----------------|
| [`tnc2c.yaml`](tnc2c.yaml) | Landolt TNC2C |
| [`baycom-ser12.yaml`](baycom-ser12.yaml) | BayCom SER12 kernel (PC-COM) — operator reference |
| [`pktnc2.yaml`](pktnc2.yaml) | PK-TNC2 / TNC-2 (TheFirmware) |
| [`kiss-serial-usb.yaml`](kiss-serial-usb.yaml) | KISS on USB (`modems.ini` catalog) |
| [`kiss-serial-rs232.yaml`](kiss-serial-rs232.yaml) | KISS on RS-232 |
| [`baycom-kiss.yaml`](baycom-kiss.yaml) | MAX25 device plugin (USB KISS) |
| [`soft-crdop.yaml`](soft-crdop.yaml) | CRDOP sound-card modem |
| [`index.yaml`](index.yaml) | Full modem database map |

## See also

- [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md) — M25/1 protocol
- [docs/MAX25-TERMINAL.md](../../docs/MAX25-TERMINAL.md) — operator UI
- [stacks/baycom-pr/config/modems.ini](../../stacks/baycom-pr/config/modems.ini) — hardware catalog
