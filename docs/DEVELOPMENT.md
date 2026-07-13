# Development

[AGENTS.md](../AGENTS.md) · [CONTRIBUTING.md](../CONTRIBUTING.md) · Doc index: [README.md](README.md) · **v1.0.0**

## Toolchain

Linux primary. GCC or Clang, CMake 3.16+, bash, Python 3. CRDOP needs ALSA dev headers.

```bash
./scripts/build.sh
cmake --install build --prefix /usr/local
./scripts/test.sh
./scripts/release-check.sh
```

Host example: [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md). *BSD porting deferred — [PLATFORMS.md](PLATFORMS.md).

## Daemon vs terminal

| Component | Linux | Other OS |
|-----------|-------|----------|
| `max25d` | **Yes** | **No** |
| `max25-terminal` | Yes | Yes — remote TCP to Linux `max25d` |

One official client: `max25-terminal` / `max25-client` — [MAX25-CLIENT.md](MAX25-CLIENT.md).

## Layout

```
plugins/          operating mode / hardware / device metadata
stacks/           tncs, baycom-pr, crdop, daemon, terminal
scripts/          build.sh, max25-ctl, discover-plugins, release-check
share/max25/      max25d.ini examples
share/baycom/     BayCom single-modem INI (v1 default)
share/clients/    max25-terminal client profiles (YAML)
share/hybbx/      HyBBX INI examples
local/            site overrides (gitignored except README)
include/max25/    protocol.md, packet-radio.md
```

## Conventions

- Plugin IDs, scripts, shipped text, and public docs: **English**
- New source comments: **English**
- Minimal diffs; link `stacks/*/` READMEs
- No personal paths in docs — use placeholders
- HyBBX external — `share/hybbx/*.ini.example` only

## Testing

```bash
./scripts/test.sh
./scripts/release-check.sh
python3 stacks/daemon/test_proto.py
python3 stacks/daemon/test_auth.py
bash stacks/terminal/test-terminal.sh
```

Hardware tests manual — [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md).

## Doc duty

| Change | Update |
|--------|--------|
| Plugin / manifest | `plugins/manifest.yaml`, `plugin.yaml` |
| M25/1 / client | [MAX25-CLIENT.md](MAX25-CLIENT.md), `include/max25/protocol.md` |
| AX.25 / KISS | [PACKET-RADIO.md](PACKET-RADIO.md), `include/max25/packet-radio.md` |
| Terminal operator | [MAX25-TERMINAL.md](MAX25-TERMINAL.md) |
| HyBBX attach | [HYBBX.md](HYBBX.md) + `share/hybbx/` |
| Platform limits | [PLATFORMS.md](PLATFORMS.md) |
| v1 scope | [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md), `VERSION`, `release-check.sh` |
| New doc file | [README.md](README.md) index + `release-check.sh` required list |

**Archive:** [MERGE-REPORT.md](MERGE-REPORT.md) — do not extend.

## Pitfalls

- TNC2C: DTR during power-on — echo mode otherwise
- BayCom SER12: no userspace serial client on raw UART while kernel driver loaded
- One process per serial port

## Git

- **Only** `ngteq <info@un1t.me>`
- Push via `~/.ssh/id_ed25519_ngteq` → `git@github.com:ngteq/MAX25-Stack.git`
- Commit/push only when user asks
