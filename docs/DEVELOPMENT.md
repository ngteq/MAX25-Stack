# Development · MAX25-Stack 1.5.0

Contributor build, test, and repository layout.

## Workflow matrix

| Step | Command |
|------|---------|
| Build | `./scripts/build.sh` |
| Test | `./scripts/test.sh` |
| Release check | `./scripts/release-check.sh` |
| Plugin discovery | `./scripts/discover-plugins.sh --json` |

## CMake matrix

| Option | Default |
|--------|---------|
| `MAX25_BUILD_CRDOP` | ON |
| `MAX25_BUNDLE_AX25` | OFF |

## Layout matrix

| Path | Content |
|------|---------|
| `stacks/daemon/` | max25d |
| `stacks/terminal/` | max25-terminal |
| `stacks/tncs/` | TNC tools |
| `stacks/baycom-pr/` | BayCom kernel stack |
| `stacks/crdop/` | SoftModem |
| `plugins/` | manifest + betriebsform |
| `share/` | INI examples |

## Related

| Goal | Doc |
|------|-----|
| Paths | [PATHS.md](PATHS.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
