# BayCom/based · MAX25-Stack

Public mark: **BayCom/based**. Preferred path: **bcpr** (userspace SER12). Never use kernel `baycom_ser_fdx` as the product path.

## Preferred path: **bcpr**

For Albrecht PC-COM / **BayCom/based** TCM3105-class AFSK hardware, use the **bcpr** MAX25 plugin.

| Item | Value |
|------|--------|
| Plugin | `stacks/bcpr/` · `bcprd` / `bcpr-ctl` |
| Feature | `[features] bcpr = yes` |
| Device | `bcpr-bc0 = bcpr:bc0` |
| Host face | **`max25e0:bc0`** / `bc1` (max 2) |
| Hardware | **BayCom/based** bits↔AFSK + PTT (UART modem-control) — not a TNC |
| Hard law | Real IRQ · exclusive COM lock · max 2 · freeze after INI/autoprobe · no calibrate |

```text
Radio AF/PTT ↔ PC-COM (TCM3105) ↔ UART
                         ↕
                    bcprd (SER12+HDLC)
                         ↕
              KISS PTY ← max25d ← M25/1
```

### Quick start

```bash
# 1) Build
cmake -S . -B build-bcpr -DMAX25_BUILD_BCPR=ON
cmake --build build-bcpr --target bcprd

# 2) Offline dry-run
./build-bcpr/bin/bcprd -c stacks/bcpr/share/bcpr.ini.example --dry-run --once

# 3) Live (owned COM, real IRQ in INI)
sudo cp stacks/bcpr/share/bcpr.ini.example /etc/max25/bcpr.ini
# edit: dry_run=no, serial/iobase/irq to match setserial
sudo ./stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini preflight
sudo ./stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini start

# 4) max25d
# [features] bcpr = yes
# [devices] bcpr-bc0 = bcpr:bc0
# [device.bcpr-bc0] kiss_link=… bcpr_ini=/etc/max25/bcpr.ini
```

Details: [`stacks/bcpr/README.md`](../stacks/bcpr/README.md).

> **Freezes:** SQ-open / RF EMI class still applies on some desktops — see **[BAYCOM-FREEZES.md](BAYCOM-FREEZES.md)**. Do **not** calibrate.

---

## Legacy (optional): kernel baycom-pr

The in-tree `baycom_ser_fdx` / `baycom-pr-ctl` path remains in-tree for reference and older setups. It is **not** the product path for new PC-COM bring-up.

| Feature | Default |
|---------|---------|
| `[features] baycom` | `no` |
| `[features] pccom` | `no` |
| Netdev | `bcsf*` — do not use as MAX25 host face |

If you must use it: `share/baycom/` + [BAYCOM-FREEZES.md](BAYCOM-FREEZES.md). Prefer **bcpr** instead.

## Related

| Goal | Doc |
|------|-----|
| Freeze warning | [BAYCOM-FREEZES.md](BAYCOM-FREEZES.md) |
| bcpr plugin | [stacks/bcpr/README.md](../stacks/bcpr/README.md) |
| Device model | [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) |
