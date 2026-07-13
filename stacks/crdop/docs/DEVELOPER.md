# CRDOP developer guide

**CRDOP** = **MAX25-SoftModem**. In-house GPLv3 sound-card modem (`stacks/crdop/`). Project rule: [docs/CRDOP.md](../../../docs/CRDOP.md).

---

## Source tree

```
stacks/crdop/
├── lib/                    # Native DSP (Python — leads validation)
│   ├── bell202_line_code.py
│   ├── afsk_modulator.py
│   ├── afsk_demodulator.py
│   ├── hdlc_codec.py
│   ├── sound_proxy.py
│   ├── m25_host_protocol.py
│   ├── acoustic_engine.py
│   └── test_bell202_line_code.py
├── include/crdop/          # C API scaffold (future native binary)
│   ├── sound_proxy.h
│   └── version.h
├── tools/
│   ├── audio-dummyd.py     # M25 host TCP daemon
│   └── max25-signal-sniffer.py
├── scripts/
│   ├── crdopc              # Launcher → audio-dummyd by default
│   ├── build-crdop.sh
│   └── install-crdop.sh
├── share/                  # crdop.ini.example (+ dual, amateur)
├── cmake/                  # Platform, vendor (dev-only), tests
├── docs/                   # This tree
├── ROADMAP.md
└── CMakeLists.txt
```

**Daemon integration:** `stacks/daemon/device_backends.py` → `CrdopTcpBackend` (`soft-crdop`), `AudioDummyBackend` (`audio-dummy`).

**AX.25 codec:** `stacks/daemon/ax25_codec.py` — shared with on-air framing in `acoustic_engine.py`.

---

## Module map

| Module | Layer | Responsibility |
|--------|-------|----------------|
| `bell202_line_code.py` | Line code | Bell 202 frequency-toggle: bit 0 → tone change; mark 1200 Hz / space 2200 Hz |
| `afsk_modulator.py` | PHY TX | Continuous-phase AFSK PCM @ configurable sample rate (default 48 kHz) |
| `afsk_demodulator.py` | PHY RX | Per-symbol Goertzel demod (1200 baud class) |
| `hdlc_codec.py` | Framing | HDLC flags `0x7E`, bit-stuffing, CRC-16-CCITT |
| `sound_proxy.py` | Audio I/O | ALSA capture/playback via `arecord`/`aplay`; buffer config |
| `m25_host_protocol.py` | Host | TCP ctrl (:8515) + data (:8516); M25-family + KISS-semantics |
| `acoustic_engine.py` | Bench | Full path: AX.25 UI → HDLC → AFSK → demod → parse; loopback self-test |

**Host vs on-air:** `m25_host_protocol.py` carries AX.25 UI on the data port **without** HDLC wrapping. `acoustic_engine.encode_ax25_ui()` builds full on-air HDLC + AFSK for RF/audio output.

**Not yet in `lib/`:** G3RUH scrambler/FSK (P1), 300 baud HF AFSK (P2), optional short-block FEC.

---

## Running tests

### MAX25-Stack (recommended)

```bash
./scripts/build.sh
cmake --build build --target max25_test          # all offline tests
cmake --build build --target max25_daemon_smoke  # daemon + CRDOP subset
```

CRDOP-related tests in `max25_daemon_smoke`:

| Test file | What it checks |
|-----------|----------------|
| `stacks/crdop/lib/test_bell202_line_code.py` | Bell 202 encode/decode round-trip |
| `stacks/daemon/test_crdop_backend.py` | `CrdopTcpBackend` attach, TX, `ardop_compat` flag |
| `stacks/daemon/test_audio_dummy_backend.py` | `audio-dummy` loopback backend |
| `stacks/daemon/test_multi_device.py` | Multi-device registry incl. `soft-crdop` |

### Direct (no CMake)

```bash
python3 stacks/crdop/lib/test_bell202_line_code.py
python3 stacks/daemon/test_crdop_backend.py
python3 stacks/daemon/test_audio_dummy_backend.py
```

### Sniffer loopback (no audio hardware)

```bash
python3 stacks/crdop/tools/max25-signal-sniffer.py --loopback
# or after install:
max25-signal-sniffer --loopback
```

Exit 0 when loopback decode produces AX.25 UI lines.

### audio-dummyd bench

```bash
python3 stacks/crdop/tools/audio-dummyd.py --ctrl-port 8515 --data-port 8516
# Terminal probe (separate shell):
max25-terminal -H 127.0.0.1 -P 8515
```

### Standalone CRDOP vendor tests (dev-only)

When built with `-DCRDOP_VENDOR_ARDOPCF=ON` and cmocka installed:

```bash
./scripts/build-crdop.sh
CRDOP_BUILD_TESTS=ON ./scripts/test-all.sh
```

Vendor tree is **never** installed in MAX25 releases.

---

## Extending the modem

### Add a modulation mode

1. Add PHY module under `lib/` (e.g. `g3ruh_fsk.py`).
2. Wire into `acoustic_engine.py` — select by `baud` / `modulation` parameter.
3. Extend `crdop.ini` `[modem]` keys in `share/crdop.ini.example` and [CONFIG.md](CONFIG.md).
4. Add unit tests beside the module (`test_*.py`).
5. Update [ROADMAP.md](../ROADMAP.md) implementation status table.

### Extend host protocol

1. Edit `m25_host_protocol.py` — keep ctrl/data port split.
2. Mirror changes in `stacks/daemon/device_backends.py` (`CrdopTcpBackend`).
3. Document in [PROTOCOL.md](PROTOCOL.md).
4. Add cases to `test_crdop_backend.py`.

### C port path

`include/crdop/sound_proxy.h` is the C ABI target. Python `lib/` leads until acoustic bench gates close; then port validated algorithms to native `crdopc` binary.

---

## Build modes

| Mode | CMake flag | Output |
|------|------------|--------|
| **MAX25-Stack (default)** | `MAX25_BUILD_CRDOP=ON` | `bin/crdop`, `bin/audio-dummyd`, `bin/max25-signal-sniffer`, `share/crdop/` |
| **MAX25 without CRDOP** | `-DMAX25_BUILD_CRDOP=OFF` | No CRDOP install artifacts |
| **Standalone CRDOP** | `stacks/crdop/scripts/build-crdop.sh` | Same scaffold; optional vendor `crdopc` with `-DCRDOP_VENDOR_ARDOPCF=ON` |
| **Dev vendor ARDOP** | `-DCRDOP_VENDOR_ARDOPCF=ON` | Legacy ardopcf binary — local only, never released |

### Install paths (MAX25 `cmake --install`)

| Artifact | Destination |
|----------|-------------|
| `crdop` (launcher) | `${CMAKE_INSTALL_PREFIX}/bin/` |
| `audio-dummyd`, `max25-signal-sniffer` | `${CMAKE_INSTALL_PREFIX}/bin/` |
| `crdop.ini.example`, `lib/*.py`, `VERSION` | `${CMAKE_INSTALL_PREFIX}/share/crdop/` |

---

## Dependencies

| Component | Requirement |
|-----------|-------------|
| Runtime | Python 3, ALSA utils (`arecord`/`aplay`) on Linux |
| Build | CMake ≥ 3.16 |
| Audio | `libasound` — kernel ALSA direct opens only |
| Tests | None beyond Python 3 (cmocka optional for vendor C tests) |

---

## Conventions

- **English** for all shipped docs and user-facing strings.
- **No PulseAudio / PipeWire** in production audio path.
- **ARDOP-plugin** wire format: optional via `ardop_compat=true` — see [plugins/external/ardop/README.md](../../../plugins/external/ardop/README.md).
- Baud ceiling: **19200** (P1 G3RUH direct FSK). Above that: out of scope.

---

## Related

| Doc | Topic |
|-----|--------|
| [MAX25-USAGE.md](MAX25-USAGE.md) | Operator workflow in MAX25-Stack |
| [HARDWARE-INTERFACE.md](HARDWARE-INTERFACE.md) | Radio interface spec for builders |
| [AUDIO-ARCHITECTURE.md](AUDIO-ARCHITECTURE.md) | Sound-proxy design |
| [ROADMAP.md](../ROADMAP.md) | P0/P1/P2 phases and module status |
