# Configuration

`scripts/crdopc` reads INI → starts native `audio-dummyd` (M25/KISS host).

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

**No PulseAudio** in the production path. The **MAX25 sound-proxy** opens ALSA directly; `scripts/crdopc` clears Pulse/PipeWire session env when `no_pulse=yes`.

## Environment

| Variable | Purpose |
|----------|---------|
| `CRDOP_INI` | Config file path |

Examples: [EXAMPLES.md](EXAMPLES.md)
