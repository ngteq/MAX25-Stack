# CRDOP documentation

**CRDOP** = stack acronym for **MAX25-SoftModem** (device id `soft-crdop`).

**MAX25-SoftModem** — in-house sound-card modem subproject (`stacks/crdop/`).

## Entry point

**[INDEX.md](INDEX.md)** — complete table of all CRDOP docs with one-line purpose.

Project rule: [docs/CRDOP.md](../../../docs/CRDOP.md)

## Policy

| Rule | |
|------|--|
| Standard | Native MAX25 M25/KISS host on TCP :8515/:8516 |
| Focus | CB-first; `dual` and `amateur` are presets |
| Scope | Modem only — no host application |

## Dev-only vendor tree

Legacy **[pflarue/ardop](https://github.com/pflarue/ardop)** (ardopcf, MIT) may exist under `vendor/ardopcf/` for local dev builds (`-DCRDOP_VENDOR_ARDOPCF=ON`). **Never installed in MAX25 releases.**

Pin: `a7c9228` · record: `vendor/ardopcf.ref`

## Platforms (tested)

Linux · FreeBSD — **tested** (GCC, Clang)

Windows · macOS — build supported, **not yet tested**
