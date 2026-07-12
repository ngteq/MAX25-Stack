# Changelog

All notable releases of BayCom PR-Stack. Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-07-08

**Stable release.** The stack is ready for everyday operators and HyBBX integrators.

- **Jedermann paths:** CB, HAM, and USB KISS single-modem install with `probe` → `setup` → `start`
- **Connects:** 11 copy-paste incoming/outgoing examples (`listen`, `call`, monitor)
- **HyBBX plugin contract:** KISS symlinks, AX.25 ports, INI schema documented in [PLUGIN.md](docs/PLUGIN.md)
- **Automatic axports:** `setup` and `start` sync `/etc/baycom/axports/axports` from INI
- **Hardware validated:** dual-modem service mode on reference station (kernel 6.18, staged ser12 probe)
- **Operator docs:** GETTING-STARTED, CONNECTS, GLOSSARY, GUIDE, REFERENCE, PLUGIN

## [0.8.5] - 2026-07-08

- Generate `/etc/baycom/axports/axports` from INI on `setup` and `start`
- New `baycom-pr-ctl` commands: `axports apply|show|check`, `listen`, `call`
- Doctor checks for axports sync; optional `config/systemd/baycom-pr.service`
- Offline tests for axports tooling

## [0.7.0] - 2026-07-08

- Operator documentation set: GETTING-STARTED (CB, HAM, USB KISS), CONNECTS, GLOSSARY, PLUGIN
- README and GUIDE refocused on modem owners; dual modem documented as service mode only
- HyBBX attachment points and terminal AX.25 client support documented

## [0.6.5] - 2026-07-08

- Dual-modem hardware validation on reference station (ttyS0 IRQ 4 + ttyS5 IRQ 30)
- Staged dual probe fix: single-instance modprobe exposes `bcsf0`/`bcp0` during probe
- Doctor: resolve `/sbin/modprobe`, treat loaded modules as OK
- Selftest works when installed under `/usr/local/sbin`
- `make install` no longer overwrites existing site INI or catalog

[1.0.0]: https://github.com/ngteq/BayCom_PR-Stack/releases/tag/v1.0.0
[0.8.5]: https://github.com/ngteq/BayCom_PR-Stack/releases/tag/v0.8.5
[0.7.0]: https://github.com/ngteq/BayCom_PR-Stack/releases/tag/v0.7.0
[0.6.5]: https://github.com/ngteq/BayCom_PR-Stack/releases/tag/v0.6.5
