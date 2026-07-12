# BayCom PR-Stack v0.5.0

First public release. Standalone Linux stack for **BayCom ser12** (kernel UART) and **KISS serial/USB** modems.

**Repository:** [github.com/ngteq/BayCom_PR-Stack](https://github.com/ngteq/BayCom_PR-Stack)  
**Plain-text notes:** [RELEASE-NOTES-0.5.0.txt](RELEASE-NOTES-0.5.0.txt)

## Scope

| In scope | Out of scope |
|----------|--------------|
| `baycom-pr-ctl`, INI config, modem catalog | BBS, terminal UI, plugin loaders |
| `baycom_sethdlc`, `baycom_kissbridge`, `baycom_kiss_serial` | On-air RF validation (deferred) |
| `baycom_test` offline suite | `baycom_par` / parallel bring-up |
| KISS + AX.25 attachment points | |

## Features

- **Control:** multi-modem `start` / `stop` / `status` / `test` / `check` / `selftest` / `listen` / `call`
- **Backends:** `kernel-ser12` + `kiss-serial` in one profile
- **HDLC:** `baycom_sethdlc` replaces broken `sethdlc` on kernel 6.x
- **KISS:** one PTY symlink per modem (`kiss_link`)
- **Catalog:** 25 modem types in `modems.ini`
- **Docs:** compact operator and developer set under `docs/`

## Verification status

| Area | v0.5.0 status |
|------|---------------|
| `baycom_ser_fdx` load, IRQ, ioctl, TX delay | **Verified** (no RF) |
| Dual modem (`ttyS0` + `ttyS5`) | **Verified** (no RF) |
| KISS PTY bridges | **Verified** |
| `baycom-pr-ctl test`, `check`, `selftest` | **Verified** |
| `make test` offline repo suite | **Verified** |
| On-air RX/TX, AX.25 traffic | **Not verified** |
| `baycom_par` parallel modems | **Planned** (catalog only) |

## Install

```bash
make install
sudo baycom-pr-ctl selftest    # on hardware with modems attached
```

See [QUICKSTART.md](QUICKSTART.md), [BUILD.md](BUILD.md).

## License

GPL-3.0-or-later — [LICENSE](../LICENSE), [COPYRIGHT](../COPYRIGHT), [NOTICE](../NOTICE).  
Third-party reference archives (TFPCX, vendor manuals) are not included in this repository.

---

## Release checklist

Use this before tagging `v0.5.0` on GitHub.

### Repository

- [x] `VERSION` = `0.5.0`
- [x] `LICENSE`, `COPYRIGHT`, `NOTICE` present
- [x] `research/` excluded from repository (third-party; see NOTICE)
- [x] No deprecated integration names in product docs
- [x] Documentation set complete under `docs/`
- [x] `make test` passes (offline)

### Maintainer actions (manual)

- [x] Review `git status` — commit release-ready files
- [x] `git tag -a v0.5.0` (annotated tag)
- [x] `git push origin main` and `git push origin v0.5.0`
- [ ] Create GitHub Release from tag; attach [RELEASE-NOTES-0.5.0.txt](RELEASE-NOTES-0.5.0.txt)

### Hardware validation (recommended post-release)

- [ ] `sudo baycom-pr-ctl selftest` on target host with real modem(s)
- [ ] On-air: `listen -a -c cb0` with traffic
- [ ] USB KISS modem path if used in deployment
- [ ] Document results in a future release note

### Smoke commands

```bash
make test
python3 tools/baycom_validate_config.py config/baycom-pr.ini
sudo baycom-pr-ctl start && sudo baycom-pr-ctl test
```
