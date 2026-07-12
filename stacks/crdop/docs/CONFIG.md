# Configuration

`scripts/crdopc` reads INI → builds ARDOP `-H` host command string.

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

| Section | Key | Default |
|---------|-----|---------|
| host | `port` | `8515` |
| mycall | `call` | `NOCALL-0` |
| audio | capture / playback | passed as CLI args after port |

## Environment

| Variable | Purpose |
|----------|---------|
| `CRDOP_INI` | Config file path |
| `CRDOP_BIN` | Path to `crdopc` binary |

Examples: [EXAMPLES.md](EXAMPLES.md)
