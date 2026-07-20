# BayCom/based · MAX25-Stack

Public mark: **BayCom/based**. Product path: **max25-bcpr** (daemon **max25-bcprd**). Host device: **`max25e0`** (forks `max25e0:bcN` only).

## Status: **not usable**

| Fact | Value |
|------|--------|
| Product status | **not usable** — not a supported operator path |
| Default build | `MAX25_BUILD_MAX25_BCPR=OFF` |
| Opt-in | Explicit `-DMAX25_BUILD_MAX25_BCPR=ON` only — **experimental**, unsupported |
| Device id | **`max25e0`** only — never `bcpr` / `bcpr-bc0` |
| Host addresses | IPv4 `127.0.0.25/8`, IPv6 `::25/128` (defaults; overridable in `max25d.ini`) |
| Kernel path | `baycom_ser_fdx` / `baycom-pr` **removed** |

Do **not** treat BayCom/based as an active capability in release builds.

## max25e0 addresses

Hardcoded defaults on device **`max25e0`** (forks inherit unless overridden):

```ini
[device.max25e0]
ipv4 = 127.0.0.25/8
ipv6 = ::25/128
```

Changeable in site `max25d.ini`. Same defaults appear under `[netdev]` for the planned TUN face.

## Experimental opt-in (unsupported)

```bash
cmake -S . -B build-max25-bcpr -DMAX25_BUILD_MAX25_BCPR=ON
cmake --build build-max25-bcpr --target max25-bcprd
```

Freeze risk: [BAYCOM-FREEZES.md](BAYCOM-FREEZES.md).

## Related

| Goal | Doc |
|------|-----|
| Freeze warning | [BAYCOM-FREEZES.md](BAYCOM-FREEZES.md) |
| Device model | [PLUGINS-DEVICE-MODEL.md](PLUGINS-DEVICE-MODEL.md) |
| TX/RX test | [TX-RX-TEST.md](TX-RX-TEST.md) |
