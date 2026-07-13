# Changelog

## [CUR999] — pre-release (current)

**CRDOP-CUR999** — in-house MAX25-SoftModem scaffold inside MAX25-Stack. Pre-release track until **v0.5** ships.

- Product label **CRDOP-CUR999**; version file `CUR999`
- Native modem DSP in development; optional legacy vendor build (`-DCRDOP_VENDOR_ARDOPCF=ON`); **ARDOP-plugin** documented separately
- `max25d` `crdop-tcp` backend, INI scaffold, launcher, HyBBX attach examples

## [0.5.0] — planned (not yet released)

Target first numbered CRDOP release after CUR999 pre-release phase.

- Standalone CRDOP modem (`crdopc`) with native DSP
- Embedded optional `vendor/ardopcf` (MIT) for legacy wire-compat dev builds only
- CB / dual / amateur profiles; Linux and *BSD tested

## [0.1.0-l2-cb] — 2026-07-03

Experimental CB profile bootstrap.

## [0.0.0-bootstrap]

Repository scaffold.
