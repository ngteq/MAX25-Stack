# Development

[AGENTS.md](../AGENTS.md) · [CONTRIBUTING.md](../CONTRIBUTING.md) · **v1.0.0-rc1**

## Toolchain

Linux primary. GCC or Clang, CMake 3.16+, bash. CRDOP needs ALSA dev headers. Example edge setup: [LINUX-EDGE-SETUP.md](LINUX-EDGE-SETUP.md).

```bash
./scripts/build.sh
cmake --install build --prefix /usr/local
cmake --build build --target max25_test
./scripts/release-check.sh
```

*BSD porting is deferred — daemon stays Linux; see [PLATFORMS.md](PLATFORMS.md).

## Daemon vs terminal

| Component | Linux | Other OS |
|-----------|-------|----------|
| `max25d` | **Yes** — BayCom, TNCs, CRDOP | **No** |
| `max25-terminal` | Yes (local or remote) | Yes — remote TCP to Linux `max25d` |

**One official client only:** `max25-terminal` / `max25-client` — text + F10 menu. See [MAX25-CLIENT.md](MAX25-CLIENT.md).

## Layout

```
plugins/          operating mode / hardware / device metadata (plugin.yaml)
stacks/           Merged source trees (tncs, baycom-pr, crdop, daemon, terminal)
scripts/          max25-ctl, discover-plugins.sh, release-check.sh
share/max25/      max25d.ini, systemd example
share/hybbx/      HyBBX INI examples per device/mode
docs/             Architecture, client dev guide, platforms, v1 scope
```

## Architecture

```
Operator → max25-ctl / stack scripts → TNC | modem | soft-modem (KISS/TCP)
HyBBX (external) → packet_radio | baycom | crdop plugins (after MAX25 prep)
```

- **Standalone-first:** MAX25 owns boot-wait, kernel load, KISS PTY, `crdopc` lifecycle.
- **HyBBX-ready:** INI in `share/hybbx/`; HyBBX does not vendor MAX25.
- **Plugin hierarchy:** operating mode (`betriebsform/`) → Hardware → Device — registry in `plugins/manifest.yaml`.
- **Linux-primary:** kernel BayCom and AX.25 paths are Linux-only today.

## Conventions

- Plugin IDs, scripts, code identifiers: **English**
- **Shipped content English-only:** `docs/`, README, UI strings, `share/*` examples, plugin READMEs, user-facing script output — see [`.cursor/rules/english-only-project.mdc`](../.cursor/rules/english-only-project.mdc)
- **Source comments:** may remain German temporarily; write **new** comments in English until a batch translation pass
- Minimal diffs; link to `stacks/*/` READMEs — do not duplicate stack docs
- Do not add personal paths, hostnames, or callsigns in docs — use placeholders.
- HyBBX is external — reference `share/hybbx/*.ini.example` only

## Testing

```bash
./scripts/test.sh            # offline stack tests (cmake target max25_test)
./scripts/release-check.sh   # v1.0.0 gates (no root, no serial required)
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
| M25/1 protocol / client binding | [MAX25-CLIENT.md](MAX25-CLIENT.md), `include/max25/protocol.md`, `stacks/terminal/` |
| AX.25 / KISS / TNC facts | [PACKET-RADIO.md](PACKET-RADIO.md), `include/max25/packet-radio.md` |
| Terminal operator docs | [MAX25-TERMINAL.md](MAX25-TERMINAL.md) |
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
