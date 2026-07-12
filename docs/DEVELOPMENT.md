# Development

[AGENTS.md](../AGENTS.md) · [CONTRIBUTING.md](../CONTRIBUTING.md) · **v1.0.0-rc1**

## Toolchain

Linux primary. GCC or Clang, make, bash. CRDOP needs CMake 3.16+ and ALSA dev headers.

```bash
make all
make test
make release-check
```

*BSD porting is deferred — see [PLATFORMS.md](PLATFORMS.md).

## Layout

```
plugins/          Betriebsform / hardware / device metadata (plugin.yaml)
stacks/           Merged source trees (tncs, baycom-pr, crdop)
scripts/          max25-ctl, discover-plugins.sh, release-check.sh
share/hybbx/      HyBBX INI examples per device/mode
docs/             Architecture, HyBBX contract, platforms, v1 scope
```

## Architecture

```
Operator → max25-ctl / stack scripts → TNC | modem | soft-modem (KISS/TCP)
HyBBX (external) → packet_radio | baycom | crdop plugins (after MAX25 prep)
```

- **Standalone-first:** MAX25 owns boot-wait, kernel load, KISS PTY, `crdopc` lifecycle.
- **HyBBX-ready:** INI in `share/hybbx/`; HyBBX does not vendor MAX25.
- **Plugin hierarchy:** Betriebsform → Hardware → Device — registry in `plugins/manifest.yaml`.
- **Linux-primary:** kernel BayCom and AX.25 paths are Linux-only today.

## Conventions

- Plugin IDs, scripts, code: **English**
- Operator-facing docs: German terms OK (**Betriebsform**, **Betrieb**)
- Minimal diffs; link to `stacks/*/` READMEs — do not duplicate stack docs
- Do not add personal paths, hostnames, or callsigns in docs — use placeholders.
- HyBBX is external — reference `share/hybbx/*.ini.example` only

## Testing

```bash
make test                  # offline stack tests
make release-check         # v1.0.0 gates (no root, no serial required)
./scripts/discover-plugins.sh --json
```

Hardware tests (TNC2C RF, BayCom SER12) are manual — see [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md).

## Git

- **Only** `ngteq <info@un1t.me>` — author and committer (`.git/config`)
- **Only** SSH push: `~/.ssh/id_ed25519_ngteq` → `git@github.com:ngteq/MAX25-Stack.git`
- Agents: commit/push only when the user asks

## Doc duty

| Change | Update |
|--------|--------|
| Plugin / manifest | `plugins/manifest.yaml`, `plugins/**/plugin.yaml`, `discover-plugins.sh` if needed |
| HyBBX attach contract | [HYBBX.md](HYBBX.md) + `share/hybbx/*.ini.example` |
| Platform limits | [PLATFORMS.md](PLATFORMS.md) |
| v1 scope / release gates | [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md), `VERSION`, `scripts/release-check.sh` |
| Stack behaviour | Stack README under `stacks/*/` — link from plugin README |

**Planning docs:** MAX25 is a release/stack repo — `docs/V1.0.0-SCOPE.md` and README roadmap are intentional (unlike HyBBX core, which avoids planning docs).

**Archive:** [MERGE-REPORT.md](MERGE-REPORT.md) is a one-time merge record — do not extend unless re-merging stacks.

## Pitfalls

- TNC2C: DTR during power-on (boot-wait) — echo mode otherwise
- BayCom SER12: never minicom on raw UART while kernel driver loaded
- One process per serial port (HyBBX **or** tnc2c-tools, not both)
- PK-TNC2 (Unit B): planned — probe serial before assuming port
