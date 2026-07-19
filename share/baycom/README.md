# BayCom/based configuration (MAX25)

Public mark: **BayCom/based**. Product path: **bcpr** only.

```bash
./build-bcpr/bin/bcprd -c stacks/bcpr/share/bcpr.ini.example --dry-run --once
sudo cp stacks/bcpr/share/bcpr.ini.example /etc/max25/bcpr.ini
sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini preflight && \
  sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini start
```

max25d: `[features] bcpr=yes` · `max25e0 = bcpr:bc0` — see `stacks/bcpr/README.md`.

Kernel `baycom-pr` INI examples were removed from this tree (2026-07-18). Frozen archive: MASTER vault `archives/legacy/max25-stack-baycom-kernel-compa/`.

Freeze warning: [docs/BAYCOM-FREEZES.md](../../docs/BAYCOM-FREEZES.md). No calibrate on interactive desktops.
