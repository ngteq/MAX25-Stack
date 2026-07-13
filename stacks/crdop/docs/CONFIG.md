# Configuration

`scripts/crdopc` reads INI → starts native `audio-dummyd` (M25/KISS host) by default.

When `[compat] ardop_compat = yes`, launcher uses **ARDOP-plugin** mode and requires `CRDOP_BIN` pointing to an ARDOP-capable host binary.

## INI search order

1. `$CRDOP_INI`
2. `~/.config/crdop/crdop.ini`
3. `share/crdop.ini.example`

Templates: `share/crdop.ini.example` · `share/crdop-dual.ini.example` · `share/crdop-amateur.ini.example`

## Keys

### `[profile]`

| Key | Default | Values |
|-----|---------|--------|
| `radio_profile` | `cb` | `cb` · `dual` · `amateur` |

### `[modem]`

| Key | Default | Notes |
|-----|---------|-------|
| `arq_bandwidth` | profile | `500MAX` (cb/dual) · `1000MAX` (amateur) |
| `duplex` | `half` | `half` · `full` (`full` → `EXTRADELAY 0`) |
| `extra_delay_ms` | _(auto)_ | Override delay; empty = profile default |

### `[host]` · `[mycall]` · `[audio]`

| Section | Key | Default | Notes |
|---------|-----|---------|-------|
| host | `port` | `8515` | TCP control |
| mycall | `call` | `NOCALL-0` | On-air ID |
| audio | `backend` | `alsa-kernel` | Kernel ALSA only — see [AUDIO-ARCHITECTURE.md](AUDIO-ARCHITECTURE.md) |
| audio | `no_pulse` | `yes` | Reject PulseAudio/PipeWire pseudo devices |
| audio | `capture` | _(required)_ | e.g. `hw:1,0` from `arecord -l` |
| audio | `playback` | _(required)_ | e.g. `hw:1,0` from `aplay -l` |
| audio | `sample_rate` | modem default | Hz |
| audio | `period_frames` | auto | Buffer tuning |

### `[compat]`

| Key | Default | Notes |
|-----|---------|-------|
| `ardop_compat` | `no` | `yes` = **ARDOP-plugin** wire mode (`CRDOP_BIN` for launcher) |

**No PulseAudio** in the production path. The **MAX25 sound-proxy** opens ALSA directly; `scripts/crdopc` clears Pulse/PipeWire session env when `no_pulse=yes`.

## Environment

| Variable | Purpose |
|----------|---------|
| `CRDOP_INI` | Config file path |
| `CRDOP_BIN` | Path to ARDOP host binary (ARDOP-plugin mode only) |

Examples: [EXAMPLES.md](EXAMPLES.md)
