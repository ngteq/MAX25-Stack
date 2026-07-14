# Optional plugins — ARDOP-plugin

**CRDOP (MAX25-SoftModem)** is the **MAX25-Stack standard** modem — built and installed by default (`MAX25_BUILD_CRDOP=ON`). See `plugins/devices/soft-crdop/`.

## ARDOP-plugin

| Item | Detail |
|------|--------|
| **Plugin** | **ARDOP-plugin** — optional registry for third-party ARDOP host wire |
| **Registry** | [ardop/plugin.yaml](ardop/plugin.yaml) |
| **CRDOP coupling** | **None** — ARDOP is not enabled via `soft-crdop` or `crdop.ini` |
| **Standard alternative** | Native CRDOP / M25-KISS host (default) |

### Using ARDOP-plugin

1. Install and run an ARDOP-capable modem host on the operator machine (third-party software).
2. Attach HyBBX or another consumer per that ARDOP host's documentation.
3. Keep CRDOP on native M25/KISS — do not mix ARDOP wire mode into CRDOP configs.

See [ardop/README.md](ardop/README.md).

## MAX25 standard (not ARDOP-plugin)

| Item | Role |
|------|------|
| **CRDOP / MAX25-SoftModem** | In-house standard — `MAX25_BUILD_CRDOP=ON` (default) |
| `stacks/crdop/` | CRDOP subproject — INI, launcher, native M25 host, docs |
| `max25d` `crdop-tcp` backend | Standard integration (native M25/KISS) |
