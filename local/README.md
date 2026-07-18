# Site-local configuration (not committed)

Operator copies live here. This directory is **gitignored** except this README.

**Never commit** live INI, env, keys, passwords, hostnames, UART inventories, or other site-private data. Public examples stay under `share/**/*.example`.

## Typical files (examples)

| File | Install target |
|------|----------------|
| `max25d.ini` | `/etc/max25/max25d.ini` |
| Serial env (per device) | `/etc/max25/` |
| `baycom-pr.ini` (if used) | `/etc/baycom/baycom-pr.ini` |

Fill secrets from `local/passwords.env` (generate with the vault `local-generate-secrets.sh` tool). Do not leave placeholders in live files.

## Deploy (sketch)

```bash
sudo cp local/max25d.ini /etc/max25/max25d.ini
# copy device serial env files as needed
sudo mkdir -p /run/max25
sudo -u hybbx max25d -c /etc/max25/max25d.ini
```

## Terminal

```bash
max25-terminal -U /run/max25/modem.sock -d <device_id>
```

Site wiring, host roles, and purchase/serial inventory live only in the private research vault — not in this repository.
