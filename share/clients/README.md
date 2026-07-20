# Terminal client profiles (YAML)

Per-modem **max25-terminal** profiles for devices that need settings beyond a BayCom/based **bcpr** or TNC env catalog.

| Who reads this | Purpose |
|----------------|---------|
| **max25-terminal** | Connection target, default `SET DEVICE`, session IDs, UI pacing |
| **Operator** | `max25-terminal -U /run/max25/modem.sock` — device from max25d `[devices] default`, or `-d <id>` / F10→7 / `SET DEVICE` (id from YAML `device.id`) |
| **max25d** | **Not** loaded from here — use `max25d.ini`, `bcpr.ini`, or env files |

## BayCom/based (bcpr) — client YAML as operator reference

SER12 PC-COM class hardware runs via **bcpr** (`stacks/max25-bcpr/`), not a kernel driver. Configure `bcpr.ini` / max25d `[features] max25_bcpr=yes` and device **`max25e0`** (`max25e0 = max25-bcpr:bc0`). No separate client YAML is required — use max25d default or `SET DEVICE max25e0`.

Terminal clients attach to **max25d** after `max25-bcprd` / max25d bring-up. See [docs/BAYCOM.md](../../docs/BAYCOM.md) and [docs/PLUGINS-DEVICE-MODEL.md](../../docs/PLUGINS-DEVICE-MODEL.md).

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
| (none — use `max25e0`) | BayCom/based SER12 via max25-bcpr (PC-COM) |
| [`pktnc2.yaml`](pktnc2.yaml) | PK-TNC2 / TNC-2 (TheFirmware)
| [`kiss-serial-usb.yaml`](kiss-serial-usb.yaml) | KISS on USB (`modems.ini` catalog) |
| [`kiss-serial-rs232.yaml`](kiss-serial-rs232.yaml) | KISS on RS-232 |
| [`baycom-kiss.yaml`](baycom-kiss.yaml) | MAX25 device plugin (USB KISS) |
| [`soft-crdop.yaml`](soft-crdop.yaml) | CRDOP sound-card modem |
| [`index.yaml`](index.yaml) | Full modem database map |

## See also

- [docs/MAX25-CLIENT.md](../../docs/MAX25-CLIENT.md) — M25/1 protocol
- [docs/MAX25-TERMINAL.md](../../docs/MAX25-TERMINAL.md) — operator UI
- [stacks/max25-bcpr/share/max25-bcpr.ini.example](../../stacks/max25-bcpr/share/max25-bcpr.ini.example) — bcpr INI example
