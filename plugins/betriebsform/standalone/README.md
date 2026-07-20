# Operating mode: Standalone

Single-operator packet radio. One TNC or one BayCom modem online. **Default v1 path.**

## Start

```bash
# TNC2C
./scripts/max25-ctl start --mode standalone --hardware tncs --device tnc2c

# BayCom/based SER12 (max25e0 via max25-bcpr) — prefer max25d
# [features] max25_bcpr=yes · max25e0 = max25-bcpr:bc0 — see docs/BAYCOM.md

# max25d (recommended host path)
sudo max25d -c /etc/max25/max25d.ini
```

## HyBBX

Optional. HyBBX opens serial or KISS **after** MAX25 prep (boot-wait, driver load).

INI: `share/hybbx/standalone.ini.example` · Contract: [docs/HYBBX.md](../../docs/HYBBX.md)
