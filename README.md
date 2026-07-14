# MAX25-Stack · 1.5.0

Linux supervisor for Packet Radio hardware: TNC lifecycle, KISS, M25/1 IPC, optional CRDOP soft-modem. HyBBX consumes RF through plugins — MAX25 owns prep and attach contracts.

## Capability matrix

| Capability | Status | Entry |
|------------|--------|-------|
| TNC2C serial (KISS) | active | `device=tnc2c` |
| PK-TNC / multi-TNC | active | `[devices]` map |
| BayCom SER12 | active | `baycom-ser12` |
| CRDOP soft-modem (1200 bd AFSK) | active (dev/test) | `soft-crdop` |
| max25-terminal (F10 UI) | active | M25/1 TCP or Unix |
| HyBBX attach | active | `:7325` + INI in `share/hybbx/` |
| AX.25 kernel bundle | optional build | `-DMAX25_BUNDLE_AX25=OFF` default CI |

## Three commands

```bash
cmake -B build && cmake --build build          # compile
cmake --build build --target max25_test          # offline smoke
sudo max25d -c /etc/max25/max25d.ini             # run (after INI deploy)
```

## HyBBX integration matrix

| Rule | Value |
|------|-------|
| Order | max25d up → HyBBX `[max25] check=yes` → `kiss_entry=none` |
| Serial ownership | One process per `/dev/tty*` |
| BayCom default | `[features] baycom=no` in INI examples (v1.5.0) |

## Related

| Goal | Doc |
|------|-----|
| Setup | [LINUX-HOST-SETUP.md](docs/LINUX-HOST-SETUP.md) |
| Architecture | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| All docs | [docs/README.md](docs/README.md) |
