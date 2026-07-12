# Site-local configuration (not committed)

Operator copies live here. This directory is gitignored except this README.

## BayCom (PC-COM kernel modem — single UART on ttyS0)

AX25SRV has **one PC-COM** on `/dev/ttyS0`. `/dev/ttyS5` is PK-TNC2 (HyBBX), not a second BayCom modem.

```bash
cp ../share/baycom/baycom-pr.pccom-ttyS0-only.ini.example baycom-pr.ini
# Edit callsign, verify iobase/irq with: setserial -g /dev/ttyS0
sudo cp baycom-pr.ini /etc/baycom/baycom-pr.ini
sudo baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup
```

Or install the shipped example directly:

```bash
sudo cp share/baycom/baycom-pr.pccom-ttyS0-only.ini.example /etc/baycom/baycom-pr.ini
```

## max25d

```bash
cp ../share/max25/max25d.ini.edge.example max25d.ini
# For BayCom: hardware=modems, device=baycom-ser12 — see docs/BAYCOM.md
sudo cp max25d.ini /etc/max25/max25d.ini
```

Optional source ban list (M25/1 `BAN`/`UNBAN`/`BANS`; see `stacks/daemon/README.md`):

```bash
sudo touch /etc/max25/bans.txt
# Uncomment bans_file in max25d.ini [modem] section
```

## HyBBX Secondary edge (Secondary)

```bash
cp ../share/hybbx/baycom-ser12-edge.ini.example hybbx-pccom.ini
# TNC2C: stacks/tncs/hybbx-tnc2c.ini or share/hybbx/tnc2c-edge.ini.example
# Merge into HyBBX hybbx.ini after MAX25 prep
```

## TNC serial env

```bash
cp ../share/max25/serial/tnc2c-serial.env.example tnc2c-serial.env
cp ../share/max25/serial/pktnc2-serial.env.example pktnc2-serial.env
```

## See also

- [docs/BAYCOM.md](../docs/BAYCOM.md) — canonical BayCom start path
- [share/baycom/README.md](../share/baycom/README.md) — shipped INI examples
- [docs/LINUX-EDGE-SETUP.md](../docs/LINUX-EDGE-SETUP.md) — edge node setup
