# Device: BayCom SER12 (legacy kernel)

**Preferred PC-COM path:** **bcpr** userspace — see [`stacks/bcpr/README.md`](../../../stacks/bcpr/README.md) and [docs/BAYCOM.md](../../../docs/BAYCOM.md).

This plugin id (`baycom-ser12`) remains for the **legacy** `baycom_ser_fdx` / `baycom-pr-ctl` path. Not recommended for new bring-up.

```bash
# Prefer:
#   [features] bcpr=yes · bcpr-bc0 = bcpr:bc0
# Legacy only:
./scripts/max25-ctl start --hardware modems --device baycom-ser12
```
