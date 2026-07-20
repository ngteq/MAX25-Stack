# MAX25-Stack · 1.8.5-fallback_untested-upcoming#3-2

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
| BayCom/based (SER12) | **not usable** | `max25-bcpr` / `max25e0`; opt-in `-DMAX25_BUILD_MAX25_BCPR=ON` |
| CRDOP soft-modem (1200 bd AFSK) | active (dev/test) | `soft-crdop` |
| max25-terminal (F10 UI) | active | M25/1 TCP or Unix |
| HyBBX attach | active | `:7325` + INI in `share/hybbx/` |
| AX.25 kernel bundle | optional build | `-DMAX25_BUNDLE_AX25=OFF` default CI |

## Three commands

```bash
cmake -B build -DMAX25_BUILD_TERMINAL=ON && cmake --build build
cmake --build build --target max25_test   # or: ./scripts/tx-rx-test.sh
./scripts/run-max25d.sh                   # root only when ttyS/USB needs it
```

BayCom/based / **max25-bcpr** is **not usable** in the default build. Device id **`max25e0`** only. Experimental opt-in: `-DMAX25_BUILD_MAX25_BCPR=ON` (see [docs/BAYCOM.md](docs/BAYCOM.md)).

## HyBBX integration matrix

| Rule | Value |
|------|-------|
| Order | max25d up → HyBBX `[max25] check=yes` → `kiss_entry=none` |
| Serial ownership | One process per `/dev/tty*` |
| BayCom/based | **not usable** (default); do not enable for production |

## Related

| Goal | Doc |
|------|-----|
| TNC / modem bring-up | [docs/DEV/TNC-MODEM-DEV.md](docs/DEV/TNC-MODEM-DEV.md) |
| Setup | [LINUX-HOST-SETUP.md](docs/LINUX-HOST-SETUP.md) |
| Architecture | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| All docs | [docs/README.md](docs/README.md) |
