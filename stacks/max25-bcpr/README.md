# max25-bcpr — BayCom/based PC-COM SER12 (MAX25 userspace)

**Status: not usable** in the shipped product (CMake default OFF). Experimental opt-in only.

Public mark: **BayCom/based**. Product path: **max25-bcpr** / daemon **max25-bcprd**. Host device: **`max25e0`** (forks `max25e0:bcN` only).

| Layer | Role |
|-------|------|
| Hardware | BayCom/based TCM3105-class AFSK (bits↔tones + PTT) |
| Host | SER12 bit clock, HDLC, KISS PTY via `max25-bcprd` |
| Device id | **`max25e0`** only — never `bcpr` / `bcpr-bc0` product ids |
| Not | TNC · digipeater · BBX · kernel BayCom product |

Internal C sources may still use `bcpr_*` symbols — product face is **max25-bcpr** only.

## Build (experimental)

```bash
cmake -S . -B build-max25-bcpr -DMAX25_BUILD_MAX25_BCPR=ON
cmake --build build-max25-bcpr --target max25-bcprd test_hdlc_offline
```

## Offline smoke

```bash
stacks/max25-bcpr/tools/max25-bcpr-ctl -c stacks/max25-bcpr/share/max25-bcpr.ini.example smoke
```

```bash
# Daemon (opt-in build)
sudo stacks/max25-bcpr/tools/max25-bcpr-ctl -c /etc/max25/max25-bcpr.ini start
sudo stacks/max25-bcpr/tools/max25-bcpr-ctl -c /etc/max25/max25-bcpr.ini status
sudo stacks/max25-bcpr/tools/max25-bcpr-ctl -c /etc/max25/max25-bcpr.ini stop

# Ultimate interactive diag / force-TX ladder (operator)
sudo -n stacks/max25-bcpr/tools/max25-bcpr-ultimate-diag.sh --menu
```

Dauerlauf / experimental orch helpers are **not** shipped in this freigegeben tree.


## max25d (when enabled)

```ini
[features]
max25_max25_bcpr = yes

[devices]
default = max25e0
max25e0 = max25-bcpr:bc0

[device.max25e0]
kiss_link = /tmp/max25-bcpr/kiss-bc0
max25_bcpr_ini = /etc/max25/max25-bcpr.ini
; Hardcoded defaults (overridable):
ipv4 = 127.0.0.25/8
ipv6 = ::25/128
```

Forks `max25e0:bcN` inherit `ipv4` / `ipv6` from `max25e0` unless set on the fork section.

## License

Algorithms from Linux `baycom_ser_fdx` / `hdlcdrv` (GPL) — `NOTICE.md`.
