# Development

[AGENT-INDEX.md](../AGENT-INDEX.md) · [AGENTS.md](../AGENTS.md) · [CONTRIBUTING.md](../CONTRIBUTING.md) · Doc index: [README.md](README.md) · **v1.0.0**

## Publication standard (static rule)

**Repo boundary:** MAX25-Stack = **code** for agents. **All documentation** = only in **0-RESEARCHES** (`projects/max25-stack/`) — [vault AGENT-INDEX §0.5](../0-RESEARCHES/AGENT-INDEX.md#05-documentation-sole-workspace-static-rule). Agents do **not** write `docs/` here unless the operator explicitly orders a shipped sync. See also [AGENT-INDEX.md §0.1](../AGENT-INDEX.md#01-static-repo-boundary-internal--owner-rule).

Applies to shipped text when the owner publishes from the vault — full spec in [AGENT-INDEX.md §0](../AGENT-INDEX.md#0-publication-standard-all-projects) and [0-RESEARCHES AGENT-INDEX](../0-RESEARCHES/AGENT-INDEX.md#0-publication-standard-all-projects).

| Requirement | MAX25 shipped docs |
|-------------|-------------------|
| Complete + compact | Operator can act from docs + `share/` examples |
| English only | All user-facing text in English |
| AI/human-readable | Tables, stable plugin/device terminology |
| Generic | `$SRC`, `$PREFIX`, placeholder devices — [PATHS.md](PATHS.md) |
| Investigations | Research vault `projects/max25-stack/` — not `docs/` dumps |

## Research vault boundary (static rule)

| Agents in MAX25-Stack | Research vault `0-RESEARCHES/` |
|-----------------------|--------------------------------|
| **Code + publication** (VERSION, release-check, `share/` when shipping) | **All documentation work** — architecture, roadmaps, scope, operator manuals |
| Read frozen `docs/` for context | Inbound-only, no deletion without replacement — [vault §0.1](../0-RESEARCHES/AGENT-INDEX.md#01-vault-retention-research-vault-only) |
| — | Dedup: `tools/vault-duplicate-check.sh`; REGISTER: `vault-register-check.sh` |

Workflow: [0-RESEARCHES/AGENT-INDEX.md](../0-RESEARCHES/AGENT-INDEX.md) §0.2 · [operations/2026-07-13-vault-automation-roadmap.md](../0-RESEARCHES/operations/2026-07-13-vault-automation-roadmap.md).

## Toolchain

Linux primary. GCC or Clang, CMake 3.16+, bash, Python 3.

**Paths in docs:** [PATHS.md](PATHS.md) (`$SRC`, `$PREFIX`, …).

**Default build:** `stacks/tncs`, `stacks/baycom-pr`, **MAX25-SoftModem (CRDOP — MAX25-SoftModem) scaffold**, `max25d` (native `ax25_codec.py`), `max25-terminal`.

**CMake flags:**

| Flag | Default | Purpose |
|------|---------|---------|
| `MAX25_BUILD_CRDOP` | **ON** | Build/install MAX25-SoftModem (CRDOP) — set OFF to skip |
| `MAX25_BUNDLE_AX25` | OFF | Deprecated — use distro `ax25-apps` or `scripts/build-ax25-deps.sh` manually |

```bash
./scripts/build.sh
cmake --install build --prefix /usr/local
./scripts/test.sh
./scripts/release-check.sh

# Skip SoftModem:
cmake -B build -DMAX25_BUILD_CRDOP=OFF && cmake --build build -j$(nproc)
```

Host example: [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md). FreeBSD server port (CRDOP, light) — [FREEBSD-AX25.md](FREEBSD-AX25.md) · [PLATFORMS.md](PLATFORMS.md).

## Daemon vs terminal

| Component | `max25d` host (mainstream OS) | Client platforms |
|-----------|------------------------------|------------------|
| **`max25d`** | Linux/KLinux (full stack) → FreeBSD **server+CRDOP** → OpenBSD → NetBSD → macOS → Windows | not on AmigaOS / legacy DOS |
| **`max25-terminal`** | yes (local or remote) | mainstream + AmigaOS — remote M25/1 TCP |

Port order: Linux/KLinux → **FreeBSD** (first *BSD) → OpenBSD → NetBSD. FreeBSD `max25d` deferred until Linux/KLinux tier is complete.

One official client: `max25-terminal` / `max25-client` — [MAX25-CLIENT.md](MAX25-CLIENT.md).

### Third-party and GUI clients (welcome)

MAX25 maintains **one** official operator client (`max25-terminal`, text-only). **GUI clients from third-party developers are explicitly welcome** — desktop (Qt, GTK, Electron), mobile, browser, or custom tooling.

| Who builds | Contract | Notes |
|------------|----------|-------|
| MAX25 project | `max25-terminal` only | No official windowing GUI in core |
| **Third-party developers** | [M25/1](include/max25/protocol.md) over TCP `:7325` or Unix socket | Encouraged; document your client; optional listing in `share/clients/` |
| Near-term MAX25 | WebSocket browser terminal (`stacks/web/`) | In development — not v1.0.0 production |

Bind to `max25d` via the documented protocol; do not open `/dev/tty*` or kernel modem devices directly. See [MAX25-CLIENT.md](MAX25-CLIENT.md) and [MAX25-TERMINAL.md](MAX25-TERMINAL.md).

**Host layout:** Main + optional Secondaries on one server — [ARCHITECTURE.md](ARCHITECTURE.md#host-layout--main--secondaries). Linux TUN: **`max25d0`** — [NETDEV.md](NETDEV.md).

**v2 mandatory:** rootless day-to-day operation and guided setup ([V2.0.0-SCOPE.md](V2.0.0-SCOPE.md)) — BayCom currently still uses `sudo` in v1; implementation targets systemd + one-time install boundary.

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
| Virtual netdev (TUN) | [NETDEV.md](NETDEV.md) |
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
