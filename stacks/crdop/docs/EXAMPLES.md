# Examples

## Build

```bash
./scripts/build-crdop.sh
CC=clang ./scripts/build-crdop.sh
CRDOP_BUILD_TESTS=ON ./scripts/test-all.sh    # needs libcmocka-dev
```

Cross-build (Linux host): see [BUILD.md](BUILD.md).

## Run — CB (default)

```bash
./scripts/crdopc
# or explicit example INI:
CRDOP_INI=share/crdop.ini.example ./scripts/crdopc
```

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

Or override delay only:

```ini
[modem]
extra_delay_ms = 0
```

## Custom call / ALSA devices

```ini
[mycall]
call = CB01-0

[audio]
capture = plughw:1,0
playback = plughw:1,0
```

Pass extra args after port (ALSA device names, etc.):

```bash
./scripts/crdopc 8515 plughw:1,0 plughw:1,0
```

## Direct binary (no launcher)

```bash
./build/crdopc 8515 -H "INITIALIZE;PROTOCOLMODE ARQ;ARQBW 500MAX;MYCALL CB01-0;EXTRADELAY 150;BUSYDET 1;LISTEN"
```

## Install

```bash
./scripts/install-crdop.sh
# → bin/crdopc (modem) + bin/crdop (launcher) + share/crdop/
```

Or manually: `cmake --install build --prefix /usr/local`

## Host application

Connect your ARDOP client to **8515** (control) and **8516** (data). CRDOP does not ship a host — any ARDOP-compatible program works.

## Environment

```bash
export CRDOP_INI=~/.config/crdop/crdop.ini
export CRDOP_BIN=/usr/local/bin/crdopc
./scripts/crdopc
```
