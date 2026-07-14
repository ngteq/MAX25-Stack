# Hardware acceptance · MAX25-Stack 1.5.0

Manual RF acceptance criteria for release tagging.

## Smoke test matrix

| Device | Pass criterion |
|--------|----------------|
| `tnc2c` | UART boot-wait + KISS + decode at remote |
| `baycom-ser12` | kernel module + PTT + on-air |
| `soft-crdop` | ALSA loopback or acoustic bench (optional for tag) |

## Offline test matrix

| Test | Scope |
|------|-------|
| `release-check.sh` | repo consistency |
| `test_crdop_backend.py` | CRDOP backend |
| `test_bell202_line_code.py` | modem line code |
| `max25_test` target | offline smoke |

## Blocker matrix

| Gate | v1.5.0 status |
|------|---------------|
| CI offline gates | pass target |
| Manual TNC RF | operator pending |
| Manual BayCom RF | operator pending |

## Related

| Goal | Doc |
|------|-----|
| Release readiness | [../RELEASE-READINESS.md](../RELEASE-READINESS.md) |
| v1 scope | [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) |
