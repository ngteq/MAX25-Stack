# CRDOP documentation

Standalone **CB Radio Digital Open Protocol** modem (`crdopc`).

## Index

| Doc | Contents |
|-----|----------|
| [EXAMPLES.md](EXAMPLES.md) | Build, run, profiles |
| [CONFIG.md](CONFIG.md) | INI / launcher |
| [PROTOCOL.md](PROTOCOL.md) | ARDOP compatibility |
| [BUILD.md](BUILD.md) | Build, install, platforms |
| [CHANGELOG.md](CHANGELOG.md) | Releases |

## Fork

CRDOP is an independent ngteq project based on **[pflarue/ardop](https://github.com/pflarue/ardop)** (ardopcf, MIT).

| Rule | |
|------|--|
| Protocol | Full ARDOP compatibility |
| Focus | CB-first; `dual` and `amateur` are presets |
| Scope | Modem only — no host application |

## Upstream

| Repo | Role | In CRDOP |
|------|------|----------|
| [pflarue/ardop](https://github.com/pflarue/ardop) | Fork base (MIT) | `vendor/ardopcf/` |
| [g8bpq/ardop](https://github.com/g8bpq/ardop) | Reference only (GPL) | not vendored |

Pin: `a7c9228` · record: `vendor/ardopcf.ref`

## Platforms (tested)

Linux · FreeBSD — **tested** (GCC, Clang)

Windows · macOS — build supported, **not yet tested**
