# Merge Report (archive)

One-time record of how MainAX25-Stack was assembled. Do not extend.

## Sources merged

| Stack | Path | Upstream |
|-------|------|----------|
| TNCs-Stack | `stacks/tncs/` | ngteq/TNCs-Stack |
| BayCom PR-Stack | `stacks/baycom-pr/` | ngteq/BayCom_PR-Stack |
| CRDOP | `stacks/crdop/` | ngteq/CRDOP |

HyBBX is **not** vendored — external consumer at ngteq/hyBBX.

## Added in umbrella repo

- `plugins/` — operating mode / hardware / device registry
- `scripts/` — `max25-ctl`, `discover-plugins.sh`, `release-check.sh`
- `share/hybbx/` — HyBBX INI examples
- `docs/` — architecture, HyBBX contract, platforms, v1 scope

## Decisions

- File copy merge (no combined git history from sources)
- Standalone-first; HyBBX attaches after MAX25 prep
- Linux-primary; *BSD later
- Personal `research/` and site-specific operator files removed from publication tree
