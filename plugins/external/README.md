# External optional plugins

**CRDOP (CB/AR Digital Open Protocol — MAX25-SoftModem)** is a **MAX25-Stack standard** — built and installed by default (`MAX25_BUILD_CRDOP=ON`). See `plugins/devices/soft-crdop/`.

This folder documents plugins that are **optional** and **external** to MAX25 releases:

| Item | Status |
|------|--------|
| **ARDOP** (third-party modem / ardopcf wire format) | Optional attach only — never shipped |
| Legacy `vendor/ardopcf` build | Dev-only: `-DCRDOP_VENDOR_ARDOPCF=ON` when tree present locally |

## ARDOP optional attach

MAX25 does **not** ship ARDOP code or binaries. For operators who run a **third-party ARDOP** implementation instead of native MAX25-SoftModem:

1. Install and run external ARDOP host/modem (not provided by MAX25).
2. Set `ardop_compat = true` in `[device.soft-crdop]` (or `max25d.ini`).
3. Point `max25d` `soft-crdop` device at TCP :8515/:8516 (ARDOP wire-compatible host interface).

Registry metadata: [ardop/plugin.yaml](ardop/plugin.yaml).

## Not external

| Item | Role |
|------|------|
| **CRDOP / MAX25-SoftModem** | In-house standard — `MAX25_BUILD_CRDOP=ON` (default) |
| `stacks/crdop/` | In-house subproject — INI, launcher, native M25 host, docs |
| `max25d` `crdop-tcp` backend | Standard integration (native M25/KISS by default) |
