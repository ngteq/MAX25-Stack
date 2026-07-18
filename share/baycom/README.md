# BayCom configuration examples (MAX25)

## Preferred for PC-COM: **bcpr** (userspace)

```bash
# Example + dry-run
./build-bcpr/bin/bcprd -c stacks/bcpr/share/bcpr.ini.example --dry-run --once
# Live INI
sudo cp stacks/bcpr/share/bcpr.ini.example /etc/max25/bcpr.ini
sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini preflight && \
  sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini start
```

max25d: `[features] bcpr=yes` · `bcpr-bc0 = bcpr:bc0` — see `stacks/bcpr/README.md`.

---

## Legacy: kernel BayCom (`baycom-pr`)

Templates under this directory are for the **optional / legacy** `baycom_ser_fdx` path. **Do not** use as the default PC-COM product path. Prefer **bcpr**.

| File | Role |
|------|------|
| [`baycom-pr.pccom-ttyS0-only.ini.example`](baycom-pr.pccom-ttyS0-only.ini.example) | Legacy single SER12 on ttyS0 |
| Dual examples | Legacy multi-modem — not for new max25d hosts |

Freeze warning: [docs/BAYCOM-FREEZES.md](../../docs/BAYCOM-FREEZES.md). No calibrate on interactive desktops.
