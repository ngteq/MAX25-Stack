# Development guide

**v0.5.0** · [REPOSITORY.md](REPOSITORY.md) · [CONFIGURATION.md](CONFIGURATION.md) · [TESTING.md](TESTING.md)

Local workflow for contributors and packagers. Operators start with [QUICKSTART.md](QUICKSTART.md).

## Prerequisites

| Tool | Purpose |
|------|---------|
| GCC, GNU make | Build C tools in `tools/` |
| Python 3.6+ | INI loader, validator, preflight (stdlib only) |
| Bash | Scripts and control layer |

Hardware tests additionally need root, `setserial`, kernel modules `ax25` and `baycom_ser_fdx`.

## Dev loop

```bash
# 1. Clone and build
git clone https://github.com/ngteq/BayCom_PR-Stack.git && cd BayCom_PR-Stack
make all

# 2. Offline QA (no root)
make test

# 3. Validate config templates
make test-config

# 4. Optional: run against repo INI without install
baycom-pr-ctl -c config/baycom-pr.ini status   # needs root + hardware for start
python3 tools/baycom_ini_load.py config/baycom-pr.ini
```

After editing C sources: `make -C tools clean all`. After editing scripts: `bash -n scripts/baycom-pr-ctl`.

## Make targets

Run `make help` for a summary.

| Target | What it does |
|--------|----------------|
| `make` / `make all` | Build all C binaries in `tools/` |
| `make install` | Install binaries to `/usr/local/sbin`, config to `/etc/baycom/` |
| `make test` | Offline suite: `scripts/test-all.sh` |
| `make test-config` | Validate `config/baycom-pr.ini` + catalog refs |
| `make clean` | Remove built binaries |

Install without full smoke test: `sudo make install`. Full install + start + tests: `sudo bash scripts/install-root.sh`.

## Offline vs hardware tests

| Layer | Command | Root | Radio |
|-------|---------|------|-------|
| Repo QA | `make test` | no | no |
| INI only | `make test-config` | no | no |
| Preflight | `sudo baycom-pr-ctl preflight` | yes | no |
| Quick stack | `sudo baycom-pr-ctl check` | yes | no |
| Full offline | `sudo baycom-pr-ctl test` | yes | no |
| Post-install | `sudo baycom-pr-ctl selftest` | yes | no |
| On-air | `listen`, `call` | yes | yes |

`scripts/test-all.sh` checks: shell syntax, build, INI validation, catalog count, required doc paths. It does **not** load kernel modules.

`scripts/baycom-pr-selftest.sh` is the full host checklist (deps, preflight, start, KISS symlinks). Invoked via `baycom-pr-ctl selftest`.

## Working with config

Edit templates in `config/` during development. Production install copies to `/etc/baycom/`:

```bash
sudo install -d /etc/baycom
sudo cp config/baycom-pr.ini /etc/baycom/baycom-pr.ini
sudo cp config/modems.ini /etc/baycom/modems.ini
sudo baycom-pr-ctl preflight
```

Dual-modem dev profile:

```bash
sudo baycom-pr-ctl -c config/examples/baycom-pr.dual.ini preflight
```

See [CONFIGURATION.md](CONFIGURATION.md) for canonical paths and environment variables.

## One-liner reference

```bash
sudo make install && sudo baycom-pr-ctl preflight && sudo baycom-pr-ctl start
sudo baycom-pr-ctl recover    # after freeze or unclean shutdown
sudo baycom-pr-ctl selftest   # full offline checklist
make test                     # contributor QA from repo root
```

## Project layout

See [REPOSITORY.md](REPOSITORY.md) for the full tree. Key dirs:

- `tools/` — compile here; Python helpers live beside C sources
- `scripts/` — `baycom-pr-ctl` is the main entry; `legacy/` is deprecated
- `config/` — all installable INI templates
- `docs/` — operator and developer documentation

## Conventions

- Prefer `baycom_*` names; keep `pccom_*` as legacy aliases only.
- Docs: generic Linux, no distribution names.
- Do not commit `research/`.
- Extend `scripts/test-all.sh` when adding required repo files or checks.

## See also

- [CONTRIBUTING.md](../CONTRIBUTING.md) — fork, PR, commit style
- [AGENTS.md](../AGENTS.md) — compact map for AI agents
- [BUILD.md](BUILD.md) — compile and install details
- [STABILITY.md](STABILITY.md) — freeze prevention during hardware dev
