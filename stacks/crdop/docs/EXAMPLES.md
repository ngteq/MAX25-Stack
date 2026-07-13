# Examples

MAX25-Stack integration (plugins, `max25d`, terminal): [MAX25-USAGE.md](MAX25-USAGE.md).

## Build

```bash
./scripts/build-crdop.sh
CC=clang ./scripts/build-crdop.sh
CRDOP_BUILD_TESTS=ON ./scripts/test-all.sh    # needs libcmocka-dev
```

Cross-build (Linux host): see [BUILD.md](BUILD.md).

## Run — CB (default, native M25 host)

```bash
./scripts/crdopc
# or explicit example INI:
CRDOP_INI=share/crdop.ini.example ./scripts/crdopc
```

This starts `audio-dummyd` with native M25/KISS host on TCP :8515/:8516.

Copy config for daily use:

```bash
mkdir -p ~/.config/crdop
cp share/crdop.ini.example ~/.config/crdop/crdop.ini
$EDITOR ~/.config/crdop/crdop.ini
./scripts/crdopc
```

## Run — dual (CB ↔ amateur)

```bash
CRDOP_INI=share/crdop-dual.ini.example ./scripts/crdopc
```

## Run — amateur (secondary)

```bash
CRDOP_INI=share/crdop-amateur.ini.example ./scripts/crdopc
```

## Full-duplex CB

`share/crdop.ini.example` with:

```ini
[modem]
duplex = full
arq_bandwidth = 500MAX
```

## Custom call / ALSA devices

```ini
[mycall]
call = CB01-0

[audio]
capture = plughw:1,0
playback = plughw:1,0
```

Pass extra args after port (reserved for future native modem flags):

```bash
./scripts/crdopc 8515
```

## ARDOP-plugin

Enable **ARDOP-plugin** wire mode with `ardop_compat=yes` and an operator ARDOP host:

```ini
[compat]
ardop_compat = yes
```

```bash
CRDOP_BIN=/path/to/ardopc ./scripts/crdopc
```

## Direct audio-dummyd (no launcher)

```bash
./build/bin/audio-dummyd --ctrl-port 8515 --data-port 8516
```

## max25d integration

```ini
[devices]
soft-crdop = crdop:default

[device.soft-crdop]
host = 127.0.0.1
port = 8515
listen = yes
```

See [../../docs/PLUGINS-DEVICE-MODEL.md](../../docs/PLUGINS-DEVICE-MODEL.md).
