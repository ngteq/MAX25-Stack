# MAX25-Stack · 1.8.5-fallback_untested-upcoming#3

Linux supervisor for Packet Radio hardware: TNC lifecycle, KISS, M25/1 IPC, optional CRDOP soft-modem. HyBBX consumes RF through plugins — MAX25 owns prep and attach contracts.

## Start (canonical)

```bash
./scripts/run-max25d.sh                 # escalates only when ttyS/USB/SER12 needs root
./scripts/run-max25-terminal.sh -U /run/max25/modem.sock
```

## Capability matrix

| Capability | Status | Entry |
|------------|--------|-------|
| TNC2C serial (KISS) | active | `device=tnc2c` |
| PK-TNC / multi-TNC | active | `[devices]` map |
| BayCom/based (SER12) | active | `max25e0` via `[features] bcpr=yes` |
| CRDOP soft-modem (1200 bd AFSK) | active (dev/test) | `soft-crdop` |
| max25-terminal (F10 UI) | active | M25/1 TCP or Unix |
| HyBBX attach | active | `:7325` + INI in `share/hybbx/` |
| AX.25 kernel bundle | optional build | `-DMAX25_BUNDLE_AX25=OFF` default CI |

## Three commands

```bash
cmake -B build-bcpr -DMAX25_BUILD_BCPR=ON -DMAX25_BUILD_TERMINAL=ON && cmake --build build-bcpr
cmake --build build-bcpr --target max25_test   # or: ./scripts/tx-rx-test.sh
./scripts/run-max25d.sh                        # root only when SER12/ttyS needs it
```

## HyBBX integration matrix

| Rule | Value |
|------|-------|
| Order | max25d up → HyBBX `[max25] check=yes` → `kiss_entry=none` |
| Serial ownership | One process per `/dev/tty*` |
| BayCom default | `[features] bcpr=yes` + device `max25e0` (BayCom/based); `[features] baycom=no` for legacy USB-kiss |

## Related

| Goal | Doc |
|------|-----|
| TNC / modem bring-up | [TNC-MODEM-DEV.md](TNC-MODEM-DEV.md) |
| Setup | [LINUX-HOST-SETUP.md](docs/LINUX-HOST-SETUP.md) |
| Architecture | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| All docs | [docs/README.md](docs/README.md) |
