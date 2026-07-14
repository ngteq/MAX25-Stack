# CRDOP / MAX25-SoftModem · MAX25-Stack 1.5.0

In-house sound-card modem — acoustically AX.25-compatible AFSK.

## Status matrix

| Item | Value |
|------|-------|
| Device id | `soft-crdop` |
| Build | `MAX25_BUILD_CRDOP=ON` default |
| Phase | development and test |
| Speed | 1200 bd primary, max 19200 bd |
| Duplex | half and full |
| Audio | ALSA direct — no PulseAudio |

## Port matrix

| Port | Role |
|------|------|
| 8515 | control (M25 host protocol) |
| 8516 | data |
| 7325 | max25d M25/1 (operator IPC) |

## Platform matrix

| Host | CRDOP role |
|------|------------|
| Linux | RF backend in max25d |
| FreeBSD | primary softmodem path (OSS) |

## Start matrix

| Step | Command |
|------|---------|
| Build | `./scripts/build.sh` |
| Start | `max25-ctl start --hardware soft-modems --device soft-crdop` |
| HyBBX | merge `share/hybbx/crdop-host.ini.example` |

## Related

| Goal | Doc |
|------|-----|
| Audio architecture | `stacks/crdop/docs/AUDIO-ARCHITECTURE.md` |
| HyBBX | [HYBBX.md](HYBBX.md) |
