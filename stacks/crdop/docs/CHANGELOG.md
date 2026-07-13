# Changelog

## [CUR999] — dev track (current)

**CUR999** — internal dev track id for MAX25-SoftModem inside MAX25-Stack v1.0.0. Dev track `CUR999`; ships with MAX25-Stack v1.0.0.

- Dev track id `CUR999` in `$SRC/stacks/crdop/VERSION`
- Native modem DSP in development; optional legacy vendor build (`-DCRDOP_VENDOR_ARDOPCF=ON`); **ARDOP-plugin** documented separately
- `max25d` `crdop-tcp` backend, INI scaffold, launcher, HyBBX attach examples

## [0.5.0] — planned (not yet released)

Target standalone CRDOP v0.5 after v1.0.0 stack ship.

- Standalone CRDOP modem (`crdopc`) with native DSP
- Embedded optional `vendor/ardopcf` (MIT) for legacy wire-compat dev builds only
- CB / dual / amateur profiles; Linux and *BSD tested

## [0.1.0-l2-cb] — 2026-07-03

Experimental CB profile bootstrap.

## [0.0.0-bootstrap]

Repository scaffold.
