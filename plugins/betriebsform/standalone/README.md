# Operating mode: Standalone

Single-operator packet radio. One TNC or one BayCom modem online. **Default v1 path.**

## Start

```bash
# TNC2C
./scripts/max25-ctl start --mode standalone --hardware tncs --device tnc2c

# BayCom SER12
./scripts/max25-ctl start --mode standalone --hardware modems --device baycom-ser12

# max25d (recommended edge path)
sudo max25d -c /etc/max25/max25d.ini
```

## HyBBX

Optional. HyBBX opens serial or KISS **after** MAX25 prep (boot-wait, driver load).

INI: `share/hybbx/standalone.ini.example` · Contract: [docs/HYBBX.md](../../docs/HYBBX.md)
