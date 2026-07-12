# CRDOP 0.5.0 - experimental

**CB Radio Digital Open Protocol** — standalone ARDOP-compatible sound-card modem.

| | |
|---|---|
| Project | [github.com/ngteq/CRDOP](https://github.com/ngteq/CRDOP) |
| Binary | `crdopc` |
| License | MIT (ngteq) |

## What it is

CRDOP is an **independent project** forked from **[pflarue/ardop](https://github.com/pflarue/ardop)** (ardopcf). Same ARDOP over-the-air and host TCP behaviour; CRDOP adds CB-first profiles, packaging, and multi-platform build.

```
Radio ↔ audio ↔ crdopc ↔ TCP :8515 / :8516 ↔ any ARDOP host
```

Modem only — no host application in this repo.

**Platforms:** Linux and *BSD tested (GCC, Clang). Windows and macOS build in-tree but **not yet tested**.

## Quick start

```bash
git clone https://github.com/ngteq/CRDOP.git && cd CRDOP
./scripts/build-crdop.sh
./scripts/install-crdop.sh    # optional → /usr/local/bin/crdopc + crdop
./scripts/crdopc
```

CB profile with example INI:

```bash
CRDOP_INI=share/crdop.ini.example ./scripts/crdopc
```

## Profiles

| Profile | Use | BW | Half-duplex delay | ARQ timeout |
|---------|-----|-----|-------------------|-------------|
| `cb` | CB radio (default) | 500MAX | 150 ms | 30 s |
| `dual` | CB ↔ amateur | 500MAX | 200 ms | 35 s |
| `amateur` | Ham (secondary) | 1000MAX | 80 ms | 45 s |

INI: `share/crdop*.ini.example` · Config: [docs/CONFIG.md](docs/CONFIG.md) · Examples: [docs/EXAMPLES.md](docs/EXAMPLES.md)

## Docs

| Doc | Topic |
|-----|--------|
| [docs/README.md](docs/README.md) | Index · fork · upstream sources |
| [docs/EXAMPLES.md](docs/EXAMPLES.md) | Usage examples |
| [docs/CONFIG.md](docs/CONFIG.md) | INI / launcher |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | ARDOP compatibility |
| [docs/BUILD.md](docs/BUILD.md) | Build · test · platforms |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Release history |

Legal: [NOTICE.md](NOTICE.md) · [LICENSE](LICENSE)

Operator responsible for band, power, and cross-service legality.
