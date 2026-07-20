# BayCom/based configuration (MAX25)

Public mark: **BayCom/based**. Product path: **max25-bcpr** only.

**Status: not usable** (default build OFF). Experimental: `-DMAX25_BUILD_MAX25_BCPR=ON`.

Device id: **`max25e0`** (forks `max25e0:bcN`). Defaults: `ipv4=127.0.0.25/8`, `ipv6=::25/128`.

```bash
# after experimental opt-in build
./build-max25-bcpr/bin/max25-bcprd -c stacks/max25-bcpr/share/max25-bcpr.ini.example --dry-run --once
sudo cp stacks/max25-bcpr/share/max25-bcpr.ini.example /etc/max25/max25-bcpr.ini
sudo stacks/max25-bcpr/tools/max25-bcpr-ctl -c /etc/max25/max25-bcpr.ini preflight
```

See [docs/BAYCOM.md](../../docs/BAYCOM.md). Freeze warning: [docs/BAYCOM-FREEZES.md](../../docs/BAYCOM-FREEZES.md).
