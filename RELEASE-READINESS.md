# Release readiness · MAX25-Stack 1.5.0

Offline and manual release gates for MAX25-Stack 1.5.0.

## Offline CI gate matrix

| Gate | Result |
|------|--------|
| `cmake` build + install | Pass |
| `./scripts/release-check.sh` | Pass target |
| `test_crdop_backend.py` | Pass |
| `test_audio_dummy_backend.py` | Pass |
| `test_bell202_line_code.py` | Pass |

## Consistency gate matrix

| Gate | Status |
|------|--------|
| Version `1.5.0` in VERSION file | Required |
| `MAX25_BUILD_CRDOP=ON` documented | Required |
| HyBBX boundary INI defaults | `[features] baycom=no`, `pccom=no` |
| Host protocol ports 8515/8516 | Unified in `m25_host_protocol.py` |

## Manual hardware gate matrix

| Gate | Status |
|------|--------|
| `tnc2c` UART boot-wait + KISS | Pending |
| `baycom-ser12` kernel + RF | Pending |
| `soft-crdop` acoustic bench | Optional |

## Tag gate matrix

| Item | Status |
|------|--------|
| Annotated tag `v1.5.0` | Operator decision |
| Push to remote | Operator decision |

## Related

| Goal | Doc |
|------|-----|
| v1 scope | [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
