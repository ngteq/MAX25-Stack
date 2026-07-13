# CRDOP — MAX25-SoftModem

**CRDOP** = stack acronym for **MAX25-SoftModem** (device id `soft-crdop`).

Sound-card software modem subproject of MAX25-Stack.

**Stack version:** MAX25-Stack **v1.0.0** · **Dev track:** `CUR999` in `$SRC/stacks/crdop/VERSION`.

**Canonical project rule:** [docs/CRDOP.md](../../docs/CRDOP.md)  
**License:** GNU GPL v3 — [LICENSE](LICENSE)

## Summary

| | |
|---|---|
| Type | MAX25-Stack **subproject** (`stacks/crdop/`) |
| Interface | Sound card IN/OUT → kernel ALSA → MAX25 sound-proxy |
| Goal | **AX.25 / KISS / TNC / modem compatible** software modem |
| Mission | **Hardware solutions** (primary) + **pure software** on computers |
| Build | Default ON (`MAX25_BUILD_CRDOP=ON`) |

Read [docs/CRDOP.md](../../docs/CRDOP.md) before changing modem, audio, or plugin code.

## Technical docs

**Index:** [docs/INDEX.md](docs/INDEX.md)

| Doc | Topic |
|-----|--------|
| [docs/MAX25-USAGE.md](docs/MAX25-USAGE.md) | MAX25-Stack operator guide |
| [docs/DEVELOPER.md](docs/DEVELOPER.md) | Source tree, modules, tests |
| [docs/HARDWARE-INTERFACE.md](docs/HARDWARE-INTERFACE.md) | Generic radio interface spec |
| [docs/SOFTMODEM.md](docs/SOFTMODEM.md) | Baud, duplex, acoustic AX.25 |
| [docs/AUDIO-ARCHITECTURE.md](docs/AUDIO-ARCHITECTURE.md) | Kernel ALSA only, no PulseAudio |
| [docs/CONFIG.md](docs/CONFIG.md) | INI / launcher |
| [ROADMAP.md](ROADMAP.md) | P0/P1/P2 milestones |
