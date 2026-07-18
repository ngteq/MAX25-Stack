# Site-local configuration (not committed)

Operator copies live here. This directory is gitignored except this README.

## This host (AX25SRV) — TNCs only

| File | Install target |
|------|----------------|
| `max25d.ini` | `/etc/max25/max25d.ini` |
| `hybbx.ini` | `/usr/local/hybbx/hybbx.ini` |
| `tnc2c-serial.env`, `pktnc2-serial.env` | `/etc/max25/` |

| Device | Path | max25d id |
|--------|------|-----------|
| TNC2C | `/dev/ttyS4` | `tnc2c` — ExSys/Oxford card [257223837752](https://www.ebay.de/itm/257223837752) |
| PK-TNC2 | `/dev/ttyS5` | `pktnc2` — same card |
| TNC7multi (planned) | TBD after ExSys / install | TBD |

**Planned:** 3rd TNC (TNC7multi) + **2× ExSys PCIe** serial cards (2 ports each). **No PC-COM / BayCom SER12 on this host.**

`baycom-pr.ini` in this folder = **template only** for the future PC-COM Secondary host — do **not** install on AX25SRV.

### Deploy (this host)

```bash
sudo cp local/max25d.ini /etc/max25/max25d.ini
sudo cp local/tnc2c-serial.env /etc/max25/tnc2c-serial.env
sudo cp local/pktnc2-serial.env /etc/max25/pktnc2-serial.env
sudo mkdir -p /run/max25 && sudo chown hybbx:hybbx /run/max25
sudo -u hybbx max25d -c /etc/max25/max25d.ini
```

### Terminal

```bash
max25-terminal -U /run/max25/modem.sock -d tnc2c
# or -d pktnc2
```

### Future PC-COM host

1. Install MAX25 + `local/baycom-pr.ini` → `/etc/baycom/baycom-pr.ini` (verify iobase/irq)
2. `max25d` with `baycom-ser12 = baycom:a` only (no dual BayCom + TNC on same machine until stable)
3. Bring-up **only** via max25d / `max25-ctl` — not raw `modprobe`
