# Site-local configuration (not committed)

Operator copies live here. This directory is gitignored except this README.

## Site-local — merged MAX25 + HyBBX (TNC only)

| File | Install target |
|------|----------------|
| `max25d.ini` | `/etc/max25/max25d.ini` |
| `hybbx.ini` | `/usr/local/hybbx/hybbx.ini` |
| `tnc2c-serial.env`, `pktnc2-serial.env` | `/etc/max25/` |

**UART:** ttyS4 TNC2C (K24) · ttyS5 PK-TNC2 (K25) — no PC-COM / BayCom on this layout.

**Contract:** MAX25 owns boot-wait / `kiss_on` on serial; HyBBX `kiss_entry=none` attach-only; `[max25] check=yes` probes `:7325`.

### One-time prerequisite

```bash
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
# 1) max25d first — TNC prep + TCP :7325 (releases /dev/tty* in hybbx-host mode)
sudo -u hybbx max25d -c /etc/max25/max25d.ini &
# wait for log: MAX25d ready + hybbx-host: serial released

# 2) HyBBX after max25d ready (or hybbx-start waits up to 120s for :7325)
sudo -u hybbx /usr/local/hybbx/hybbx-start &
```

**Never** start HyBBX before max25d prep on the same `/dev/ttyS*` ports.

**Unix socket:** ensure `/run/max25` exists and is writable (`RuntimeDirectory=max25` in systemd) or use TCP `:7325` only.

HyBBX: **2× packet_radio** (K24 + K25). max25d devices: `tnc2c`, `pktnc2`.

## max25-terminal

```bash
max25-terminal -U /run/max25/modem.sock -d tnc2c
```

## TNC serial env

```bash
cp ../share/max25/serial/tnc2c-serial.env.example tnc2c-serial.env
cp ../share/max25/serial/pktnc2-serial.env.example pktnc2-serial.env
```

## See also

- [docs/LINUX-HOST-SETUP.md](../docs/LINUX-HOST-SETUP.md)
