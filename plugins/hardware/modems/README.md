# Hardware: Modems

BayCom/based SER12 — userspace **bcpr** (`stacks/bcpr/`). USB/async KISS — `plugins/devices/baycom-kiss/`.

Kernel `baycom-pr` / `baycom_ser_fdx` removed from this tree (2026-07-18).

## HyBBX

Optional BayCom/based path is via MAX25 (`bcpr` → KISS). See [docs/BAYCOM.md](../../docs/BAYCOM.md) and [docs/HYBBX.md](../../docs/HYBBX.md).

| Path | Role |
|------|------|
| `stacks/bcpr/` | SER12 userspace (PC-COM class) |
| `baycom-kiss` | USB/async KISS TNC firmware |

## Quick start

```bash
cmake -S . -B build-bcpr -DMAX25_BUILD_BCPR=ON
cmake --build build-bcpr
# then: docs/BAYCOM.md (bcpr-ctl / max25d [features] bcpr=yes)
```

## Docs

- [docs/BAYCOM.md](../../docs/BAYCOM.md)
- [stacks/bcpr/README.md](../../stacks/bcpr/README.md)
