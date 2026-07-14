# BayCom / PC-COM · MAX25-Stack 1.5.0

Kernel BayCom SER12 lifecycle — single PC-COM default, dual modem opt-in.

## Device matrix

| Device id | Hardware | HyBBX plugin |
|-----------|----------|--------------|
| `baycom-ser12` | SER12 / PC-COM on 8250 UART | `baycom` |
| deferred | `baycom-par96`, `baycom-kiss` | — |

## v1.5.0 feature gate matrix

| Item | Default |
|------|---------|
| `[features] baycom` | `no` in INI examples |
| `[features] pccom` | `no` in INI examples |
| Enable | set `baycom=yes` in INI + run setup |

## Stack path matrix

```
Radio ← UART ← baycom-pr-ctl (kernel) ← KISS PTY ← max25d ← M25/1 / HyBBX
```

## Start matrix

| Step | Command |
|------|---------|
| INI | `share/baycom/baycom-pr.pccom-ttyS0-only.ini.example` |
| Setup | `baycom-pr-ctl -c /etc/baycom/baycom-pr.ini setup` |
| Start | `max25-ctl start --hardware modems --device baycom-ser12` |
| Netdev | `bcsf0` (SER12*) |

## When to use matrix

| Use BayCom when | Use TNC when |
|-----------------|--------------|
| PC-COM / SER12 on real 8250 UART | TNC2C, PK-TNC2, USB serial KISS |
| Linux `baycom_ser_fdx` path | Boot-wait + firmware KISS |

## Related

| Goal | Doc |
|------|-----|
| HyBBX attach | [HYBBX.md](HYBBX.md) |
| Device model | [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) |
