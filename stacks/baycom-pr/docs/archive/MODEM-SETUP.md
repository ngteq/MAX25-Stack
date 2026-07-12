# Modem setup quick reference

Per-catalog defaults from [modems.ini](../config/modems.ini). Matrix: [MODEMS.md](MODEMS.md). INI keys: [MANUAL.md](MANUAL.md).

**kernel-ser12:** `setserial /dev/ttySx uart none` before start.  
**kiss-serial:** plug device — no `setserial`.

## ser12 @ 1200 baud (`baycom_ser_fdx`)

| Catalog ID | mode | baud | txdelay | Notes |
|------------|------|------|---------|-------|
| `baycom-ser12` | `ser12*` | 1200 | 20 | Reference DIY |
| `albrecht-pc-com` | `ser12*` | 1200 | **35** | **Offline verified** |
| `albrecht-pc-com-4500` | `ser12*` | 1200 | 35 | CB standalone |
| `baypac-bp1` / `bp2` | `ser12*` | 1200 | 20 | DE-25 adapter |
| `baypac-bp2m` | `ser12*` | 1200 | 20 | HF: use `ser3*` @ 300 |
| `fx614-ser12` / `mx614-ser12` | `ser12*` | 1200 | 20 | TCM3105 successors |
| `pmp-ezpacket-ser12` | `ser12*` | 1200 | 20 | DIY kits |
| `am7911-ser12` | `ser12*` | 1200 | 25–30 | Raise if framing fails |
| `cb-ser12-generic` | `ser12*` | 1200 | 30–35 | Verify pinout |
| `tnc2-ser12-clone` | `ser12*` | 1200 | 20 | Verify pinout |
| `ser12-hdx-fallback` | `ser12*` | 1200 | 20 | `baycom_ser_hdx` → `bcsh0` |

## 300 baud HF

| Catalog ID | mode | baud | txdelay |
|------------|------|------|---------|
| `ser12-300-hf` | `ser3*` | 300 | 30 |
| `baypac-bp2m` (HF) | `ser3*` | 300 | 20–30 |

## kiss-serial

| Catalog ID | kiss_baud | Device |
|------------|-----------|--------|
| `kiss-serial-usb` | 9600 | `/dev/ttyUSB*`, `/dev/ttyACM*` |
| `kiss-serial-rs232` | 9600 | async serial KISS TNC |

No `iobase`/`irq`. USB adapters: [HARDWARE.md](HARDWARE.md).

## Planned (catalog only)

| Catalog ID | driver | mode | baud | iface |
|------------|--------|------|------|-------|
| `baycom-par96` | `baycom_par` | `par96` | 9600 | `bcp0` |
| `baycom-picpar` | `baycom_par` | `picpar` | 9600 | `bcp0` |
| `baypac-bp96a` | `baycom_par` | `par96` | 9600 | `bcp0` |
| `baycom-epp` | `baycom_epp` | `epp` | — | `bce0` |

## Example override

```ini
[modem.hf]
catalog = baypac-bp2m
serial = /dev/ttyS1
mode = ser3*
baud = 300
txdelay = 25
```

## TX delay tuning

1. Start with catalog `txdelay`.
2. Adjust: `baycom_sethdlc bcsf0 <n>` (n × 10 ms).
3. Override in `[modem.<id>]` if needed.

## v0.5.0 on-air gaps

| Item | Status |
|------|--------|
| Dual ser12 offline | Verified |
| BayPac / FX614 / DIY | Supported-by-design |
| 300 baud HF | Documented; RF not tested |
| par96 / picpar / EPP | Planned — no `baycom-pr-ctl` path yet |
