# BayCom/based · MAX25-Stack

Public mark: **BayCom/based**. Product path: **bcpr** (userspace SER12). Kernel `baycom_ser_fdx` / `baycom-pr` is **removed** from this tree (2026-07-18).

## Product path: **bcpr**

For Albrecht PC-COM / **BayCom/based** TCM3105-class AFSK hardware, use the **bcpr** MAX25 plugin.

| Item | Value |
|------|--------|
| Plugin | `stacks/bcpr/` · `bcprd` / `bcpr-ctl` |
| Feature | `[features] bcpr = yes` |
| Device | `max25e0 = bcpr:bc0` (backend tag; product id is **`max25e0`**) |
| Host face | **`max25e0`** (forks `max25e0:bcN` only when multi-dev) |
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

# 4) max25d (preferred: auto_start owns bcprd)
sudo max25d -c /etc/max25/max25d.ini
# or: max25d -c local/max25d.ini

# 5) terminal (default device from INI — no -d required)
max25-terminal -U /run/max25/modem.sock
# CONNECT → SEND …
```

With `auto_start`, restart **max25d only** — do not recycle `bcprd` outside max25d.

Details: [`stacks/bcpr/README.md`](../stacks/bcpr/README.md).

**TX/RX test:** unified entry [TX-RX-TEST.md](TX-RX-TEST.md) (`scripts/tx-rx-test.sh` · L0 offline in CI; `--live` / `--tx` for PC-COM).

> **Freezes:** SQ-open / RF EMI class still applies on some desktops — see **[BAYCOM-FREEZES.md](BAYCOM-FREEZES.md)**. Do **not** calibrate.

---

## Legacy kernel baycom-pr (removed)

`stacks/baycom-pr/`, kernel SER12/PAR96 plugins, and dual-kernel INI examples were archived out of this repository.

Frozen copy (MASTER vault, not shipped): `archives/legacy/max25-stack-baycom-kernel-compa/`.

Do **not** load `baycom_ser_fdx` for product bring-up.

## Related

| Goal | Doc |
|------|-----|
| Freeze warning | [BAYCOM-FREEZES.md](BAYCOM-FREEZES.md) |
| bcpr plugin | [stacks/bcpr/README.md](../stacks/bcpr/README.md) |
| Device model | [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) |
