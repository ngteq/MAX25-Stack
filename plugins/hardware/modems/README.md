# Hardware: Modems

BayCom/based SER12 — userspace **bcpr** (`stacks/max25-bcpr/`). USB/async KISS — `plugins/devices/baycom-kiss/`.

Kernel `baycom-pr` / `baycom_ser_fdx` removed from this tree (2026-07-18).

## HyBBX

Optional BayCom/based path is via MAX25 (`bcpr` → KISS). See [docs/BAYCOM.md](../../docs/BAYCOM.md) and [docs/HYBBX.md](../../docs/HYBBX.md).

| Path | Role |
|------|------|
| `stacks/max25-bcpr/` | SER12 userspace (PC-COM class) |
| `baycom-kiss` | USB/async KISS TNC firmware |

## Quick start

```bash
cmake -S . -B build-max25-bcpr -DMAX25_BUILD_MAX25_BCPR=ON
cmake --build build-max25-bcpr
# then: docs/BAYCOM.md (max25-bcpr-ctl / max25d [features] max25_bcpr=yes)
```

## Docs

- [docs/BAYCOM.md](../../docs/BAYCOM.md)
- [stacks/max25-bcpr/README.md](../../stacks/max25-bcpr/README.md)
