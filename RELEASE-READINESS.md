# MAX25-Stack-v1.0.0 — release readiness

**Date:** 2026-07-13 · **Version file:** `1.0.0` · **Product:** MAX25-Stack-v1.0.0

## Offline gates (CI)

| Gate | Result |
|------|--------|
| `cmake` build + install (`build-release/`, prefix `/tmp/max25-v100-test`) | **Pass** |
| `./scripts/release-check.sh` | **Pass** — 75 OK, 0 FAIL, 1 WARN (`tnc2c-probe`: no serial hardware) |
| `test_crdop_backend.py` | **Pass** |
| `test_audio_dummy_backend.py` | **Pass** |
| `test_bell202_line_code.py` | **Pass** |

## Consistency audit (fixed)

- Version `1.0.0` (no `1.0.0.0`)
- CRDOP product **CRDOP-CUR999** until separate v0.5
- `MAX25_BUILD_CRDOP=ON` default documented everywhere
- ARDOP-plugin documented; vendor tree not in release install path
- `CrdopTcpBackend`: KISS default, `[CRDOP AX25 UI …]` display strings
- German user-facing strings in shipped docs/YAML → English
- `stacks/crdop/docs/INDEX.md` linked from `AGENTS.md` and `docs/README.md`
- **Vault → repo:** implementable specs in `stacks/crdop/docs/*-SPEC.md`, `docs/HARDWARE-ACCEPTANCE.md`, `docs/MAX25-OPERATOR-RUNBOOK.md`, `docs/AX25-NATIVE-CODEC.md`
- Host protocol ports unified: **8515/8516** in `m25_host_protocol.py` + [HOST-PROTOCOL-SPEC.md](stacks/crdop/docs/HOST-PROTOCOL-SPEC.md)

## Tag status

| Item | Status |
|------|--------|
| Annotated tag `v1.0.0` | **Exists** on commit `7f81fb9` (2026-07-12) — **predates** current release-prep tree |
| Retag after commit | **Needed** if this tree should be the official v1.0.0 — requires `git tag -d v1.0.0` + `git tag -a v1.0.0` (maintainer decision; not done automatically) |
| Push | **Not done** — per project rules |
| `third_party/_build-test/` in tree | **Removed** in follow-up commit — added to `.gitignore` |

## Remaining blockers (non-CI)

| Gate | Status |
|------|--------|
| Manual hardware smoke — `tnc2c` | **Pending** (UART boot-wait + KISS) |
| Manual hardware smoke — `baycom-ser12` | **Pending** (kernel BayCom + RF) |
| Manual hardware smoke — `soft-crdop` | **Optional** for v1 tag (acoustic bench / ALSA loopback acceptable offline) |

## Recommendation

**Offline release-ready.** Commit release-prep changes, then either:

1. **Move tag** `v1.0.0` to the new commit after maintainer review, or
2. **Ship as v1.0.1** if the existing tag must remain immutable.

Manual RF acceptance remains a post-tag operator step — see [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md).
