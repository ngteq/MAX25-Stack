# Site-local configuration (not committed)

Operator copies live here. This directory is **gitignored** except this README.

**Never commit** live INI, env, keys, passwords, hostnames, UART inventories, or other site-private data. Public examples stay under `share/**/*.example`.

## Typical files (examples)

| File | Install target |
|------|----------------|
| `max25d.ini` | `/etc/max25/max25d.ini` |
| Serial env (per device) | `/etc/max25/` |
| `bcpr.ini` (BayCom/based / bcpr) | `/etc/max25/max25-bcpr.ini` (or symlink here) |

Fill secrets from `local/passwords.env` (generate with the vault `local-generate-secrets.sh` tool). Do not leave placeholders in live files.

## Deploy (sketch)

```bash
sudo cp local/max25d.ini /etc/max25/max25d.ini
sudo mkdir -p /run/max25
sudo max25d -c /etc/max25/max25d.ini
```

## Terminal (canonical)

```bash
max25-terminal -U /run/max25/modem.sock
# DEVICE from max25d [devices] default — optional override:
#   -d <id>   |   SET DEVICE <id>   |   F10 → 7
```

Prefer `/usr/local/bin/max25-terminal` or `build*/bin/max25-terminal`. Path is **`stacks/terminal/`**, never `stacks/daemon/`.

Unix socket: max25d binds then `chmod 0660`. If the daemon runs as **root**, a non-root client gets connect refused/EACCES — use `sudo max25-terminal …`, or run max25d as the same user/group that owns the terminal.

Site wiring, host roles, and purchase/serial inventory live only in the private research vault — not in this repository.

## bcpr prove-out (workstation)

```bash
# Preferred: max25d auto_start
max25d -c local/max25d.ini
max25-terminal -U /run/max25/modem.sock
# CONNECT → SEND …

# Manual bcpr only when debugging:
sudo ./stacks/max25-bcpr/tools/max25-bcpr-ctl -c /etc/max25/max25-bcpr.ini preflight
sudo ./stacks/max25-bcpr/tools/max25-bcpr-ctl -c /etc/max25/max25-bcpr.ini start
```

`tcp_password` comes from `passwords.env` → `MAX25_TCP_PASSWORD`.
