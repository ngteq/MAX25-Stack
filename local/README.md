# Site-local configuration (not committed)

Operator copies live here. This directory is gitignored except this README.

## Site-local — merged MAX25 + HyBBX

| File | Install target |
|------|----------------|
| `max25d.ini` | `/etc/max25/max25d.ini` |
| `hybbx.ini` | `/usr/local/hybbx/hybbx.ini` |
| `tnc2c-serial.env`, `pktnc2-serial.env` | `/etc/max25/` |
| `baycom-pr.ini` | `/etc/baycom/baycom-pr.ini` |

**UART:** ttyS0 BayCom · ttyS4 TNC2C (K24) · ttyS5 PK-TNC2 (K25)

**Contract:** MAX25 owns boot-wait / `kiss_on` on serial; HyBBX `kiss_entry=none` attach-only; `[max25] check=yes` probes `:7325`.

### One-time prerequisite

```bash
sudo cp local/baycom-pr.ini /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini preflight
sudo cp local/tnc2c-serial.env /etc/max25/tnc2c-serial.env
sudo cp local/pktnc2-serial.env /etc/max25/pktnc2-serial.env
sudo mkdir -p /run/max25 && sudo chown hybbx:hybbx /run/max25
```

### Deploy configs

```bash
sudo cp local/max25d.ini /etc/max25/max25d.ini
sudo cp local/hybbx.ini /usr/local/hybbx/hybbx.ini
```

### Start order (cold boot)

```bash
# Modems powered → then e.g. /home/hybbx/start-hybbx.sh:
#   pktnc2-boot-wait → tnc2c-boot-wait → max25d → hybbx-start
sudo -u hybbx max25d -c /etc/max25/max25d.ini &
# wait for 127.0.0.1:7325
sudo -u hybbx /usr/local/hybbx/hybbx-start &
```

HyBBX today: **2× packet_radio** (K24+K25). Third radio (BayCom ttyS0) is prepped by max25d; enable `[transport.baycom1]` in `hybbx.ini` when ready (`baycom=yes`, plugin build ON).

## BayCom (PC-COM kernel modem — single UART on ttyS0)

See `baycom-pr.ini` or shipped example:

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
```

## max25-terminal

```bash
max25-terminal -U /run/max25/modem.sock -d tnc2c
```

Devices: `tnc2c`, `pktnc2`, `baycom-ser12`.

## TNC serial env

```bash
cp ../share/max25/serial/tnc2c-serial.env.example tnc2c-serial.env
cp ../share/max25/serial/pktnc2-serial.env.example pktnc2-serial.env
```

## See also

- [docs/BAYCOM.md](../docs/BAYCOM.md)
- [docs/LINUX-HOST-SETUP.md](../docs/LINUX-HOST-SETUP.md)
- HyBBX research copy: `~/Code/0-RESEARCHES/hybbx/ax25srv-un1tme.ini`
