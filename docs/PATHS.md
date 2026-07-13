# Path conventions (documentation)

Use these **variables** in docs — never hardcode operator home directories (`/home/…`), `/tmp/…` build trees, or `/root/…`.

| Variable | Meaning | Typical value |
|----------|---------|----------------|
| **`$SRC`** | MAX25-Stack repository root (this checkout) | `git clone` directory |
| **`$VAULT`** | External research vault (`0-RESEARCHES`) | Sibling of `$SRC` or `$VAULT` env |
| **`$PREFIX`** | CMake install prefix | `/usr/local` or `~/.local` |
| **`$BUILD`** | Out-of-tree build directory | `$SRC/build` |
| **`$ETC_MAX25`** | Site daemon config (FHS) | `/etc/max25` |
| **`$RUN_MAX25`** | Runtime state (systemd `RuntimeDirectory`) | `/run/max25` |

## In prose

| Instead of | Write |
|------------|--------|
| `$SRC/...` | `$SRC/...` |
| `$VAULT/...` | `$VAULT/...` |
| `/tmp/max25-v100-test` | `$BUILD/install-test` or `$PREFIX` after `cmake --install` |
| `/home/hybbx/start-hybbx.sh` | site operator script (e.g. `$HYBBX_HOME/start-hybbx.sh`) |

## Repo-relative links

Inside MAX25-Stack markdown, prefer **relative links** (`stacks/crdop/...`, `docs/...`) over absolute paths.

## Vault references

Research lives outside this repo. Point to `$VAULT/<path>` or cite the vault filename only — do not assume a fixed home directory.

## Install paths (allowed literals)

FHS paths are fine when documenting production layout:

- `/etc/max25/max25d.ini`
- `/run/max25/modem.sock`
- `/usr/local/bin/max25d` (when documenting default `$PREFIX`)

Say **`$PREFIX/bin/max25d`** when the doc is prefix-agnostic.
