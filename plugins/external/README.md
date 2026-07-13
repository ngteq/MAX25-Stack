# Optional plugins — ARDOP-plugin

**CRDOP (MAX25-SoftModem)** is the **MAX25-Stack standard** modem — built and installed by default (`MAX25_BUILD_CRDOP=ON`). See `plugins/devices/soft-crdop/`.

## ARDOP-plugin

| Item | Detail |
|------|--------|
| **Plugin** | **ARDOP-plugin** — optional MAX25-Stack plugin |
| **Registry** | [ardop/plugin.yaml](ardop/plugin.yaml) |
| **Enable** | `ardop_compat = true` on `soft-crdop` or in `crdop.ini` `[compat]` |
| **Ports** | TCP :8515 (control) / :8516 (data) |
| **Standard alternative** | Native CRDOP / M25-KISS host (default) |

### Using ARDOP-plugin

1. Install and run an ARDOP-capable modem host on the operator machine.
2. Set `ardop_compat=true` in `max25d.ini` `[device.soft-crdop]` or CRDOP INI.
3. Point `max25d` `soft-crdop` at TCP :8515/:8516.

See [ardop/README.md](ardop/README.md) and [stacks/crdop/docs/MAX25-USAGE.md](../../stacks/crdop/docs/MAX25-USAGE.md).

## MAX25 standard (not ARDOP-plugin)

| Item | Role |
|------|------|
| **CRDOP / MAX25-SoftModem** | In-house standard — `MAX25_BUILD_CRDOP=ON` (default) |
| `stacks/crdop/` | CRDOP subproject — INI, launcher, native M25 host, docs |
| `max25d` `crdop-tcp` backend | Standard integration (native M25/KISS by default) |
