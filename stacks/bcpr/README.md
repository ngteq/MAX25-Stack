# bcpr — BayCom/based PC-COM SER12 (MAX25 userspace)

**MAX25 plugin** · max **2** COM · host **`max25e0:bc0`/`bc1`** · **no** `baycom_ser_fdx` product path

Public mark: **BayCom/based**. Internal workstream: **bcpr**.

| Layer | Role |
|-------|------|
| Hardware | **BayCom/based** TCM3105-class AFSK (bits↔tones + PTT) |
| Host | SER12 bit clock, HDLC, KISS PTY |
| Not | TNC · digipeater · BBX · kernel BayCom product |

**A–O–Z:** isolate held COM · real unique IRQs · never deviate from INI/autoprobe once frozen · exclusive lock (fail closed). Autoprobe only when serial missing/wrong.

**UX:** Simple steps · prefer **more config + probes** (safe) over thin checks (H11).

Vault SSoT: `0-RESEARCHES/projects/max25-stack/2026-07-18-bcpr-rxtx-smoke-nofreeze.md` · harden · detect · freezes.

## Use (simple)

```bash
# Build (if build-bcpr is not writable, use build-bcpr-$USER)
cmake -S . -B build-bcpr -DMAX25_BUILD_BCPR=ON
cmake --build build-bcpr --target bcprd test_hdlc_offline

# Offline smoke (always — NO TX)
stacks/bcpr/tools/bcpr-ctl -c stacks/bcpr/share/bcpr.ini.example smoke

# Live RX listen (radio OFF OK; short cap)
sudo cp stacks/bcpr/share/bcpr.ini.example /etc/max25/bcpr.ini   # edit IRQ/serial; dry_run=no
sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini preflight
sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini smoke --live --seconds 15

# Optional TX (PTT warning even if radio OFF)
sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini smoke --live --tx --seconds 15

# Daemon
sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini start
sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini status
sudo stacks/bcpr/tools/bcpr-ctl -c /etc/max25/bcpr.ini stop
```

## max25d

```ini
[features]
bcpr = yes

[devices]
default = bcpr-bc0
bcpr-bc0 = bcpr:bc0

[device.bcpr-bc0]
kiss_link = /tmp/bcpr/kiss-bc0
bcpr_ini = /etc/max25/bcpr.ini
```

## License

Algorithms from Linux `baycom_ser_fdx` / `hdlcdrv` (GPL) — `NOTICE.md`. Product path = this userspace plugin.
