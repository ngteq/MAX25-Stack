# Contributing

Standards: [AGENTS.md](AGENTS.md), [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). Doc index: [docs/README.md](docs/README.md).

```bash
git clone git@github.com:ngteq/MAX25-Stack.git && cd MAX25-Stack
./scripts/build.sh
./scripts/release-check.sh
```

## Git identity

**Only** this identity — no alternatives:

```
user.name  = ngteq
user.email = info@un1t.me
```

Push **only** via SSH `~/.ssh/id_ed25519_ngteq` → `git@github.com:ngteq/MAX25-Stack.git`.

## Pull requests

- Small, focused diffs; plugin hierarchy unchanged unless discussed
- Plugin / manifest → `plugins/manifest.yaml`, `plugins/**/plugin.yaml`
- HyBBX attach → [docs/HYBBX.md](docs/HYBBX.md) + `share/hybbx/*.ini.example`
- Platform → [docs/PLATFORMS.md](docs/PLATFORMS.md)
- Verify: `./scripts/test.sh && ./scripts/release-check.sh`

Issues: `.github/ISSUE_TEMPLATE/`.
