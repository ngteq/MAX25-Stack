# Developer guide

## Repository layout

```
BayCom_PR-Stack/
├── Makefile                 make help | all | install | test | verify
├── README.md                project entry
├── AGENTS.md                  AI agent map
├── CONTRIBUTING.md            PR workflow
├── config/
│   ├── baycom-pr.ini          single-modem default
│   ├── modems.ini             hardware catalog
│   └── examples/              cb, ham, dual, par96, picpar
├── docs/
│   ├── INDEX.md               documentation hub
│   ├── GUIDE.md               operator guide
│   ├── REFERENCE.md           INI, backends, paths
│   └── DEVELOPER.md           this file
├── scripts/
│   ├── baycom-pr-ctl          main control
│   ├── baycom-pr-selftest.sh  hardware checklist
│   ├── test-all.sh            offline QA (make test)
│   └── verify-analysis.sh     deep-scan checklist (make verify)
└── tools/                     C binaries + Python INI tools
```

`research/` is gitignored (local archives only).

---

## Build

```bash
make all          # C tools in tools/
make test         # offline QA
make verify       # analysis checklist + test
make test-config  # validate config/baycom-pr.ini
sudo make install # /usr/local/sbin + /etc/baycom/
```

Dependencies: `gcc`, `make`, `python3`, `libutil` (PTY).

---

## Offline vs hardware tests

| Scope | Command | Root |
|-------|---------|------|
| CI / dev | `make test` | no |
| Analysis P0 | `make verify` | no |
| Doctor offline | `baycom_doctor.py --offline config/baycom-pr.ini` | no |
| Hardware | `sudo baycom-pr-ctl selftest` | yes |

---

## Key code paths

| Component | File |
|-----------|------|
| Stack control | `scripts/baycom-pr-ctl` |
| INI loader | `tools/baycom_ini_load.py` |
| Validation | `tools/baycom_validate_config.py` |
| Preflight | `tools/baycom_preflight.py` |
| Freeze watchdog | `post_start_irq_watch` in `baycom-pr-ctl` |
| Staged dual | `staged_dual_ser12_probe`, `staged_dual_par_probe` |
| Offline tests | `tools/baycom_test.c` |

---

## Conventions

- Install config under `/etc/baycom/` only
- Default profile: **single modem**
- Dual, CB, HAM, par96: optional examples in `config/examples/`
- Docs: generic **Linux** wording (no distribution names)
- Terminology: BayCom, ser12, `baycom_*`, kernel `baycom_ser_fdx`
- Legacy `pccom_*` symlinks kept for compatibility; do not extend

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md). Before PR:

```bash
make verify
bash -n scripts/baycom-pr-ctl
```

---

## Kernel analysis

Freeze risks and driver review: [kernel/BAYCOM-DRIVER-ANALYSIS.md](kernel/BAYCOM-DRIVER-ANALYSIS.md)

P0 userspace mitigations: preflight, staged start, IRQ watchdog, recover. Kernel-side IRQ limits not patched in this repo.

---

## Release checklist

1. `make verify` green
2. AX25SRV: `doctor` + `selftest` zero errors (when hardware available)
3. Single modem stable (no freeze)
4. Optional dual with preflight
5. Update `VERSION`, [CHANGELOG.md](../CHANGELOG.md), tag, push
