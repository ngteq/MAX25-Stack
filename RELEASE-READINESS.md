# Release readiness · MAX25-Stack 1.8.5-fallback_untested-upcoming#3-2

Offline and manual release gates for MAX25-Stack **1.8.5-fallback_untested-upcoming#3-2**.

## Offline CI gate matrix

| Gate | Result |
|------|--------|
| `cmake` build + install (`MAX25_BUILD_BCPR=ON`) | Pass target |
| `./scripts/terminology-check.sh` | Required |
| `./scripts/release-check.sh` | Pass target |
| `./scripts/tx-rx-test.sh` (L0 offline) | Pass target |
| `max25_web_smoke` (no UART) | Pass target |
| `test_crdop_backend.py` | Pass |
| `test_audio_dummy_backend.py` | Pass |
| `test_bell202_line_code.py` | Pass |

## Consistency gate matrix

| Gate | Status |
|------|--------|
| Version `1.8.5-fallback_untested-upcoming#3-2` in VERSION file | Required |
| Device face BayCom/based = **`max25e0`** (not `bcpr-bc0`) | Required |
| `MAX25_BUILD_CRDOP=ON` documented | Required |
| HyBBX boundary INI defaults | `[features] baycom=no`, `pccom=no`; bcpr via `bcpr=yes` |
| Host protocol ports 8515/8516 | Unified in `m25_host_protocol.py` |
| Canonical start | `scripts/run-max25d.sh` (§0.21 root when needed) |

## Manual hardware gate matrix

| Gate | Status |
|------|--------|
| `tnc2c` UART boot-wait + KISS | Pending |
| BayCom/based `max25e0` (bcpr) | active |
| Live RX before TX (§0.20) | Required |
| `soft-crdop` acoustic bench | Optional |

## Tag gate matrix

| Item | Status |
|------|--------|
| Annotated tag `v1.8.5-fallback_untested-upcoming#3-2` | Operator decision |
| Push to remote | Operator decision |

## Related

| Goal | Doc |
|------|-----|
| TNC / modem bring-up | [TNC-MODEM-DEV.md](TNC-MODEM-DEV.md) |
| v1 scope | [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| BayCom/based | [docs/BAYCOM.md](docs/BAYCOM.md) |
